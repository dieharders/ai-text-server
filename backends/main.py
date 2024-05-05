import os
import sys
import threading
import json
import uvicorn
import webbrowser
import httpx
import socket
import pyqrcode
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from inference import text_llama_index
from embedding import embedding, storage, query
from server import common, classes
from routes import router as endpoint_router
from huggingface_hub import (
    hf_hub_download,
    get_hf_file_metadata,
    hf_hub_url,
    ModelFilter,
    HfApi,
)

server_info = None
server_thread = None
api_version = "0.4.2"
PLAYGROUND_SETTINGS_FILE_NAME = "playground.json"
BOT_SETTINGS_FILE_NAME = "bots.json"
SERVER_PORT = 8008
# Display where the admin can use the web UI
openbrew_studio_url = "https://studio.openbrewai.com"


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
    # https://www.python-httpx.org/quickstart/
    app.requests_client = httpx.Client()
    # Store some state here if you want...
    application.state.PORT_HOMEBREW_API = SERVER_PORT
    application.state.db_client = None
    application.state.llm = None  # Set each time user loads a model
    application.state.path_to_model = ""  # Set each time user loads a model
    application.state.model_id = ""
    application.state.embed_model = None
    app.state.loaded_text_model_data = {}

    yield
    # Do shutdown cleanup here...
    print(f"{common.PRNT_API} Lifespan shutdown")


app = FastAPI(title="Obrew🍺Server", version=api_version, lifespan=lifespan)
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Get paths for SSL certificate
SSL_KEY: str = common.dep_path("public/key.pem")
SSL_CERT: str = common.dep_path("public/cert.pem")
# Configure CORS settings
CUSTOM_ORIGINS_ENV: str = os.getenv("CUSTOM_ORIGINS")
CUSTOM_ORIGINS = CUSTOM_ORIGINS_ENV.split(",") if CUSTOM_ORIGINS_ENV else []
origins = [
    "http://localhost:3000",  # (optional) for testing client apps
    # "https://hoppscotch.io",  # (optional) for testing endpoints
    "https://brain-dump-dieharders.vercel.app",  # (optional) client app origin (preview)
    "https://homebrew-ai-discover.vercel.app",  # (optional) client app origin (production/alias)
    "https://studio.openbrewai.com",  # (required) client app origin (production/domain)
    *CUSTOM_ORIGINS,
]

# Redirect requests to our custom endpoints
# from fastapi import Request
# @app.middleware("http")
# async def redirect_middleware(request: Request, call_next):
#     return await redirects.text(request, call_next, str(app.PORT_TEXT_INFERENCE))


##############
### Routes ###
##############


# Add CORS support
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoint_router)


# Return a "connect" GUI page for user to config and startup the API server,
# then return the user to the supplied callback url with query params of config added.
# QRcode generation -> https://github.com/arjones/qr-generator/tree/main
@app.get("/", response_class=HTMLResponse)
async def connect_page(request: Request):
    remote_url = server_info["remote_ip"]
    local_url = server_info["local_ip"]
    # Generate QR code - direct to remote url
    qr_code = pyqrcode.create(
        f"{remote_url}:{SERVER_PORT}/?hostname={remote_url}&port={SERVER_PORT}"
    )
    qr_data = qr_code.png_as_base64_str(scale=5)
    # qr_image = qr_code.png("image.png", scale=8) # Write image file to disk

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "qr_data": qr_data,
            "title": "Connect to Obrew Server",
            "app_name": "Obrew🍺Server",
            "message": "Scan the code with your mobile device to access the WebUI remotely and/or click the link below.",
            "host": local_url,
            "remote_host": remote_url,
            "port": SERVER_PORT,
        },
    )


# Keep server/database alive
@app.get("/v1/ping")
def ping() -> classes.PingResponse:
    try:
        db = storage.get_vector_db_client(app)
        db.heartbeat()
        return {"success": True, "message": "pong"}
    except Exception as e:
        print(f"{common.PRNT_API} Error pinging server: {e}")
        return {"success": False, "message": ""}


