import os
import json
import uvicorn
import subprocess
import httpx
import re
from typing import List, Dict, Any, Union, Optional
from fastapi import (
    FastAPI,
    HTTPException,
    BackgroundTasks,
    File,
    UploadFile,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from inference import text_llm
from embedding import embedding

MEMORY_PATH = "memories"
VECTOR_DB_PATH = "chromadb"


@asynccontextmanager
async def lifespan(application: FastAPI):
    print("[homebrew api] Lifespan startup")
    app.requests_client = httpx.AsyncClient()
    # Store some state here if you want...
    application.state.storage_directory = os.path.join(os.getcwd(), VECTOR_DB_PATH)
    application.state.db_client = None
    application.state.llm = None  # Set each time user loads a model
    application.state.path_to_model = ""  # Set each time user loads a model

    yield

    print("[homebrew api] Lifespan shutdown")
    kill_text_inference()


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


# Keep server/database alive
@app.get("/v1/ping")
def ping():
    try:
        db = get_vectordb_client()
        db.heartbeat()
        return {"success": True, "message": "pong"}
    except Exception as e:
        print(f"[homebrew api] Error pinging server: {e}")
        return {"success": False, "message": ""}


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
    pathToModel: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "modelId": "llama-2-13b-chat-ggml",
                    "pathToModel": "C:\\homebrewai-app\\models\\llama-2-13b.GGUF",
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
        app.state.path_to_model = data.pathToModel
        print(f"[homebrew api] Path to model loaded: {data.pathToModel}")
        # Logic to load the specified ai model here...
        return {"message": f"AI model [{model_id}] loaded.", "success": True}
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid JSON format: missing key")


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
        kill_text_inference()
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

    # Return services that are ready now
    memory_api = {
        "name": "memory",
        "port": app.PORT_HOMEBREW_API,
        "endpoints": [
            {
                "name": "create",
                "urlPath": "/v1/memory/create",
                "method": "POST",
            },
            {
                "name": "addCollection",
                "urlPath": "/v1/memory/addCollection",
                "method": "GET",
            },
            {
                "name": "getAllCollections",
                "urlPath": "/v1/memory/getAllCollections",
                "method": "GET",
            },
            {
                "name": "getCollection",
                "urlPath": "/v1/memory/getCollection",
                "method": "POST",
            },
            {
                "name": "getDocument",
                "urlPath": "/v1/memory/getDocument",
                "method": "POST",
            },
            {
                "name": "update",
                "urlPath": "/v1/memory/update",
                "method": "POST",
            },
            {
                "name": "deleteDocuments",
                "urlPath": "/v1/memory/deleteDocuments",
                "method": "GET",
            },
            {
                "name": "deleteCollection",
                "urlPath": "/v1/memory/deleteCollection",
                "method": "GET",
            },
            {
                "name": "wipe",
                "urlPath": "/v1/memory/wipe",
                "method": "GET",
            },
        ],
    }
    data.append(memory_api)

    return {
        "success": True,
        "message": "These are the currently available service api's",
        "data": data,
    }


class PreProcessRequest(BaseModel):
    name: str
    collection_name: str
    description: Optional[str] = ""
    tags: Optional[str] = ""


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
        if not form.name or not form.collection_name:
            raise Exception("You must supply a collection and memory name.")
    except (Exception, ValueError, TypeError, KeyError) as error:
        return {
            "success": False,
            "message": f"There was an internal server error uploading the file:\n{error}",
        }
    else:
        # Read the form inputs
        name = form.name  # name of new memory (document)
        collection_name = form.collection_name
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
        with open(target_output_path, "w", encoding="utf-8") as output_file, open(
            tmp_input_file_path, "r"
        ) as input_file:
            # Check if header exists
            first_line = input_file.readline()
            if first_line != "---\n":
                # Add a header to file
                output_file.write("---\n")
                output_file.write(f"collection: {collection_name}\n")
                output_file.write(f"document: {name}\n")
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
            print(f"[homebrew api] Removed temp file upload.")
        else:
            print(
                "[homebrew api] Failed to delete temp file upload. The file does not exist."
            )

    return {
        "success": True,
        "message": f"Successfully processed {filename}",
        "data": {
            "filename": new_filename,
            "path_to_file": target_output_path,
        },
    }


class AddCollectionRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    tags: Optional[str] = List[None]


@app.get("/v1/memory/addCollection")
def add_collection(form: AddCollectionRequest = Depends()):
    try:
        if not form.name:
            raise Exception("You must supply a collection name.")
        # Create payload. ChromaDB only accepts strings, numbers, bools.
        metadata = {
            "tags": form.tags,
            "description": form.description,
            "sources": json.dumps([]),
            "filePaths": json.dumps([]),
            "processing": json.dumps([]),
        }
        # Apply input values to collection metadata
        db_client = get_vectordb_client()
        db_client.create_collection(
            name=form.name,
            metadata=metadata,
        )
        return {
            "success": True,
            "message": f"Successfully created new collection [{form.name}]",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create new collection [{form.name}]: {e}",
        }


# Create a memory for Ai.
# This is a multi-step process involving several endpoints.
# It will first process the file, then embed its data into vector space and
# finally add it as a document to specified collection.
@app.post("/v1/memory/create")
async def create_memory(
    form: PreProcessRequest = Depends(),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,  # This prop is auto populated by FastAPI
):
    try:
        if not form.name or not form.collection_name:
            # Collection name must be 3 and 63 characters.
            raise Exception("You must supply a collection and memory name")
        if not app.state.path_to_model:
            raise Exception("No model path defined.")
        # Parse/Process input files
        result = pre_process_documents(form, file)
        data = result["data"]
        # Create embeddings
        print("[homebrew api] Start embedding process...")
        if app.state.llm == None:
            app.state.llm = text_llm.load_text_model(app.state.path_to_model)
        db_client = get_vectordb_client()
        background_tasks.add_task(
            embedding.create_embedding,
            data["path_to_file"],
            app.state.storage_directory,
            form,
            app.state.llm,
            db_client,
        )
    except Exception as e:
        msg = f"[homebrew api] Failed to create a new memory: {e}"
        print(msg)
        return {
            "success": False,
            "message": msg,
        }
    else:
        msg = "[homebrew api] A new memory has been added to the queue. It will be available for use shortly."
        print(msg)
        return {
            "success": True,
            "message": msg,
        }


@app.get("/v1/memory/getAllCollections")
def get_all_collections():
    try:
        db = get_vectordb_client()
        collections = db.list_collections()
        return {
            "success": True,
            "message": f"Returned {len(collections)} collection(s)",
            "data": collections,
        }
    except Exception as e:
        print(f"[homebrew api] Error: {e}")
        return {
            "success": False,
            "message": f"Error {e}",
        }


class GetCollectionRequest(BaseModel):
    id: str
    include: Optional[List[str]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "examples",
                    "include": ["embeddings", "documents"],
                }
            ]
        }
    }


