import os
from fastapi import APIRouter, Request, HTTPException, Depends
from sse_starlette.sse import EventSourceResponse
from embeddings import main, query
from inference import text_llama_index
from core import classes, common
from huggingface_hub import (
    hf_hub_download,
    get_hf_file_metadata,
    hf_hub_url,
    ModelFilter,
    HfApi,
)

router = APIRouter()


# Return a list of all currently installed models and their metadata
@router.get("/installed")
def get_installed_models() -> classes.TextModelInstallMetadataResponse:
    try:
        data = []
        # Get installed models file
        metadatas: classes.InstalledTextModel = common.get_settings_file(
            common.APP_SETTINGS_PATH, common.MODEL_METADATAS_FILEPATH
        )
        if not metadatas:
            metadatas = common.DEFAULT_SETTINGS_DICT
        if common.INSTALLED_TEXT_MODELS in metadatas:
            data = metadatas[common.INSTALLED_TEXT_MODELS]
            return {
                "success": True,
                "message": "This is a list of all currently installed models.",
                "data": data,
            }
        else:
            raise Exception(
                f"No attribute {common.INSTALLED_TEXT_MODELS} exists in settings file."
            )
    except Exception as err:
        return {
            "success": False,
            "message": f"Failed to find any installed models. {err}",
            "data": [],
        }


# Gets the currently loaded model and its installation/config metadata
@router.get("/model")
def get_text_model(request: Request) -> classes.LoadedTextModelResponse | dict:
    app = request.app

    try:
        llm = app.state.llm
        model_id = app.state.model_id

        if llm:
            metadata = app.state.loaded_text_model_data
            return {
                "success": True,
                "message": f"Model {model_id} is currently loaded.",
                "data": metadata,
            }
        else:
            return {
                "success": False,
                "message": "No model is currently loaded.",
                "data": {},
            }
    except (Exception, KeyError, HTTPException) as error:
        return {
            "success": False,
            "message": f"Something went wrong: {error}",
            "data": {},
        }


# Eject the currently loaded Text Inference model
@router.post("/unload")
def unload_text_inference(request: Request):
    app = request.app
    text_llama_index.unload_text_model(app.state.llm)
    app.state.loaded_text_model_data = {}
    app.state.llm = None
    app.state.path_to_model = ""
    app.state.model_id = ""

    return {
        "success": True,
        "message": "Model was ejected",
        "data": None,
    }


# Start Text Inference service
@router.post("/load")
def load_text_inference(
    request: Request,
    data: classes.LoadInferenceRequest,
) -> classes.LoadInferenceResponse:
    app = request.app

    try:
        model_id = data.modelId
        mode = data.mode
        modelPath = data.modelPath
        callback_manager = main.create_index_callback_manager()
        # Record model's save path
        app.state.model_id = model_id
        app.state.path_to_model = modelPath
        # Unload the model if one exists
        if app.state.llm:
            print(
                f"{common.PRNT_API} Ejecting model {model_id} currently loaded from: {modelPath}"
            )
            unload_text_inference()
        # Load the specified Ai model
        if app.state.llm is None:
            model_settings = data.init
            generate_settings = data.call
            app.state.llm = text_llama_index.load_text_model(
                modelPath,
                mode,
                model_settings,
                generate_settings,
                callback_manager=callback_manager,
            )
            # Record the currently loaded model
            app.state.loaded_text_model_data = {
                "modelId": model_id,
                "mode": mode,
                "modelSettings": model_settings,
                "generateSettings": generate_settings,
            }
            print(f"{common.PRNT_API} Model {model_id} loaded from: {modelPath}")
        return {
            "message": f"AI model [{model_id}] loaded.",
            "success": True,
            "data": None,
        }
    except (Exception, KeyError) as error:
        return {
            "message": f"Unable to load AI model [{model_id}]\nMake sure you have available system memory.\n{error}",
            "success": False,
            "data": None,
        }


# Open OS file explorer on host machine
@router.get("/modelExplore")
def explore_text_model_dir() -> classes.FileExploreResponse:
    filePath = common.app_path(common.TEXT_MODELS_CACHE_DIR)

    if not os.path.exists(filePath):
        return {
            "success": False,
            "message": "No file path exists",
        }

    # Open a new os window
    common.file_explore(filePath)

    return {
        "success": True,
        "message": "Opened file explorer",
    }


