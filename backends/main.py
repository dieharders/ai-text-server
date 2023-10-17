import os
import json
import uvicorn
import subprocess
import asyncio
import httpx
from typing import List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Initialize timer variables for "ping" check
ping_timeout = 60  # seconds


@asynccontextmanager
async def lifespan(application: FastAPI):
    print("[homebrew api] Lifespan startup")
    app.requests_client = httpx.AsyncClient()
    app.text_model_config = {}
    # Store some state here if you want...
    # application.state.super_secret = secrets.token_hex(16)

    yield

    print("[homebrew api] Lifespan shutdown")
    killTextInference()


app = FastAPI(title="🍺 HomeBrew API server", version="0.0.1", lifespan=lifespan)


# Configure CORS settings
origins = [
    "http://localhost:3000",  # (optional) for testing client apps
    "https://hoppscotch.io",  # (optional) for testing endpoints
    "http://localhost:8000",  # (required) Homebrew front-end
    "https://brain-dump-dieharders.vercel.app/",  # (required) client app origin
]


# Redirect requests to our custom endpoints
# from fastapi import Request
# @app.middleware("http")
# async def redirect_middleware(request: Request, call_next):
#     return await redirects.text(request, call_next, str(app.PORT_TEXT_INFERENCE))


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/ping")
async def ping(request: Request):
    # Can get state from app lifecycle here
    # request.app.state.super_secret

    # Restart "ping" timer
    success = False
    # Request /v1/models endpoint on inference server to determine if alive
    client = request.app.requests_client
    result = None
    try:
        response = await client.get(
            f"http://127.0.0.1:{app.PORT_TEXT_INFERENCE}/v1/models"
        )
        result = response.json()
    except Exception as e:
        print(f"[homebrew api] Error pinging inference server: {e}")

    # Process exists
    # if hasattr(app, "text_inference_process"):
    #     if app.text_inference_process.poll() is None:
    #         startPingTimer()
    #         success = True

    # Server exists
    if result:
        if "data" in result:
            startPingTimer()
            success = True

    return {"success": success, "message": "pong"}


class ConnectResponse(BaseModel):
    success: bool
    message: str
    data: dict

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Connected to api server on port 8008.",
                    "data": {"docs": "http://localhost:8008/docs"},
                }
            ]
        }
    }


# Tell client we are ready to accept requests
@app.get("/v1/connect")
def connect() -> ConnectResponse:
    return {
        "success": True,
        "message": f"Connected to api server on port {app.PORT_HOMEBREW_API}. Refer to 'http://localhost:{app.PORT_HOMEBREW_API}/docs' for api docs.",
        "data": {
            "docs": f"http://localhost:{app.PORT_HOMEBREW_API}/docs",
        },
    }


# Load in the ai model to be used for inference.
class LoadInferenceRequest(BaseModel):
    modelId: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "modelId": "llama-2-13b-chat-ggml",
                }
            ]
        }
    }


class LoadInferenceResponse(BaseModel):
    message: str
    success: bool

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "AI model [llama-2-13b-chat-ggml] loaded.",
                    "success": True,
                }
            ]
        }
    }


@app.post("/v1/text/load")
def load_text_inference(data: LoadInferenceRequest) -> LoadInferenceResponse:
    try:
        model_id: str = data.modelId
        # Logic to load the specified ai model here...
        return {"message": f"AI model [{model_id}] loaded.", "success": True}
    except KeyError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON format: 'modelId' key not found"
        )


class StartInferenceRequest(BaseModel):
    modelConfig: dict

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "modelConfig": {
                        "promptTemplate": "Instructions:{{PROMPT}}\n\n### Response:",
                        "savePath": "C:\\Project Files\\brain-dump-ai\\models\\llama-2-13b-chat.ggmlv3.q2_K.bin",
                        "id": "llama2-13b",
                        "numTimesRun": 0,
                        "isFavorited": False,
                        "validation": "success",
                        "modified": "Tue, 19 Sep 2023 23:25:28 GMT",
                        "size": 1200000,
                        "endChunk": 13,
                        "progress": 67,
                        "tokenizerPath": "/some/path/to/tokenizer",
                        "checksum": "90b27795b2e319a93cc7c3b1a928eefedf7bd6acd3ecdbd006805f7a028ce79d",
                    },
                }
            ]
        }
    }


class StartInferenceResponse(BaseModel):
    success: bool
    message: str
    data: dict

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "AI text inference started.",
                    "data": {
                        "port": 8080,
                        "docs": "http://localhost:8080/docs",
                        "textModelConfig": {
                            "promptTemplate": "Instructions:{{PROMPT}}\n\n### Response:",
                            "savePath": "C:\\Project Files\\brain-dump-ai\\models\\llama-2-13b-chat.ggmlv3.q2_K.bin",
                            "id": "llama2-13b",
                            "numTimesRun": 0,
                            "isFavorited": False,
                            "validation": "success",
                            "modified": "Tue, 19 Sep 2023 23:25:28 GMT",
                            "size": 1200000,
                            "endChunk": 13,
                            "progress": 67,
                            "tokenizerPath": "/some/path/to/tokenizer",
                            "checksum": "90b27795b2e319a93cc7c3b1a928eefedf7bd6acd3ecdbd006805f7a028ce79d",
                        },
                    },
                }
            ]
        }
    }


