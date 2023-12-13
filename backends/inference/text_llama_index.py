import json
from typing import List
from llama_index.llms import LlamaCPP
from llama_index.llms.llama_utils import messages_to_prompt, completion_to_prompt
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from embedding import embedding


# Low level llama-cpp-python object wrapped in class from LlamaIndex
def load_text_model(path_to_model):
    llama_debug = LlamaDebugHandler(print_trace_on_end=True)
    callback_manager = CallbackManager([llama_debug])

    llm = LlamaCPP(
        # provide a url to download a model from
        model_url=None,
        # or, you can set the path to a pre-downloaded model instead of model_url
        model_path=path_to_model,
        temperature=0.0,
        max_new_tokens=1024,
        # query_wrapper_prompt=query_wrapper_prompt,
        # llama2 has a context window of 4096 tokens, but we set it lower to allow for some wiggle room
        context_window=3900,  # note, this sets n_ctx in the model_kwargs below, so you don't need to pass it there.
        # kwargs to pass to __call__()
        generate_kwargs={},
        # kwargs to pass to __init__()
        # set to at least 1 to use GPU
        # model_kwargs={"n_gpu_layers": 4, "torch_dtype": torch.float16, "load_in_8bit": True},
        model_kwargs={},
        # transform inputs into Llama2 format
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
            yield json.dumps(payload)
    except (ValueError, UnicodeEncodeError, Exception) as e:
        msg = f"Error streaming tokens: {e}"
        print(msg)
        raise Exception(msg)


# Search through a database of embeddings and return similiar documents for llm to use as context
def query_memory(query: str, collection_names: List[str], app, db):
    if app.state.llm == None:
        app.state.llm = load_text_model(app.state.path_to_model)
    # @TODO We can do filtering based on doc/collection name, metadata, etc via LlamaIndex.
    collection_name = collection_names[0]  # Only take the first collection for now
    indexDB = embedding.load_embedding(app.state.llm, db, collection_name)
    # Stream the response
    token_generator = embedding.query_embedding(query, indexDB)
    return token_streamer(token_generator)