# Search huggingface hub and return results
# https://huggingface.co/docs/huggingface_hub/en/guides/search
@router.get("/searchModels")
def search_models(payload):
    sort = payload.sort
    task = payload.task or "text-generation"
    limit = payload.limit or 10
    hf_api = HfApi()
    # @TODO Example showing how to filter by task and return only top 10 most downloaded
    models = hf_api.list_models(
        sort=sort,  # or "downloads" or "trending"
        limit=limit,
        filter=ModelFilter(
            task=task,
        ),
    )
    return {
        "success": True,
        "message": f"Returned {len(models)} results",
        "data": models,
    }


# Fetches repo info about a model from huggingface hub
@router.get("/getModelInfo")
def get_model_info(
    payload: classes.GetModelInfoRequest = Depends(),
):
    id = payload.repoId
    hf_api = HfApi()
    info = hf_api.model_info(repo_id=id, files_metadata=True)
    return {
        "success": True,
        "message": "Returned model info",
        "data": info,
    }


# Fetches metadata about a file from huggingface hub
@router.get("/getModelMetadata")
def get_model_metadata(payload):
    repo_id = payload.repo_id
    filename = payload.filename
    url = hf_hub_url(repo_id=repo_id, filename=filename)
    metadata = get_hf_file_metadata(url=url)

    return {
        "success": True,
        "message": "Returned model metadata",
        "data": metadata,
    }


# Download a text model from huggingface hub
# https://huggingface.co/docs/huggingface_hub/v0.21.4/en/package_reference/file_download#huggingface_hub.hf_hub_download
@router.post("/download")
def download_text_model(payload: classes.DownloadTextModelRequest):
    try:
        repo_id = payload.repo_id
        filename = payload.filename
        cache_dir = common.app_path(common.TEXT_MODELS_CACHE_DIR)
        resume_download = False
        # repo_type = "model" # optional, specify type of data, defaults to model
        # local_dir = "" # optional, downloaded file will be placed under this directory

        # Save initial path and details to json file
        common.save_text_model(
            {
                "repoId": repo_id,
                "savePath": {filename: ""},
            }
        )

        # Download model.
        # Returned path is symlink which isnt loadable; for our purposes we use get_cached_blob_path().
        hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            cache_dir=cache_dir,
            resume_download=resume_download,
            # local_dir=cache_dir,
            # local_dir_use_symlinks=False,
            # repo_type=repo_type,
        )

        # Get actual file path
        [model_cache_info, repo_revisions] = common.scan_cached_repo(
            cache_dir=cache_dir, repo_id=repo_id
        )
        # Get from dl path
        # file_path = common.app_path(download_path)

        # Get from huggingface hub managed cache dir
        file_path = common.get_cached_blob_path(
            repo_revisions=repo_revisions, filename=filename
        )
        if not isinstance(file_path, str):
            raise Exception("Path is not string.")

        # Save finalized details to disk
        common.save_text_model(
            {
                "repoId": repo_id,
                "savePath": {filename: file_path},
            }
        )

        return {
            "success": True,
            "message": f"Saved model file to {file_path}.",
        }
    except (KeyError, Exception, EnvironmentError, OSError, ValueError) as err:
        print(f"Error: {err}", flush=True)
        raise HTTPException(
            status_code=400, detail=f"Something went wrong. Reason: {err}"
        )


# Remove text model weights file and installation record.
# Current limitation is that this deletes all quant files for a repo.
@router.post("/delete")
def delete_text_model(payload: classes.DeleteTextModelRequest):
    filename = payload.filename
    repo_id = payload.repoId

    try:
        cache_dir = common.app_path(common.TEXT_MODELS_CACHE_DIR)

        # Checks file and throws if not found
        common.check_cached_file_exists(
            cache_dir=cache_dir, repo_id=repo_id, filename=filename
        )

        # Find model hash
        [model_cache_info, repo_revisions] = common.scan_cached_repo(
            cache_dir=cache_dir, repo_id=repo_id
        )
        repo_commit_hash = []
        for r in repo_revisions:
            repo_commit_hash.append(r.commit_hash)

        # Delete weights from cache, https://huggingface.co/docs/huggingface_hub/en/guides/manage-cache
        delete_strategy = model_cache_info.delete_revisions(*repo_commit_hash)
        delete_strategy.execute()
        freed_size = delete_strategy.expected_freed_size_str
        print(f"Freed {freed_size} space.", flush=True)

        # Delete install record from json file
        if freed_size != "0.0":
            common.delete_text_model_revisions(repo_id=repo_id)

        return {
            "success": True,
            "message": f"Deleted model file from {filename}. Freed {freed_size} of space.",
        }
    except (KeyError, Exception) as err:
        print(f"Error: {err}", flush=True)
        raise HTTPException(
            status_code=400, detail=f"Something went wrong. Reason: {err}"
        )


