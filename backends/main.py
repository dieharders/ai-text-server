import os
import json
import uvicorn
import subprocess
import httpx
import re
from typing import List, Optional
from fastapi import (
    FastAPI,
    HTTPException,
    BackgroundTasks,
    Request,
    File,
    UploadFile,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from embedding import embedding

MEMORY_PATH = "memories"


@asynccontextmanager
async def lifespan(application: FastAPI):
    print("[homebrew api] Lifespan startup")
    app.requests_client = httpx.AsyncClient()
    # Store some state here if you want...
    # application.state.super_secret = secrets.token_hex(16)

    yield

    print("[homebrew api] Lifespan shutdown")
    killTextInference()


app = FastAPI(title="🍺 HomeBrew API server", version="0.1.0", lifespan=lifespan)


# Configure CORS settings
origins = [
    "http://localhost:3000",  # (optional) for testing client apps
    "https://hoppscotch.io",  # (optional) for testing endpoints
    "http://localhost:8000",  # (required) Homebrew front-end
    "https://brain-dump-dieharders.vercel.app",  # (required) client app origin (preview)
    "https://homebrew-ai-discover.vercel.app",  # (required) client app origin (production)
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
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
async def ping(request: Request):
    success = False

    # Can get state from app lifecycle here
    # request.app.state.super_secret

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
    #         success = True

    # Server exists
    if result:
        if "data" in result:
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
        # Reset, kill processes
        killTextInference()
        delattr(app, "text_model_config")

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
    data = []

    # Only return api configs for servers that are actually running
    if hasattr(app, "text_model_config"):
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
        data.append(text_inference_api)

    return {
        "success": True,
        "message": "These are the currently available service api's",
        "data": data,
    }


class PreProcessRequest(BaseModel):
    name: str
    title: Optional[str]
    description: Optional[str]
    tags: Optional[str]


# Pre-process docs into a text format specified by user.
@app.post("/v1/embeddings/pre-process")
def pre_process_documents(
    form: PreProcessRequest = Depends(), file: UploadFile = File(...)
):
    try:
        # Check supported file types
        filename = file.filename
        tmp_input_path = os.path.join(os.getcwd(), MEMORY_PATH, "tmp")
        tmp_input_file_path = os.path.join(os.getcwd(), MEMORY_PATH, "tmp", filename)
        file_extension = filename.rsplit(".", 1)[1]
        supported_ext = (
            "txt",
            "md",
            "mdx",
            "doc",
            "docx",
            "pdf",
            "rtf",
            "csv",
            "json",
            "xml",
            "xls",
            "orc",
        )
        is_supported = file_extension.lower().endswith(supported_ext)
        if not is_supported:
            raise Exception(f"Unsupported file format {file_extension}")
        if not form.name:
            raise Exception("You must supply a collection name.")
    except (Exception, ValueError, TypeError, KeyError) as error:
        return {
            "success": False,
            "message": f"There was an internal server error uploading the file:\n{error}",
        }
    else:
        # Read the form inputs
        name = form.name  # name of new collection
        title = form.title  # title of document
        description = form.description
        tags = form.tags
        rootFileName = os.path.splitext(filename)[0]
        new_file_path = os.getcwd()  # path to app storage
        new_filename = f"{rootFileName}.md"
        # Create new output folder
        new_output_path = os.path.join(new_file_path, MEMORY_PATH, "parsed")
        if not os.path.exists(new_output_path):
            os.makedirs(new_output_path)
        target_output_path = os.path.join(new_output_path, new_filename)
        # Format tags
        comma_sep_tags = re.sub("\s+", ", ", tags.strip())
        # Read the file in chunks of 1mb
        if not os.path.exists(tmp_input_path):
            os.makedirs(tmp_input_path)
        with open(tmp_input_file_path, "wb") as f:
            while contents := file.file.read(1024 * 1024):
                f.write(contents)
        file.file.close()
        # Finalize uploaded file
        # @TODO If the file is not text, then create a text description of the contents (via VisionAi, Human, OCR)
        # Copy text contents of original file into a new file, parsed for embedding
        with open(target_output_path, "w") as output_file, open(
            tmp_input_file_path, "r"
        ) as input_file:
            # Check if header exists
            first_line = input_file.readline()
            if first_line != "---\n":
                # Add a header to file
                output_file.write("---\n")
                output_file.write(f"collection: {name}\n")
                output_file.write(f"title: {title}\n")
                output_file.write(f"description: {description}\n")
                output_file.write(f"tags: {comma_sep_tags}\n")
                output_file.write("---\n\n")
            input_file.seek(0)  # set back to start of file
            # Copy each line from source file
            output_file.writelines(line for line in input_file)
            # @TODO Copied text should be parsed and edited to include markdown syntax to describe important bits (headings, attribution, links)
            # @TODO Copied contents may include things like images/graphs that need special parsing to generate an effective text description
            # parsed_text = markdown.parse(copied_text)
    finally:
        # Delete uploaded file
        if os.path.exists(tmp_input_file_path):
            os.remove(tmp_input_file_path)
            print(f"Removed temp file upload.")
        else:
            print("Failed to delete temp file upload. The file does not exist.")

    return {
        "success": True,
        "message": f"Successfully processed {filename}",
        "data": {
            "filename": new_filename,
            "path_to_file": target_output_path,
            "base_path_to_file": new_output_path,
        },
    }


# Create a memory for Ai
@app.post("/v1/memory/create")
async def create_memory(
    form: PreProcessRequest = Depends(),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    try:
        if not form.name:
            raise Exception("You must supply a collection name.")
        # Parse inputs
        result = pre_process_documents(form, file)
        data = result["data"]
        # Create embeddings
        print("Start embedding process...")
        collection_name = form.name
        background_tasks.add_task(
            embedding.create_embedding,
            data["path_to_file"],
            data["base_path_to_file"],
            collection_name,
        )
    except Exception as e:
        msg = f"Failed to create a new memory: {e}"
        print(msg)
        return {
            "success": False,
            "message": msg,
        }
    else:
        msg = "A new memory has been added to the queue. It will be available for use shortly."
        print(msg)
        return {
            "success": True,
            "message": msg,
        }


# Create vector embeddings from the pre-processed documents, then store in database.
@app.post("/v1/embeddings/create")
def create_embeddings(path_to_file: str, base_path: str, collection_name: str):
    try:
        result = embedding.create_embedding(path_to_file, base_path, collection_name)
    except Exception as e:
        msg = f"Failed to create embeddings:\n{e}"
        print(msg)
        return {
            "success": False,
            "message": msg,
        }

    return {
        "success": True,
        "message": "Successfully created embeddings",
        "data": {"result": result},
    }


# Use Llama Index to run queries on vector database embeddings.
@app.post("/v1/search/similiar")
def search_similiar():
    # index = embedding.load_embedding(llm, storage_directory)
    # response = embedding.query_embedding("What does this mean?", index, service_context)
    # answer = response.response
    return {"success": True, "message": "search_similiar"}


# Methods...


def killTextInference():
    if hasattr(app, "text_inference_process"):
        if app.text_inference_process.poll() != None:
            app.text_inference_process.kill()
            app.text_inference_process = None


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