# Return a collection by id and all its documents
@app.post("/v1/memory/getCollection")
def get_collection(props: GetCollectionRequest):
    try:
        db = get_vectordb_client()
        id = props.id
        include = props.include
        collection = db.get_collection(id)
        numItems = collection.count()
        if include == None:
            documents = collection.get()
        else:
            documents = collection.get(include=include)
        return {
            "success": True,
            "message": f"Returned {len(documents)} document(s) in collection [{id}]",
            "data": {
                "collection": collection,
                "documents": documents,
                "numItems": numItems,
            },
        }
    except Exception as e:
        print(f"[homebrew api] Error: {e}")
        return {
            "success": False,
            "message": f"Error: {e}",
        }


class GetDocumentRequest(BaseModel):
    collection_id: str
    document_ids: List[str]
    include: Optional[List[str]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "collection_id": "examples",
                    "document_ids": ["science"],
                    "include": ["embeddings", "documents"],
                }
            ]
        }
    }


# Get one or more documents by id
# @TODO This is actually returning the chunks of a document. Can we return the "source" document instead?
@app.post("/v1/memory/getDocument")
def get_document(params: GetDocumentRequest):
    try:
        collection_id = params.collection_id
        document_ids = params.document_ids
        include = params.include
        db = get_vectordb_client()
        collection = db.get_collection(collection_id)
        if include == None:
            documents = collection.get(ids=document_ids)
        else:
            documents = collection.get(ids=document_ids, include=include)
        return {
            "success": True,
            "message": f"Returned {len(documents)} document(s)",
            "data": documents,
        }
    except Exception as e:
        print(f"[homebrew api] Error: {e}")
        return {
            "success": False,
            "message": f"Error {e}",
        }