# Use Llama Index to run queries on vector database embeddings or run normal chat inference.
@router.post("/inference")
async def text_inference(
    request: Request,
    payload: classes.InferenceRequest,
):
    app = request.app

    try:
        prompt = payload.prompt
        messages = payload.messages
        collection_names = payload.collectionNames
        mode = payload.mode
        prompt_template = payload.promptTemplate
        rag_prompt_template = payload.ragPromptTemplate
        system_message = payload.systemMessage
        message_format = payload.messageFormat  # format wrapper for full prompt
        m_tokens = payload.max_tokens
        n_ctx = payload.n_ctx
        streaming = payload.stream
        max_tokens = common.calc_max_tokens(m_tokens, n_ctx, mode)
        options = dict(
            stream=streaming,
            temperature=payload.temperature,
            max_tokens=max_tokens,
            stop=payload.stop,
            echo=payload.echo,
            model=payload.model,
            grammar=payload.grammar,
            mirostat_tau=payload.mirostat_tau,
            tfs_z=payload.tfs_z,
            top_k=payload.top_k,
            top_p=payload.top_p,
            min_p=payload.min_p,
            seed=payload.seed,
            repeat_penalty=payload.repeat_penalty,
            presence_penalty=payload.presence_penalty,
            frequency_penalty=payload.frequency_penalty,
        )

        if not app.state.path_to_model:
            msg = "No path to model provided."
            print(f"Error: {msg}", flush=True)
            raise Exception(msg)
        if not app.state.llm:
            msg = "No LLM loaded."
            print(f"Error: {msg}", flush=True)
            raise Exception(msg)

        # Call LLM with context loaded via llama-index/vector store
        if collection_names is not None and len(collection_names) > 0:
            # Only take the first collection for now
            collection_name = collection_names[0]
            # Set LLM settings
            retrieval_options = dict(
                similarity_top_k=payload.similarity_top_k,
                response_mode=payload.response_mode,
            )
            # Update LLM generation options
            # app.state.llm.generate_kwargs.update(options)

            # Load embedding model for context retrieval
            main.define_embedding_model(app)

            # Load the vector index. @TODO Load multiple collections
            vector_index = main.load_embedding(app, collection_name)

            # Call LLM query engine
            res = query.query_embedding(
                llm=app.state.llm,
                query=prompt,
                prompt_template=rag_prompt_template,
                index=vector_index,
                options=retrieval_options,
                streaming=streaming,
            )
            # Return streaming response
            if streaming:
                token_generator = res.response_gen
                response = text_llama_index.token_streamer(token_generator)
                return EventSourceResponse(response)
            # Return non-stream response
            else:
                return res
        # Call LLM in raw completion mode
        elif mode == classes.CHAT_MODES.INSTRUCT.value:
            options["n_ctx"] = n_ctx
            # Return streaming response
            if streaming:
                return EventSourceResponse(
                    text_llama_index.text_stream_completion(
                        prompt,
                        prompt_template,
                        system_message,
                        message_format,
                        app,
                        options,
                    )
                )
            # Return non-stream response
            else:
                return text_llama_index.text_completion(
                    prompt,
                    prompt_template,
                    system_message,
                    message_format,
                    app,
                    options,
                )
        # Stream LLM in chat mode
        elif mode == classes.CHAT_MODES.CHAT.value:
            options["n_ctx"] = n_ctx
            return EventSourceResponse(
                text_llama_index.text_chat(
                    messages, system_message, message_format, app, options
                )
            )
        # elif mode == classes.CHAT_MODES.SLIDING.value:
        # do stuff here ...
        elif mode is None:
            raise Exception("Check 'mode' is provided.")
        else:
            raise Exception("No 'mode' or 'collection_names' provided.")
    except (KeyError, Exception) as err:
        print(f"Error: {err}", flush=True)
        raise HTTPException(
            status_code=400, detail=f"Something went wrong. Reason: {err}"
        )
