import os
import sys
import signal
import threading
import glob
import json
import uvicorn
import httpx
import shutil
import socket
from dotenv import load_dotenv
from typing import List
from fastapi import (
    FastAPI,
    HTTPException,
    BackgroundTasks,
    File,
    UploadFile,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import tkinter as tk
from PIL import Image, ImageTk
from contextlib import asynccontextmanager
from inference import text_llama_index
from embedding import embedding
from server import common, classes
from routes import router as endpoint_router
from llama_index.response_synthesizers import ResponseMode
from huggingface_hub import (
    hf_hub_download,
    get_hf_file_metadata,
    hf_hub_url,
    ModelFilter,
    HfApi,
)

VECTOR_DB_FOLDER = "chromadb"
MEMORY_FOLDER = "memories"
PARSED_FOLDER = "parsed"
TMP_FOLDER = "tmp"
VECTOR_STORAGE_PATH = os.path.join(os.getcwd(), VECTOR_DB_FOLDER)
MEMORY_PATH = os.path.join(os.getcwd(), MEMORY_FOLDER)
PARSED_DOCUMENT_PATH = os.path.join(MEMORY_PATH, PARSED_FOLDER)
TMP_DOCUMENT_PATH = os.path.join(MEMORY_PATH, TMP_FOLDER)
PLAYGROUND_SETTINGS_FILE_NAME = "playground.json"
BOT_SETTINGS_FILE_NAME = "bots.json"
SERVER_PORT = 8008


# Parse runtime arguments passed to script
def parse_runtime_args():
    # Command-line arguments are accessed via sys.argv
    arguments = sys.argv[1:]
    # Initialize variables to store parsed arguments
    mode = None
    # Iterate through arguments and parse them
    for arg in arguments:
        if arg.startswith("--mode="):
            mode = arg.split("=")[1]
    return mode


buildEnv = parse_runtime_args()
isDebug = hasattr(sys, "gettrace") and sys.gettrace() is not None
isDev = buildEnv == "dev" or isDebug
isProd = buildEnv == "prod" or not isDev
if isProd:
    # Remove prints in prod when deploying in window mode
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

# Path to the .env file in the parent directory
current_directory = os.path.dirname(os.path.abspath(__file__))
parent_directory = os.path.dirname(current_directory)
env_path = os.path.join(parent_directory, ".env")
load_dotenv(env_path)


@asynccontextmanager
async def lifespan(application: FastAPI):
    print(f"{common.PRNT_API} Lifespan startup", flush=True)
    # Display where the admin can use the web UI
    openbrew_studio_url = "https://studio.openbrewai.com"
    print(
        f"{common.PRNT_API} Navigate your browser to OpenBrew Studio\n-> {openbrew_studio_url} for the admin web UI.",
        flush=True,
    )
    # Display the local IP address of this server
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    openbrew_server_ip = f"http://{IPAddr}:{SERVER_PORT}/docs"
    openbrew_server_local_ip = f"http://localhost:{SERVER_PORT}/docs"
    print(
        f"{common.PRNT_API} Refer to API docs for OpenBrew Server \n-> {openbrew_server_local_ip} \nOR\n-> {openbrew_server_ip}",
        flush=True,
    )
    # https://www.python-httpx.org/quickstart/
    app.requests_client = httpx.Client()
    # Store some state here if you want...
    application.state.PORT_HOMEBREW_API = SERVER_PORT
    application.state.storage_directory = VECTOR_STORAGE_PATH
    application.state.db_client = None
    application.state.llm = None  # Set each time user loads a model
    application.state.path_to_model = ""  # Set each time user loads a model
    application.state.model_id = ""
    app.state.loaded_text_model_data = {}

    yield

    print(f"{common.PRNT_API} Lifespan shutdown")


app = FastAPI(title="🍺 HomeBrew API server", version="0.2.0", lifespan=lifespan)


# Configure CORS settings
CUSTOM_ORIGINS_ENV: str = os.getenv("CUSTOM_ORIGINS")
CUSTOM_ORIGINS = CUSTOM_ORIGINS_ENV.split(",") if CUSTOM_ORIGINS_ENV else []
origins = [
    "http://localhost:3000",  # (optional) for testing client apps
    # "https://hoppscotch.io",  # (optional) for testing endpoints
    "https://brain-dump-dieharders.vercel.app",  # (required) client app origin (preview)
    "https://homebrew-ai-discover.vercel.app",  # (required) client app origin (production/alias)
    "https://studio.openbrewai.com",  # (required) client app origin (production/domain)
    *CUSTOM_ORIGINS,
]

# Redirect requests to our custom endpoints
# from fastapi import Request
# @app.middleware("http")
# async def redirect_middleware(request: Request, call_next):
#     return await redirects.text(request, call_next, str(app.PORT_TEXT_INFERENCE))


# Add CORS support
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

##############
### Routes ###
##############

app.include_router(endpoint_router)


# Keep server/database alive
@app.get("/v1/ping")
def ping() -> classes.PingResponse:
    try:
        db = embedding.get_vectordb_client(app)
        db.heartbeat()
        return {"success": True, "message": "pong"}
    except Exception as e:
        print(f"{common.PRNT_API} Error pinging server: {e}")
        return {"success": False, "message": ""}


# Tell client we are ready to accept requests
@app.get("/v1/connect")
def connect() -> classes.ConnectResponse:
    version = "0.2.0"

    return {
        "success": True,
        "message": f"Connected to api server on port {SERVER_PORT}. Refer to 'http://localhost:{SERVER_PORT}/docs' for api docs.",
        "data": {
            "docs": f"http://localhost:{SERVER_PORT}/docs",
            "version": version,
            # @TODO Lets just return everything that /services/api does.
            # "api": "/v1/services/api", # endpoint to tell front-end what all the endpoints are
        },
    }


# Return a list of all currently installed models and their metadata
@app.get("/v1/text/installed")
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
@app.get("/v1/text/model")
def get_text_model() -> classes.LoadedTextModelResponse | dict:
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
@app.post("/v1/text/unload")
def unload_text_inference():
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
@app.post("/v1/text/load")
def load_text_inference(
    data: classes.LoadInferenceRequest,
) -> classes.LoadInferenceResponse:
    try:
        model_id = data.modelId
        mode = data.mode
        modelPath = data.modelPath
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
                modelPath, mode, model_settings, generate_settings
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
        raise HTTPException(status_code=400, detail=f"Something went wrong: {error}")


# Open OS file explorer on host machine
@app.get("/v1/text/modelExplore")
def explore_text_model_dir() -> classes.FileExploreResponse:
    filePath = os.path.join(os.getcwd(), common.MODELS_CACHE_DIR)

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
@app.get("/v1/text/searchModels")
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
@app.get("/v1/text/getModelInfo")
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
@app.get("/v1/text/getModelMetadata")
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
@app.post("/v1/text/download")
def download_text_model(payload: classes.DownloadTextModelRequest):
    try:
        repo_id = payload.repo_id
        filename = payload.filename
        cache_dir = os.path.join(os.getcwd(), common.MODELS_CACHE_DIR)
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
        # file_path = os.path.join(os.getcwd(), download_path)
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
@app.post("/v1/text/delete")
def delete_text_model(payload: classes.DeleteTextModelRequest):
    filename = payload.filename
    repo_id = payload.repoId

    try:
        cache_dir = os.path.join(os.getcwd(), common.MODELS_CACHE_DIR)

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
@app.post("/v1/text/inference")
async def text_inference(payload: classes.InferenceRequest):
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
        max_tokens = common.calc_max_tokens(m_tokens, n_ctx, mode)
        options = dict(
            stream=payload.stream,
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
                similarity_top_k=payload.similarity_top_k or 1,
                response_mode=payload.response_mode or ResponseMode.COMPACT,
            )
            # Update LLM generation options
            # app.state.llm.generate_kwargs.update(options)

            # Load the vector index
            indexDB = embedding.load_embedding(app, collection_name)

            # Call LLM query engine
            res = embedding.query_embedding(
                prompt, rag_prompt_template, indexDB, retrieval_options
            )
            token_generator = res.response_gen
            response = text_llama_index.token_streamer(token_generator)
            return EventSourceResponse(response)
        # Call LLM in raw completion mode
        elif mode == classes.CHAT_MODES.INSTRUCT.value:
            options["n_ctx"] = n_ctx
            return EventSourceResponse(
                text_llama_index.text_completion(
                    prompt,
                    prompt_template,
                    system_message,
                    message_format,
                    app,
                    options,
                )
            )
        # Call LLM in raw chat mode
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


# Pre-process supplied files into a text format and save to disk for embedding later.
@app.post("/v1/embeddings/preProcess")
def pre_process_documents(
    form: classes.PreProcessRequest = Depends(),
) -> classes.PreProcessResponse:
    try:
        # Validate inputs
        document_id = form.document_id
        file_path = form.filePath
        collection_name = form.collection_name
        document_name = form.document_name
        if not common.check_valid_id(collection_name) or not common.check_valid_id(
            document_name
        ):
            raise Exception(
                "Invalid input. No '--', uppercase, spaces or special chars allowed."
            )
        # Validate tags
        parsed_tags = common.parse_valid_tags(form.tags)
        if parsed_tags == None:
            raise Exception("Invalid value for 'tags' input.")
        # Process files
        processed_file = embedding.pre_process_documents(
            document_id=document_id,
            document_name=document_name,
            collection_name=collection_name,
            description=form.description,
            tags=parsed_tags,
            input_file_path=file_path,
            output_folder_path=PARSED_DOCUMENT_PATH,
        )

        return {
            "success": True,
            "message": f"Successfully processed {file_path}",
            "data": processed_file,
        }
    except (Exception, ValueError, TypeError, KeyError) as error:
        return {
            "success": False,
            "message": f"There was an internal server error uploading the file:\n{error}",
            "data": {},
        }


@app.get("/v1/memory/addCollection")
def create_memory_collection(
    form: classes.AddCollectionRequest = Depends(),
) -> classes.AddCollectionResponse:
    try:
        parsed_tags = common.parse_valid_tags(form.tags)
        collection_name = form.collectionName
        if not collection_name:
            raise Exception("You must supply a collection name.")
        if parsed_tags == None:
            raise Exception("Invalid value for 'tags' input.")
        if not common.check_valid_id(collection_name):
            raise Exception(
                "Invalid collection name. No '--', uppercase, spaces or special chars allowed."
            )
        # Create payload. ChromaDB only accepts strings, numbers, bools.
        metadata = {
            "tags": parsed_tags,
            "description": form.description,
            "sources": json.dumps([]),
        }
        # Apply input values to collection metadata
        db_client = embedding.get_vectordb_client(app)
        db_client.create_collection(
            name=collection_name,
            metadata=metadata,
            # embedding_function=custom_embed_function,
        )
        return {
            "success": True,
            "message": f"Successfully created new collection [{collection_name}]",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create new collection [{collection_name}]: {e}",
        }


# Create a memory for Ai.
# This is a multi-step process involving several endpoints.
# It will first process the file, then embed its data into vector space and
# finally add it as a document to specified collection.
@app.post("/v1/memory/addDocument")
async def create_memory(
    form: classes.EmbedDocumentRequest = Depends(),
    file: UploadFile = File(None),  # File(...) means required
    background_tasks: BackgroundTasks = None,  # This prop is auto populated by FastAPI
) -> classes.AddDocumentResponse:
    try:
        document_name = form.documentName
        collection_name = form.collectionName
        description = form.description
        tags = common.parse_valid_tags(form.tags)
        url_path = form.urlPath
        text_input = form.textInput
        tmp_input_file_path = ""
        chunk_size = form.chunkSize
        chunk_overlap = form.chunkOverlap
        chunk_strategy = form.chunkStrategy

        if file == None and url_path == "" and text_input == "":
            raise Exception("You must supply a file upload, url or text.")
        if not document_name or not collection_name:
            raise Exception("You must supply a collection and memory name.")
        if tags == None:
            raise Exception("Invalid value for 'tags' input.")
        if not common.check_valid_id(document_name):
            raise Exception(
                "Invalid memory name. No '--', uppercase, spaces or special chars allowed."
            )

        # Save temp files to disk first. The filename doesnt matter much.
        tmp_folder = TMP_DOCUMENT_PATH
        filename = embedding.create_parsed_filename(collection_name, document_name)
        tmp_input_file_path = os.path.join(tmp_folder, filename)
        if url_path:
            print(
                f"{common.PRNT_API} Downloading file from url {url_path} to {tmp_input_file_path}"
            )
            if not os.path.exists(tmp_folder):
                os.makedirs(tmp_folder)
            # Download the file and save to disk
            await common.get_file_from_url(url_path, tmp_input_file_path, app)
        elif text_input:
            print(f"{common.PRNT_API} Saving raw text to file...\n{text_input}")
            if not os.path.exists(tmp_folder):
                os.makedirs(tmp_folder)
            # Write to file
            with open(tmp_input_file_path, "w") as f:
                f.write(text_input)
        elif file:
            print(f"{common.PRNT_API} Saving uploaded file to disk...")
            # Read the uploaded file in chunks of 1mb,
            # store to a tmp dir for processing later
            if not os.path.exists(tmp_folder):
                os.makedirs(tmp_folder)
            with open(tmp_input_file_path, "wb") as f:
                while contents := file.file.read(1024 * 1024):
                    f.write(contents)
            file.file.close()
        else:
            raise Exception("No file or url supplied")

        # Parse/Process input files
        processed_file = embedding.pre_process_documents(
            document_name=document_name,
            collection_name=collection_name,
            description=description,
            tags=tags,
            input_file_path=tmp_input_file_path,
            output_folder_path=PARSED_DOCUMENT_PATH,
        )

        # Create embeddings
        print(f"{common.PRNT_API} Start embedding...")
        embed_form = {
            "collection_name": collection_name,
            "document_name": document_name,
            "document_id": processed_file["document_id"],
            "description": description,
            "tags": tags,
            "is_update": False,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "chunk_strategy": chunk_strategy,
        }
        background_tasks.add_task(
            embedding.create_embedding,
            processed_file,
            embed_form,
            app,
        )
    except (Exception, KeyError) as e:
        # Error
        msg = f"Failed to create a new memory: {e}"
        print(f"{common.PRNT_API} {msg}")
        return {
            "success": False,
            "message": msg,
        }
    else:
        msg = "A new memory has been added to the queue. It will be available for use shortly."
        print(f"{common.PRNT_API} {msg}", flush=True)
        return {
            "success": True,
            "message": msg,
        }
    finally:
        # Delete uploaded tmp file
        if os.path.exists(tmp_input_file_path):
            os.remove(tmp_input_file_path)
            print(f"{common.PRNT_API} Removed temp file.")


@app.get("/v1/memory/getAllCollections")
def get_all_collections() -> classes.GetAllCollectionsResponse:
    try:
        db = embedding.get_vectordb_client(app)
        collections = db.list_collections()

        # Parse json data
        for collection in collections:
            metadata = collection.metadata
            if "sources" in metadata:
                sources_json = metadata["sources"]
                sources_data = json.loads(sources_json)
                metadata["sources"] = sources_data

        return {
            "success": True,
            "message": f"Returned {len(collections)} collection(s)",
            "data": collections,
        }
    except Exception as e:
        print(f"{common.PRNT_API} Error: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": [],
        }


# Return a collection by id and all its documents
@app.post("/v1/memory/getCollection")
def get_collection(
    props: classes.GetCollectionRequest,
) -> classes.GetCollectionResponse:
    try:
        db = embedding.get_vectordb_client(app)
        id = props.id
        collection = db.get_collection(id)
        num_items = 0
        metadata = collection.metadata
        if metadata == None:
            raise Exception("No metadata found for collection")

        if "sources" in metadata:
            sources_json = metadata["sources"]
            sources_data = json.loads(sources_json)
            num_items = len(sources_data)
            metadata["sources"] = sources_data

        return {
            "success": True,
            "message": f"Returned {num_items} source(s) in collection [{id}]",
            "data": {
                "collection": collection,
                "numItems": num_items,
            },
        }
    except Exception as e:
        print(f"{common.PRNT_API} Error: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": {},
        }


# Get one or more documents by id.
@app.post("/v1/memory/getDocument")
def get_document(params: classes.GetDocumentRequest) -> classes.GetDocumentResponse:
    try:
        collection_id = params.collection_id
        document_ids = params.document_ids
        include = params.include

        documents = embedding.get_document(
            collection_name=collection_id,
            document_ids=document_ids,
            app=app,
            include=include,
        )

        num_documents = len(documents)

        return {
            "success": True,
            "message": f"Returned {num_documents} document(s)",
            "data": documents,
        }
    except Exception as e:
        print(f"{common.PRNT_API} Error: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": [],
        }


# Open an OS file exporer on host machine
@app.get("/v1/memory/fileExplore")
def explore_source_file(
    params: classes.FileExploreRequest = Depends(),
) -> classes.FileExploreResponse:
    filePath = params.filePath

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


# Re-process and re-embed existing document(s) from /parsed directory or url link
@app.post("/v1/memory/updateDocument")
async def update_memory(
    form: classes.UpdateEmbeddedDocumentRequest,
    background_tasks: BackgroundTasks = None,  # This prop is auto populated by FastAPI
) -> classes.UpdateDocumentResponse:
    try:
        collection_name = form.collectionName
        document_id = form.documentId
        document_name = form.documentName
        metadata = form.metadata  # @TODO Should we re-create this?
        url_path = form.urlPath
        file_path = form.filePath
        chunk_size = form.chunkSize
        chunk_overlap = form.chunkOverlap
        chunk_strategy = form.chunkStrategy
        document = None
        document_metadata = {}

        # Verify id's
        if not collection_name or not document_name or not document_id:
            raise Exception(
                "Please supply a collection name, document name, and document id"
            )
        if not common.check_valid_id(document_name):
            raise Exception(
                "Invalid memory name. No '--', uppercase, spaces or special chars allowed."
            )

        # Retrieve document data
        documents = embedding.get_document(
            collection_name=collection_name,
            document_ids=[document_id],
            app=app,
            include=["documents", "metadatas"],
        )
        if len(documents) >= 1:
            document = documents[0]
            document_metadata = document["metadata"]

        if not document:
            raise Exception("No record could be found for that memory")

        # Fetch file(s)
        new_file_name = embedding.create_parsed_filename(collection_name, document_id)
        tmp_folder = TMP_DOCUMENT_PATH
        tmp_file_path = os.path.join(TMP_DOCUMENT_PATH, new_file_name)
        if url_path:
            # Download the file and save to disk
            print(f"{common.PRNT_API} Downloading file to {tmp_file_path} ...")
            await common.get_file_from_url(url_path, tmp_file_path, app)
        elif file_path:
            # Copy file from provided location to /tmp dir, only if paths differ
            print(f"{common.PRNT_API} Loading local file from disk {file_path} ...")
            if file_path != tmp_file_path:
                if not os.path.exists(tmp_folder):
                    os.makedirs(tmp_folder)
                shutil.copy(file_path, tmp_file_path)
            print(f"{common.PRNT_API} File to be copied already in /tmp dir")
        else:
            raise Exception("Please supply a local path or url to a file")

        # Compare checksums
        updated_document_metadata = {}
        new_file_hash = embedding.create_checksum(tmp_file_path)
        stored_file_hash = document_metadata["checksum"]
        if new_file_hash != stored_file_hash:
            # Pass provided metadata or stored
            updated_document_metadata = metadata or document_metadata
            description = updated_document_metadata["description"]
            # Validate tags
            updated_tags = common.parse_valid_tags(updated_document_metadata["tags"])
            if updated_tags == None:
                raise Exception("Invalid value for 'tags' input.")
            # Process input documents
            processed_file = embedding.pre_process_documents(
                document_id=document_id,
                document_name=document_name,
                collection_name=collection_name,
                description=description,
                tags=updated_tags,
                input_file_path=tmp_file_path,
                output_folder_path=PARSED_DOCUMENT_PATH,
            )
            # Create text embeddings
            form = {
                "collection_name": collection_name,
                "document_name": document_name,
                "document_id": document_id,
                "description": description,
                "tags": updated_tags,
                "is_update": True,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "chunk_strategy": chunk_strategy,
            }
            background_tasks.add_task(
                embedding.create_embedding,
                processed_file,
                form,
                app,
            )
        else:
            # Delete tmp files if exist
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
            # If same input file, abort
            raise Exception("Input file has not changed.")

        return {
            "success": True,
            "message": f"Updated memories [{document_name}]",
        }
    except Exception as e:
        print(f"{common.PRNT_API} Error: {e}")
        return {
            "success": False,
            "message": f"{e}",
        }


# Delete a document by id
@app.post("/v1/memory/deleteDocuments")
def delete_documents(
    params: classes.DeleteDocumentsRequest,
) -> classes.DeleteDocumentsResponse:
    try:
        collection_id = params.collection_id
        document_ids = params.document_ids
        num_documents = len(document_ids)
        document = None
        db = embedding.get_vectordb_client(app)
        collection = db.get_collection(collection_id)
        sources: List[str] = json.loads(collection.metadata["sources"])
        source_file_path = ""
        documents = embedding.get_document(
            collection_name=collection_id,
            document_ids=document_ids,
            app=app,
            include=["metadatas"],
        )
        # Delete all files and references associated with embedded docs
        for document in documents:
            document_metadata = document["metadata"]
            source_file_path = document_metadata["filePath"]
            document_id = document_metadata["id"]
            # Remove file from disk
            print(
                f"{common.PRNT_API} Remove file {document_id} from {source_file_path}"
            )
            if os.path.exists(source_file_path):
                os.remove(source_file_path)
            # Remove source reference from collection array
            sources.remove(document_id)
            # Update collection
            sources_json = json.dumps(sources)
            collection.metadata["sources"] = sources_json
            collection.modify(metadata=collection.metadata)
            # Delete embeddings from llama-index @TODO Verify this works
            index = embedding.load_embedding(app, collection_id)
            index.delete(document_id)
        # Delete the embeddings from collection
        collection.delete(ids=document_ids)

        return {
            "success": True,
            "message": f"Removed {num_documents} document(s): {document_ids}",
        }
    except Exception as e:
        print(f"{common.PRNT_API} Error: {e}")
        return {
            "success": False,
            "message": str(e),
        }


# Delete a collection by id
@app.get("/v1/memory/deleteCollection")
def delete_collection(
    params: classes.DeleteCollectionRequest = Depends(),
) -> classes.DeleteCollectionResponse:
    try:
        collection_id = params.collection_id
        db = embedding.get_vectordb_client(app)
        collection = db.get_collection(collection_id)
        sources: List[str] = json.loads(collection.metadata["sources"])
        include = ["documents", "metadatas"]
        # Remove all associated source files
        documents = embedding.get_document(
            collection_name=collection_id,
            document_ids=sources,
            app=app,
            include=include,
        )
        for document in documents:
            document_metadata = document["metadata"]
            filePath = document_metadata["filePath"]
            os.remove(filePath)
        # Remove the collection
        db.delete_collection(name=collection_id)
        # Remove persisted vector index from disk
        common.delete_vector_store(collection_id, VECTOR_STORAGE_PATH)

        return {
            "success": True,
            "message": f"Removed collection [{collection_id}]",
        }
    except Exception as e:
        print(f"{common.PRNT_API} Error: {e}")
        return {
            "success": False,
            "message": str(e),
        }


# Completely wipe database
@app.get("/v1/memory/wipe")
def wipe_all_memories() -> classes.WipeMemoriesResponse:
    try:
        # Delete all db values
        db = embedding.get_vectordb_client(app)
        db.reset()
        # Delete all parsed documents/files in /memories
        if os.path.exists(TMP_DOCUMENT_PATH):
            files = glob.glob(f"{TMP_DOCUMENT_PATH}/*")
            for f in files:
                os.remove(f)  # del files
            os.rmdir(TMP_DOCUMENT_PATH)  # del folder
        if os.path.exists(PARSED_DOCUMENT_PATH):
            files = glob.glob(f"{PARSED_DOCUMENT_PATH}/*.md")
            for f in files:
                os.remove(f)  # del all .md files
            os.rmdir(PARSED_DOCUMENT_PATH)  # del folder
        # Remove all vector storage collections and folders
        if os.path.exists(VECTOR_STORAGE_PATH):
            folders = glob.glob(f"{VECTOR_STORAGE_PATH}/*")
            for dir in folders:
                if "chroma.sqlite3" not in dir:
                    files = glob.glob(f"{dir}/*")
                    for f in files:
                        os.remove(f)  # del files
                    os.rmdir(dir)  # del collection folder
        # Remove root vector storage folder and database file
        # os.remove(os.path.join(app.state.storage_directory, "chroma.sqlite3"))
        # os.rmdir(app.state.storage_directory)

        # Acknowledge success
        return {
            "success": True,
            "message": "Successfully wiped all memories from Ai",
        }
    except Exception as e:
        print(f"{common.PRNT_API} Error: {e}")
        return {
            "success": False,
            "message": str(e),
        }


# Load playground settings
@app.get("/v1/persist/playground-settings")
def get_playground_settings() -> classes.GetPlaygroundSettingsResponse:
    # Paths
    file_name = PLAYGROUND_SETTINGS_FILE_NAME
    file_path = os.path.join(common.APP_SETTINGS_PATH, file_name)
    loaded_data = {}

    # Check if folder exists
    if not os.path.exists(common.APP_SETTINGS_PATH):
        print("Path does not exist.", flush=True)
        os.makedirs(common.APP_SETTINGS_PATH)

    try:
        # Open the file
        with open(file_path, "r") as file:
            loaded_data = json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist, fail
        print("No file exists.", flush=True)

    return {
        "success": True,
        "message": f"Returned app settings",
        "data": loaded_data,
    }


# Save playground settings
@app.post("/v1/persist/playground-settings")
def save_playground_settings(data: dict) -> classes.GenericEmptyResponse:
    # Paths
    file_name = PLAYGROUND_SETTINGS_FILE_NAME
    file_path = os.path.join(common.APP_SETTINGS_PATH, file_name)

    # Save to disk
    common.save_settings_file(common.APP_SETTINGS_PATH, file_path, data)

    return {
        "success": True,
        "message": f"Saved settings to {file_path}",
        "data": None,
    }


# Save bot settings
@app.post("/v1/persist/bot-settings")
def save_bot_settings(settings: dict) -> classes.BotSettingsResponse:
    # Paths
    file_name = BOT_SETTINGS_FILE_NAME
    file_path = os.path.join(common.APP_SETTINGS_PATH, file_name)
    # Save to memory
    results = common.save_bot_settings_file(
        common.APP_SETTINGS_PATH, file_path, settings
    )

    return {
        "success": True,
        "message": f"Saved bot settings to {file_path}",
        "data": results,
    }


# Load bot settings
@app.get("/v1/persist/bot-settings")
def get_bot_settings() -> classes.BotSettingsResponse:
    # Paths
    file_name = BOT_SETTINGS_FILE_NAME
    file_path = os.path.join(common.APP_SETTINGS_PATH, file_name)

    # Check if folder exists
    if not os.path.exists(common.APP_SETTINGS_PATH):
        return {
            "success": False,
            "message": "Failed to return settings. Folder does not exist.",
            "data": [],
        }

    # Try to open the file (if it exists)
    loaded_data = []
    try:
        with open(file_path, "r") as file:
            loaded_data = json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist, return empty
        return {
            "success": False,
            "message": "Failed to return settings. File does not exist.",
            "data": [],
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "message": "Invalid JSON format or empty file.",
            "data": [],
        }

    return {
        "success": True,
        "message": f"Returned bot settings",
        "data": loaded_data,
    }


# Methods...


class Window:
    def __init__(self, master):
        # @TODO Swap out with a UI or other image
        self.img = Image.open("public/splash.png")
        self.img = self.img.resize((640, 480), Image.FILTERED)

        self.img = ImageTk.PhotoImage(self.img)

        label = tk.Label(master, image=self.img)
        label.pack(expand=True, fill=tk.BOTH)


# Function to create and run the Tkinter window
def run_GUI():
    root = tk.Tk()
    root.title("OpenBrew Server")
    window = Window(root)
    root.mainloop()


def run_server():
    try:
        print(f"{common.PRNT_API} Starting API server...")
        # Start the ASGI server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=SERVER_PORT,
            log_level="info",
        )
        return True
    except:
        print(f"{common.PRNT_API} Failed to start API server")
        return False


if __name__ == "__main__":
    # Start the API server in a separate thread
    fastapi_thread = threading.Thread(target=run_server)
    fastapi_thread.start()
    # GUI window
    if isProd:
        run_GUI()
        # Handle stopping the server when window is closed
        print(f"{common.PRNT_API} Shutting down", flush=True)
        os.kill(os.getpid(), signal.SIGINT)