# Starts the text inference server
@app.post("/v1/text/start")
async def start_text_inference(data: StartInferenceRequest) -> StartInferenceResponse:
    try:
        # Store the current model's configuration for later reference
        app.text_model_config = data.modelConfig
        # Send signal to start server
        model_file_path: str = data.modelConfig["savePath"]
        isStarted = await start_text_inference_server(model_file_path)

        return {
            "success": isStarted,
            "message": "AI inference started.",
            "data": {
                "port": app.PORT_TEXT_INFERENCE,
                "docs": f"http://localhost:{app.PORT_TEXT_INFERENCE}/docs",
                "text_model_config": data.modelConfig,
            },
        }
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON format: 'modelConfig' key not found",
        )


class ShutdownInferenceResponse(BaseModel):
    success: bool
    message: str

    model_config = {
        "json_schema_extra": {
            "examples": [{"message": "Services shutdown.", "success": True}]
        }
    }


# Shutdown all currently open processes/subprocesses for text inferencing.
@app.get("/v1/services/shutdown")
async def shutdown_text_inference() -> ShutdownInferenceResponse:
    try:
        print("[homebrew api] Shutting down all services")
        # Reset, kill processes, timers
        killTextInference()
        if hasattr(app, "shutdown_text_timer"):
            app.shutdown_text_timer.cancel()

        return {
            "success": True,
            "message": "Services shutdown successfully.",
        }
    except Exception as e:
        print(f"[homebrew api] Error shutting down services: {e}")
        return {
            "success": False,
            "message": f"Error shutting down services: {e}",
        }


class ServicesApiResponse(BaseModel):
    success: bool
    message: str
    data: List[dict]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "These are api params for accessing services endpoints.",
                    "data": [
                        {
                            "name": "textInference",
                            "port": 8008,
                            "endpoints": [
                                {
                                    "name": "completions",
                                    "urlPath": "/v1/completions",
                                    "method": "POST",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
    }


# Return api info for available services
@app.get("/v1/services/api")
def get_services_api() -> ServicesApiResponse:
    text_inference_api = {
        "name": "textInference",
        "port": app.PORT_TEXT_INFERENCE,
        "endpoints": [
            {
                "name": "copilot",
                "urlPath": "/v1/engines/copilot-codex/completions",
                "method": "POST",
            },
            {
                "name": "completions",
                "urlPath": "/v1/completions",
                "method": "POST",
                "promptTemplate": app.text_model_config["promptTemplate"],
            },
            {"name": "embeddings", "urlPath": "/v1/embeddings", "method": "POST"},
            {
                "name": "chatCompletions",
                "urlPath": "/v1/chat/completions",
                "method": "POST",
            },
            {"name": "models", "urlPath": "/v1/models", "method": "GET"},
        ],
    }

    return {
        "success": True,
        "message": "These are the available service api's",
        "data": [text_inference_api],
    }


# Pre-process docs into a text format specified by user.
@app.post("/v1/embeddings/pre-process")
def pre_process_documents():
    return {"message": "pre_process_documents"}


# Create vector embeddings from the pre-processed documents, then store in database.
@app.post("/v1/embeddings/create")
def create_embeddings():
    return {"message": "create_embeddings"}


# Use Llama Index to run queries on vector database embeddings.
@app.post("/v1/search/similiar")
def search_similiar():
    return {"message": "search_similiar"}


# Methods...


def killTextInference():
    if hasattr(app, "text_inference_process"):
        if app.text_inference_process.poll() != None:
            app.text_inference_process.kill()
            app.text_inference_process = None


def startPingTimer():
    print("[homebrew api] Start ping timer")
    if hasattr(app, "shutdown_text_timer"):
        app.shutdown_text_timer.cancel()
    app.shutdown_text_timer = asyncio.create_task(start_text_shutdown_timer())


async def start_text_shutdown_timer():
    await asyncio.sleep(ping_timeout)
    # Shutdown Subprocess
    killTextInference()


def start_homebrew_server():
    try:
        print("Starting API server...")
        # Start the ASGI server
        uvicorn.run(app, host="0.0.0.0", port=app.PORT_HOMEBREW_API, log_level="info")
        return True
    except:
        print("Failed to start API server")
        return False


async def start_text_inference_server(file_path: str):
    try:
        path = file_path.replace("\\", "/")

        # Command to execute
        serve_llama_cpp = [
            "python",
            "-m",
            "llama_cpp.server",
            "--host",
            "0.0.0.0",
            "--port",
            str(app.PORT_TEXT_INFERENCE),
            "--model",
            path,
            # "--help",
            "--n_ctx",
            "2048",
            # "--n_gpu_layers",
            # "2",
            # "--verbose",
            # "True",
            # "--cache",
            # "True",
            # "--cache_type",
            # "disk",
            # "--seed",
            # "0",
        ]
        # Execute the command
        proc = subprocess.Popen(serve_llama_cpp)
        app.text_inference_process = proc
        startPingTimer()
        print(f"Starting Inference server from: {file_path} with pid: {proc.pid}")
        return True
    except:
        print("Failed to start Inference server")
        return False


if __name__ == "__main__":
    # Determine path to file based on prod or dev
    current_directory = os.getcwd()
    substrings = current_directory.split("\\")
    last_substring = substrings[-1]
    if last_substring == "backends":
        path = "../shared/constants.json"
    else:
        path = "./shared/constants.json"
    # Open and read the JSON constants file
    with open(path, "r") as json_file:
        data = json.load(json_file)
        app.PORT_HOMEBREW_API = data["PORT_HOMEBREW_API"]
        app.PORT_TEXT_INFERENCE = data["PORT_TEXT_INFERENCE"]
    # Starts the homebrew API server
    start_homebrew_server()