# Tell client we are ready to accept requests
@app.get("/v1/connect")
def connect() -> classes.ConnectResponse:
    return {
        "success": True,
        "message": f"Connected to api server on port {SERVER_PORT}. Refer to 'https://localhost:{SERVER_PORT}/docs' for api docs.",
        "data": {
            "docs": f"https://localhost:{SERVER_PORT}/docs",
            "version": api_version,
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
        callback_manager = embedding.create_index_callback_manager()
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
        raise HTTPException(status_code=400, detail=f"Something went wrong: {error}")


# Open OS file explorer on host machine
@app.get("/v1/text/modelExplore")
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
@app.post("/v1/text/delete")
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
            embedding.define_embedding_model(app)

            # Load the vector index. @TODO Load multiple collections
            vector_index = embedding.load_embedding(app, collection_name)

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
            # @TODO Return non-stream response
            else:
                raise Exception("Non-streaming completion not supported.")
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


# Delete bot settings
@app.delete("/v1/persist/bot-settings")
def delete_bot_settings(name: str) -> classes.BotSettingsResponse:
    new_settings = []
    # Paths
    base_path = common.APP_SETTINGS_PATH
    file_name = BOT_SETTINGS_FILE_NAME
    file_path = os.path.join(base_path, file_name)
    try:
        # Try to open the file (if it exists)
        if os.path.exists(base_path):
            prev_settings = None
            with open(file_path, "r") as file:
                prev_settings = json.load(file)
                for setting in prev_settings:
                    if name == setting.get("model").get("botName"):
                        # Delete setting dict
                        del_index = prev_settings.index(setting)
                        del prev_settings[del_index]
                        # Save new settings
                        new_settings = prev_settings
                        break
            # Save new settings to file
            with open(file_path, "w") as file:
                if new_settings is not None:
                    json.dump(new_settings, file, indent=2)
    except FileNotFoundError:
        return {
            "success": False,
            "message": "Failed to delete bot setting. File does not exist.",
            "data": None,
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "message": "Failed to delete bot setting. Invalid JSON format or empty file.",
            "data": None,
        }

    msg = "Removed bot setting."
    print(f"{common.PRNT_API} {msg}")
    return {
        "success": True,
        "message": f"Success: {msg}",
        "data": new_settings,
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


def shutdown_server(*args):
    print(f"{common.PRNT_API} Shutting down server...", flush=True)
    # os.kill(os.getpid(), signal.SIGINT)
    # server_thread.join()
    print(f"{common.PRNT_API} Server shutdown complete.", flush=True)
    sys.exit(0)


def display_server_info():
    print(
        f"{common.PRNT_API} Navigate your browser to Obrew Studio for the admin web UI:\n-> {openbrew_studio_url}",
        flush=True,
    )
    # Display the local IP address of this server
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    # @TODO Can we infer the http protocol automatically somehow?
    remote_ip = f"https://{IPAddr}"
    local_ip = f"https://localhost"
    print(
        f"{common.PRNT_API} Refer to API docs for Obrew Server:\n-> {local_ip}:{SERVER_PORT}/docs \nOR\n-> {remote_ip}:{SERVER_PORT}/docs",
        flush=True,
    )
    return {
        "local_ip": local_ip,
        "remote_ip": remote_ip,
    }


def start_server():
    try:
        print(f"{common.PRNT_API} Starting API server...")
        # Start the ASGI server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=SERVER_PORT,
            log_level="info",
            # Include these to host over https
            # If server fails to start make sure the .pem files are generated in root dir
            ssl_keyfile=SSL_KEY,
            ssl_certfile=SSL_CERT,
        )
    except:
        print(f"{common.PRNT_API} Failed to start API server")


def run_server():
    # Start the API server in a separate thread from main
    fastapi_thread = threading.Thread(target=start_server)
    fastapi_thread.daemon = True  # let the parent kill the child thread at exit
    fastapi_thread.start()
    return fastapi_thread


if __name__ == "__main__":
    try:
        # Find IP info
        server_info = display_server_info()
        local_ip = server_info["local_ip"]
        local_url = f"{local_ip}:{SERVER_PORT}"
        # Open browser to WebUI
        print(f"{common.PRNT_API} API server started. Opening WebUI at {local_url}")
        webbrowser.open(local_url, new=2)
        print(f"{common.PRNT_API} Close this window to shutdown server.")
        # Start API server
        start_server()
    except KeyboardInterrupt:
        print(f"{common.PRNT_API} User pressed Ctrl+C exiting...")
        shutdown_server()
