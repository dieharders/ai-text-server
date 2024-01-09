import json
from typing import List, Sequence
from llama_index.llms import LlamaCPP
from llama_index.llms.llama_utils import messages_to_prompt, completion_to_prompt
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from embedding import embedding
from server import common, classes

QUERY_INPUT = "{query_str}"

###
# Llama-Index allows us to search embeddings in a db and perform queries on them.
# It wraps llama-cpp-python so we can run inference from here as well.
###


# High level llama-cpp-python object wrapped in class from LlamaIndex
def load_text_model(
    path_to_model: str,
    mode: str,
    init_settings: classes.LoadTextInferenceInit,  # init settings
    gen_settings: classes.LoadTextInferenceCall,  # generation settings
):
    n_ctx = init_settings.n_ctx or classes.DEFAULT_CONTEXT_WINDOW
    if n_ctx <= 0:
        n_ctx = classes.DEFAULT_CONTEXT_WINDOW
    seed = init_settings.seed
    temperature = gen_settings.temperature
    m_tokens = gen_settings.max_tokens
    max_tokens = common.calc_max_tokens(m_tokens, n_ctx, mode)
    n_threads = init_settings.n_threads  # None means auto calc
    if n_threads == -1:
        n_threads = None

    generate_kwargs = {
        "stream": gen_settings.stream,
        "stop": gen_settings.stop,
        "echo": gen_settings.echo,
        "model": gen_settings.model,
        "mirostat_tau": gen_settings.mirostat_tau,
        "tfs_z": gen_settings.tfs_z,
        "top_k": gen_settings.top_k,
        "top_p": gen_settings.top_p,
        "min_p": gen_settings.min_p,
        "repeat_penalty": gen_settings.repeat_penalty,
        "presence_penalty": gen_settings.presence_penalty,
        "frequency_penalty": gen_settings.frequency_penalty,
        "temperature": temperature,
        "seed": seed,
        "grammar": gen_settings.grammar,
        "max_tokens": max_tokens,
    }

    model_kwargs = {
        "n_gpu_layers": init_settings.n_gpu_layers,
        "use_mmap": init_settings.use_mmap,
        "use_mlock": init_settings.use_mlock,
        "f16_kv": init_settings.f16_kv,
        "seed": seed,
        "n_ctx": n_ctx,
        "n_batch": init_settings.n_batch,
        "n_threads": n_threads,
        "offload_kqv": init_settings.offload_kqv,
        "chat_format": "llama-2",  # @TODO Load from model_configs.chat_format
        # "torch_dtype": torch.float16,
        # "load_in_8bit": True,
    }

    llama_debug = LlamaDebugHandler(print_trace_on_end=True)
    callback_manager = CallbackManager([llama_debug])

    # @TODO Can we update these without needing to unload model?
    # From: https://docs.llamaindex.ai/en/stable/examples/llm/llama_2_llama_cpp.html
    llm = LlamaCPP(
        # Provide a url to download a model from
        model_url=None,
        # Or, you can set the path to a pre-downloaded model instead of model_url
        model_path=path_to_model,
        # Both max_new_tokens and temperature will override their generate_kwargs counterparts
        max_new_tokens=max_tokens,
        temperature=temperature,
        # llama2 has a context window of 4096 tokens, but we set it lower to allow for some wiggle room.
        # Note, this sets n_ctx in the model_kwargs below, so you don't need to pass it there.
        context_window=n_ctx,
        # kwargs to pass to __call__()
        generate_kwargs=generate_kwargs,
        # kwargs to pass to __init__()
        model_kwargs=model_kwargs,
        # Transform inputs into Llama2 format, swap out for other model's prompt template
        messages_to_prompt=messages_to_prompt,
        completion_to_prompt=completion_to_prompt,
        callback_manager=callback_manager,
        verbose=True,
    )
    return llm


# Remove from memory
def unload_text_model(llm):
    # Python garbage collector should cleanup if no ref to obj exists
    # https://github.com/abetlen/llama-cpp-python/issues/302
    del llm


def token_streamer(token_generator):
    # @TODO We may need to do some token parsing here...multi-byte encoding can cut off emoji/khanji chars.
    # result = "" # accumulate a final response to be encoded in utf-8 in entirety
    try:
        for token in token_generator:
            payload = {"event": "GENERATING_TOKENS", "data": f"{token}"}
            # print(token, end="", flush=True)
            yield json.dumps(payload)
    except (ValueError, UnicodeEncodeError, Exception) as e:
        msg = f"Error streaming tokens: {e}"
        print(msg)
        raise Exception(msg)


# Search through a database of embeddings and return similiar documents for llm to use as context
def query_memory(
    query: str,
    rag_prompt_template: classes.RagTemplateData,
    system_prompt: str,
    collection_names: List[str],
    app,
    db,
    options: dict,
):
    if app.state.llm == None:
        raise Exception("No Ai loaded.")

    # @TODO We can do filtering based on doc/collection name, metadata, etc via LlamaIndex.
    collection_name = collection_names[0]  # Only take the first collection for now
    # Update the LLM settings
    n_ctx = options.get("n_ctx") - 100  # for llama-index
    max_tokens = options.get("max_tokens")
    # Remove n_ctx from options
    del options["n_ctx"]
    app.state.llm.generate_kwargs.update(options)
    # Load the vector index
    indexDB = embedding.load_embedding(
        app,
        db,
        collection_name,
        max_tokens,
        n_ctx,
        system_prompt,
    )
    # Stream the response
    token_generator = embedding.query_embedding(query, rag_prompt_template, indexDB)
    return token_streamer(token_generator)


# Perform a normal text completion on a prompt
def text_completion(
    prompt: str, prompt_template: str, system_prompt: str, app, options
):
    llm: LlamaCPP = app.state.llm
    if llm == None:
        raise Exception("No Ai loaded.")

    # Format query from prompt template
    query_str = prompt
    if prompt_template:
        query_str = prompt_template.replace(QUERY_INPUT, prompt)
    # Format query to model spec, Inject system prompt into prompt
    if system_prompt:
        query_str = llm.completion_to_prompt(query_str, system_prompt)
    # Stream response
    token_generator = llm.stream_complete(query_str, kwargs=options)
    for token in token_generator:
        # print(token.delta, end="", flush=True)
        payload = {"event": "GENERATING_TOKENS", "data": f"{token.delta}"}
        yield json.dumps(payload)


# Perform a normal text chat conversation
def text_chat(messages: Sequence[str], system_prompt, app, options):
    llm: LlamaCPP = app.state.llm
    if llm == None:
        raise Exception("No Ai loaded.")

    # Format messages
    messages = llm.messages_to_prompt(messages, system_prompt)
    # Stream response
    token_generator = llm.stream_chat(messages, kwargs=options)
    for token in token_generator:
        # print(token.delta, end="", flush=True)
        payload = {"event": "GENERATING_TOKENS", "data": f"{token.delta}"}
        yield json.dumps(payload)
