import json
from typing import List, Optional
from llama_index.llms import LlamaCPP
from llama_index.llms.llama_utils import messages_to_prompt, completion_to_prompt
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from embedding import embedding

###
# Llama-Index allows us to search embeddings in a db and perform queries on them.
# It wraps llama-cpp-python so we can run inference from here as well.
###


# High level llama-cpp-python object wrapped in class from LlamaIndex
def load_text_model(
    path_to_model,
    settings: Optional[dict] = None,
    options: Optional[dict] = None,
):
    DEFAULT_CONTEXT_WINDOW = 3900
    DEFAULT_MAX_TOKENS = 128
    DEFAULT_TEMPERATURE = 0.2

    generate_kwargs = {
        "stream": options.get("stream", True),
        "stop": options.get(
            "stop",
            [
                # "\n",
                # "###",
                "[DONE]",
            ],
        ),
        "echo": options.get("echo", False),
        "model": options.get("model", "local"),
        "mirostat_tau": options.get("mirostat_tau", 5.0),
        "tfs_z": options.get("tfs_z", 1.0),
        "top_k": options.get("top_k", 40),
        "top_p": options.get("top_p", 0.95),
        "min_p": options.get("min_p", 0.05),
        "repeat_penalty": options.get("repeat_penalty", 1.1),
        "presence_penalty": options.get("presence_penalty", 0.0),
        "frequency_penalty": options.get("frequency_penalty", 0.0),
        "temperature": options.get("temperature", DEFAULT_TEMPERATURE),
        "seed": options.get("seed", 1337),
        "grammar": options.get("grammar", None),
        "max_tokens": options.get("max_tokens", DEFAULT_MAX_TOKENS),
    }

    model_kwargs = {}
    if bool(settings):
        model_kwargs = {
            # 32, n_gpu_layers should be exposed to users to adjust based on their hardware
            "n_gpu_layers": settings["n_gpu_layers"],
            "use_mmap": settings["use_mmap"],
            "use_mlock": settings["use_mlock"],
            "f16_kv": settings["f16_kv"],
            "seed": settings["seed"],
            "n_ctx": settings["n_ctx"],
            "n_batch": settings["n_batch"],
            "n_threads": settings["n_threads"],
            "offload_kqv": settings["offload_kqv"],
            # "torch_dtype": torch.float16,
            # "load_in_8bit": True,
        }

    llama_debug = LlamaDebugHandler(print_trace_on_end=True)
    callback_manager = CallbackManager([llama_debug])

    # @TODO Can we set update these without needing to unload model?
    # From: https://docs.llamaindex.ai/en/stable/examples/llm/llama_2_llama_cpp.html
    llm = LlamaCPP(
        # Provide a url to download a model from
        model_url=None,
        # Or, you can set the path to a pre-downloaded model instead of model_url
        model_path=path_to_model,
        # Both max_new_tokens and temperature will override their generate_kwargs counterparts
        max_new_tokens=options.get("max_tokens", DEFAULT_MAX_TOKENS),
        temperature=options.get("temperature", DEFAULT_TEMPERATURE),
        # query_wrapper_prompt=query_wrapper_prompt,
        # llama2 has a context window of 4096 tokens, but we set it lower to allow for some wiggle room.
        # Note, this sets n_ctx in the model_kwargs below, so you don't need to pass it there.
        context_window=options.get("n_ctx", DEFAULT_CONTEXT_WINDOW),
        # kwargs to pass to __call__()
        generate_kwargs=generate_kwargs,
        # kwargs to pass to __init__()
        model_kwargs=model_kwargs,
        # Transform inputs into Llama2 format
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
def query_memory(query: str, collection_names: List[str], app, db, options):
    if app.state.llm == None:
        raise Exception("No Ai loaded.")

    # @TODO We can do filtering based on doc/collection name, metadata, etc via LlamaIndex.
    collection_name = collection_names[0]  # Only take the first collection for now
    # Update the LLM settings
    app.state.llm.generate_kwargs.update(options)
    # Load the vector index
    indexDB = embedding.load_embedding(
        app,
        db,
        collection_name,
    )
    # Stream the response
    token_generator = embedding.query_embedding(query, indexDB)
    return token_streamer(token_generator)


# Perform a normal text completion on a prompt
def text_completion(prompt: str, app, options):
    llm: LlamaCPP = app.state.llm
    if llm == None:
        raise Exception("No Ai loaded.")

    # Stream response
    token_generator = llm.stream_complete(prompt, kwargs=options)
    for token in token_generator:
        # print(token.delta, end="", flush=True)
        payload = {"event": "GENERATING_TOKENS", "data": f"{token.delta}"}
        yield json.dumps(payload)