class UpdateMemoryRequest(BaseModel):
    collection_id: Optional[str]
    doc_ids: Optional[List[str]] = None
    metadata: Dict[str, Union[str, int, bool, Dict[str, Any], List[str]]] = None
    documents: List[str] = None


# Update existing collection or document(s)
@app.post("/v1/memory/update")
def update_memory(params: UpdateMemoryRequest):
    try:
        collection_id = params.collection_id
        doc_ids = params.doc_ids
        metadata = params.metadata
        documents = params.documents
        db = get_vectordb_client()
        collection = db.get_collection(collection_id)
        if documents:
            collection.update(
                name=collection_id,
                documents=documents,
                metadatas=metadata,
                ids=doc_ids,
            )
        else:
            collection.modify(name=collection_id, metadata=metadata)
        return {
            "success": True,
            "message": "Updated items",
        }
    except Exception as e:
        print(f"[homebrew api] Error: {e}")
        return {
            "success": False,
            "message": f"Error {e}",
        }


class DeleteDocumentsRequest(BaseModel):
    collection_id: str
    doc_ids: List[str]


# Delete a document by id
@app.get("/v1/memory/deleteDocuments")
def delete_documents(params: DeleteDocumentsRequest):
    try:
        collection_id = params.collection_id
        doc_ids = params.doc_ids
        db = get_vectordb_client()
        collection = db.get_collection(collection_id)
        collection.delete(ids=doc_ids)
        return {
            "success": True,
            "message": f"Removed {len(doc_ids)} document(s)",
        }
    except Exception as e:
        print(f"[homebrew api] Error: {e}")
        return {
            "success": False,
            "message": f"Error {e}",
        }


class DeleteCollectionRequest(BaseModel):
    collection_id: str


# Delete a collection by id
@app.get("/v1/memory/deleteCollection")
def delete_collection(params: DeleteCollectionRequest):
    try:
        collection_id = params.collection_id
        db = get_vectordb_client()
        db.delete_collection(name=collection_id)
        return {
            "success": True,
            "message": f"Removed collection [{collection_id}]",
        }
    except Exception as e:
        print(f"[homebrew api] Error: {e}")
        return {
            "success": False,
            "message": f"Error {e}",
        }


# Completely wipe database
@app.get("/v1/memory/wipe")
def wipe_all_memories():
    try:
        db = get_vectordb_client()
        db.reset()
        return {
            "success": True,
            "message": f"Successfully wiped all memories from Ai",
        }
    except Exception as e:
        print(f"[homebrew api] Error: {e}")
        return {
            "success": False,
            "message": f"Error {e}",
        }


class SearchSimilarRequest(BaseModel):
    query: str
    collection_name: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "Why does mass conservation break down?",
                    "collection_name": "examples",
                }
            ]
        }
    }


# Use Llama Index to run queries on vector database embeddings.
@app.post("/v1/search/similar")
def search_similar(payload: SearchSimilarRequest):
    try:
        query = payload.query
        collection_name = payload.collection_name
        print(f"Search: {query} in: {collection_name}")

        if not app.state.path_to_model:
            raise Exception("No path to model provided.")
        if app.state.llm == None:
            app.state.llm = text_llm.load_text_model(app.state.path_to_model)
        db_client = get_vectordb_client()
        index = embedding.load_embedding(
            app.state.llm,
            db_client,
            collection_name,
        )
        response = embedding.query_embedding(query, index)
        answer = response.response
        return {"success": True, "message": "search_similar", "data": answer}
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid JSON format: missing key")


# Methods...


def get_vectordb_client():
    if app.state.db_client == None:
        app.state.db_client = embedding.create_db_client(app.state.storage_directory)
    return app.state.db_client


def kill_text_inference():
    if hasattr(app, "text_inference_process"):
        if app.text_inference_process.poll() != None:
            app.text_inference_process.kill()
            app.text_inference_process = None


def start_homebrew_server():
    try:
        print("[homebrew api] Starting API server...")
        # Start the ASGI server
        uvicorn.run(app, host="0.0.0.0", port=app.PORT_HOMEBREW_API, log_level="info")
        return True
    except:
        print("[homebrew api] Failed to start API server")
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
        print(
            f"[homebrew api] Starting Inference server from: {file_path} with pid: {proc.pid}"
        )
        return True
    except:
        print("[homebrew api] Failed to start Inference server")
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
