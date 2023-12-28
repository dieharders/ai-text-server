import os
import glob
import json
import uvicorn
import httpx
import shutil
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
from contextlib import asynccontextmanager
from inference import text_llama_index
from embedding import embedding
from server import common, classes
from routes import router as endpoint_router

VECTOR_DB_FOLDER = "chromadb"
MEMORY_FOLDER = "memories"
PARSED_FOLDER = "parsed"
TMP_FOLDER = "tmp"
APP_SETTINGS_FOLDER = "settings"
VECTOR_STORAGE_PATH = os.path.join(os.getcwd(), VECTOR_DB_FOLDER)
MEMORY_PATH = os.path.join(os.getcwd(), MEMORY_FOLDER)
PARSED_DOCUMENT_PATH = os.path.join(MEMORY_PATH, PARSED_FOLDER)
TMP_DOCUMENT_PATH = os.path.join(MEMORY_PATH, TMP_FOLDER)
APP_SETTINGS_PATH = os.path.join(os.getcwd(), APP_SETTINGS_FOLDER)


@asynccontextmanager
async def lifespan(application: FastAPI):
    print("[homebrew api] Lifespan startup")
    # https://www.python-httpx.org/quickstart/
    app.requests_client = httpx.Client()
    # Store some state here if you want...
    app.text_inference_process = None
    application.state.PORT_HOMEBREW_API = app.PORT_HOMEBREW_API
    application.state.storage_directory = VECTOR_STORAGE_PATH
    application.state.db_client = None
    application.state.llm = None  # Set each time user loads a model
    application.state.path_to_model = ""  # Set each time user loads a model
    application.state.text_model_config = {}
    app.state.settings = {}

    yield

    print("[homebrew api] Lifespan shutdown")
    common.kill_text_inference(app)


app = FastAPI(title="🍺 HomeBrew API server", version="0.2.0", lifespan=lifespan)


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
        print(f"[homebrew api] Error pinging server: {e}")
        return {"success": False, "message": ""}


# Tell client we are ready to accept requests
@app.get("/v1/connect")
def connect() -> classes.ConnectResponse:
    # Read the version from package.json file
    try:
        file_path = os.path.join(os.getcwd(), "package.json")
        with open(file_path, "r") as file:
            loaded_data = json.load(file)
            version = loaded_data["version"]
    except FileNotFoundError:
        # If the file doesn't exist
        version = "0"

    return {
        "success": True,
        "message": f"Connected to api server on port {app.PORT_HOMEBREW_API}. Refer to 'http://localhost:{app.PORT_HOMEBREW_API}/docs' for api docs.",
        "data": {
            "docs": f"http://localhost:{app.PORT_HOMEBREW_API}/docs",
            "version": version,
        },
    }


@app.get("/v1/text/models")
def get_text_model():
    # llm = app.state.llm
    model_config = app.state.text_model_config

    return {
        "success": True,
        "message": "",
        "data": {
            "id": model_config["id"],
            "name": model_config["name"],
            "path": model_config["savePath"],
            "size": model_config["size"],
            "type": model_config["type"],
            "ownedBy": model_config["provider"],
            "permissions": model_config["licenses"],
            "promptTemplate": model_config["promptTemplate"],
        },
    }


@app.post("/v1/text/load")
def load_text_inference(
    data: classes.LoadInferenceRequest,
) -> classes.LoadInferenceResponse:
    try:
        # Store the current model's configuration for later reference
        app.state.text_model_config = data.textModelConfig
        model_id = data.modelId
        app.state.path_to_model = data.pathToModel
        # Save model init settings to disk
        save_settings(
            {
                "init": {
                    "n_gpu_layers": data.n_gpu_layers,
                    "use_mmap": data.use_mmap,
                    "use_mlock": data.use_mlock,
                    "f16_kv": data.f16_kv,
                    "seed": data.seed,
                    "n_ctx": data.n_ctx,
                    "n_batch": data.n_batch,
                    "n_threads": data.n_threads,
                    "offload_kqv": data.offload_kqv,
                    "verbose": data.verbose,
                    "offload_kqv": data.offload_kqv,
                },
            }
        )
        print(f"[homebrew api] Path to model loaded: {data.pathToModel}")
        # Load the specified Ai model
        if app.state.llm == None:
            model_settings = app.state.settings["init"]
            generate_settings = {}
            app.state.llm = text_llama_index.load_text_model(
                app.state.path_to_model, model_settings, generate_settings
            )

        return {"message": f"AI model [{model_id}] loaded.", "success": True}
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid JSON format: missing key")


# Use Llama Index to run queries on vector database embeddings or run normal chat inference.
@app.post("/v1/text/inference")
async def text_inference(payload: classes.InferenceRequest):
    try:
        prompt = payload.prompt
        collection_names = payload.collectionNames
        mode = payload.mode
        options = dict(
            stream=payload.stream,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
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
            raise Exception("No path to model provided.")
        if not app.state.text_model_config:
            raise Exception("No model config exists.")

        # Call LLM
        if len(collection_names):
            print(
                f"[homebrew api] text_inference: {prompt} on: {collection_names} in mode {mode}"
            )

            return EventSourceResponse(
                text_llama_index.query_memory(
                    prompt,
                    collection_names,
                    app,
                    embedding.get_vectordb_client(app),
                    options,
                ),
            )
        else:
            return EventSourceResponse(
                text_llama_index.text_completion(prompt, app, options)
            )
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid JSON format: missing key")


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
    form: classes.AddDocumentRequest = Depends(),
    file: UploadFile = File(None),  # File(...) means required
    background_tasks: BackgroundTasks = None,  # This prop is auto populated by FastAPI
) -> classes.AddDocumentResponse:
    try:
        document_name = form.documentName
        collection_name = form.collectionName
        description = form.description
        url_path = form.urlPath
        tags = common.parse_valid_tags(form.tags)
        tmp_input_file_path = ""

        if file == None and url_path == "":
            raise Exception("You must supply a file upload or url.")
        if not document_name or not collection_name:
            raise Exception("You must supply a collection and memory name.")
        if tags == None:
            raise Exception("Invalid value for 'tags' input.")
        if not common.check_valid_id(document_name):
            raise Exception(
                "Invalid memory name. No '--', uppercase, spaces or special chars allowed."
            )
        if not app.state.path_to_model:
            raise Exception("No model path defined.")

        # Save temp files to disk first. The filename doesnt matter much.
        tmp_folder = TMP_DOCUMENT_PATH
        filename = embedding.create_parsed_filename(collection_name, document_name)
        tmp_input_file_path = os.path.join(tmp_folder, filename)
        if url_path:
            print(
                f"[homebrew api] Downloading file from url {url_path} to {tmp_input_file_path}"
            )
            if not os.path.exists(tmp_folder):
                os.makedirs(tmp_folder)
            # Download the file and save to disk
            await common.get_file_from_url(url_path, tmp_input_file_path, app)
        elif file:
            print("[homebrew api] Saving uploaded file to disk...")
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
        print("[homebrew api] Start embedding...")
        if app.state.llm == None:
            raise Exception("No Ai loaded.")
        db_client = embedding.get_vectordb_client(app)
        embed_form = {
            "collection_name": collection_name,
            "document_name": document_name,
            "document_id": processed_file["document_id"],
            "description": description,
            "tags": tags,
            "is_update": False,
        }
        background_tasks.add_task(
            embedding.create_embedding,
            processed_file,
            app.state.storage_directory,
            embed_form,
            app.state.llm,
            db_client,
        )
    except (Exception, KeyError) as e:
        # Error
        msg = f"Failed to create a new memory: {e}"
        print(f"[homebrew api] {msg}")
        return {
            "success": False,
            "message": msg,
        }
    else:
        msg = "A new memory has been added to the queue. It will be available for use shortly."
        print(f"[homebrew api] {msg}")
        return {
            "success": True,
            "message": msg,
        }
    finally:
        # Delete uploaded tmp file
        if os.path.exists(tmp_input_file_path):
            os.remove(tmp_input_file_path)
            print(f"[homebrew api] Removed temp file.")


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
        print(f"[homebrew api] Error: {e}")
        return {
            "success": False,
            "message": e,
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
        print(f"[homebrew api] Error: {e}")
        return {
            "success": False,
            "message": e,
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
            db=embedding.get_vectordb_client(app),
            include=include,
        )

        num_documents = len(documents)

        return {
            "success": True,
            "message": f"Returned {num_documents} document(s)",
            "data": documents,
        }
    except Exception as e:
        print(f"[homebrew api] Error: {e}")
        return {
            "success": False,
            "message": e,
        }


# Open an OS file exporer on host machine
@app.get("/v1/memory/fileExplore")
def explore_source_file(
    params: classes.FileExploreRequest = Depends(),
) -> classes.FileExploreResponse:
    filePath = params.filePath

    if not filePath:
        return {
            "success": False,
            "message": "No file path given",
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
    args: classes.UpdateDocumentRequest,
    background_tasks: BackgroundTasks = None,  # This prop is auto populated by FastAPI
) -> classes.UpdateDocumentResponse:
    try:
        collection_name = args.collectionName
        document_id = args.documentId
        document_name = args.documentName
        metadata = args.metadata
        url_path = args.urlPath
        file_path = args.filePath
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
        db = embedding.get_vectordb_client(app)
        documents = embedding.get_document(
            collection_name=collection_name,
            document_ids=[document_id],
            db=db,
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
            print(f"[homebrew api] Downloading file to {tmp_file_path} ...")
            await common.get_file_from_url(url_path, tmp_file_path, app)
        elif file_path:
            # Copy file from provided location to /tmp dir, only if paths differ
            print(f"[homebrew api] Loading local file from disk {file_path} ...")
            if file_path != tmp_file_path:
                if not os.path.exists(tmp_folder):
                    os.makedirs(tmp_folder)
                shutil.copy(file_path, tmp_file_path)
            print("[homebrew api] File to be copied already in /tmp dir")
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
            if app.state.llm == None:
                raise Exception("No Ai loaded.")
            form = {
                "collection_name": collection_name,
                "document_name": document_name,
                "document_id": document_id,
                "description": description,
                "tags": updated_tags,
                "is_update": True,
            }
            background_tasks.add_task(
                embedding.create_embedding,
                processed_file,
                app.state.storage_directory,
                form,
                app.state.llm,
                db,
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
        print(f"[homebrew api] Error: {e}")
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
            db=db,
            include=["metadatas"],
        )
        if app.state.llm == None:
            raise Exception("No Ai loaded.")
        # Delete all files and references associated with embedded docs
        for document in documents:
            document_metadata = document["metadata"]
            source_file_path = document_metadata["filePath"]
            document_id = document_metadata["id"]
            # Remove file from disk
            print(f"[homebrew api] Remove file {document_id} from {source_file_path}")
            if os.path.exists(source_file_path):
                os.remove(source_file_path)
            # Remove source reference from collection array
            sources.remove(document_id)
            # Update collection
            sources_json = json.dumps(sources)
            collection.metadata["sources"] = sources_json
            collection.modify(metadata=collection.metadata)
            # Delete embeddings from llama-index @TODO Verify this works
            index = embedding.load_embedding(app.state.llm, db, collection_id)
            index.delete(document_id)
        # Delete the embeddings from collection
        collection.delete(ids=document_ids)

        return {
            "success": True,
            "message": f"Removed {num_documents} document(s): {document_ids}",
        }
    except Exception as e:
        print(f"[homebrew api] Error: {e}")
        return {
            "success": False,
            "message": e,
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
            db=embedding.get_vectordb_client(app),
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
        print(f"[homebrew api] Error: {e}")
        return {
            "success": False,
            "message": e,
        }


# Completely wipe database
@app.get("/v1/memory/wipe")
def wipe_all_memories() -> classes.WipeMemoriesResponse:
    try:
        db = embedding.get_vectordb_client(app)
        # Delete all db values
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
        # Remove persisted vector storage folder
        if os.path.exists(VECTOR_STORAGE_PATH):
            folders = glob.glob(f"{VECTOR_STORAGE_PATH}/*")
            for dir in folders:
                if not "chroma." in dir:
                    files = glob.glob(f"{dir}/*")
                    for f in files:
                        os.remove(f)  # del files
            os.rmdir(dir)  # del folder

        return {
            "success": True,
            "message": "Successfully wiped all memories from Ai",
        }
    except Exception as e:
        print(f"[homebrew api] Error: {e}")
        return {
            "success": False,
            "message": e,
        }


# Get all app settings
@app.get("/v1/persist/settings")
def get_settings():
    # Paths
    file_name = "app.json"
    file_path = os.path.join(APP_SETTINGS_PATH, file_name)

    # Check if folder exists
    if not os.path.exists(APP_SETTINGS_PATH):
        return {
            "success": False,
            "message": f"Failed to return settings. Folder does not exist.",
            "data": None,
        }

    # Try to open the file (if it exists)
    loaded_data = {}
    try:
        with open(file_path, "r") as file:
            loaded_data = json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist, fail
        return {
            "success": False,
            "message": f"Failed to return settings. File does not exist.",
            "data": None,
        }

    return {
        "success": True,
        "message": f"Returned app settings",
        "data": loaded_data,
    }


# Save app settings
@app.post("/v1/persist/settings")
def save_settings(data: dict) -> classes.GenericEmptyResponse:
    # Paths
    file_name = "app.json"
    file_path = os.path.join(APP_SETTINGS_PATH, file_name)

    # Create folder/file
    if not os.path.exists(APP_SETTINGS_PATH):
        os.makedirs(APP_SETTINGS_PATH)

    # Try to open the file (if it exists)
    try:
        with open(file_path, "r") as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist yet, create an empty dictionary
        existing_data = {}

    # Update the existing data with the new variables
    for key, val in data.items():
        existing_data[key] = val

    # Save the updated data to the file, this will overwrite all values in the key's dict.
    with open(file_path, "w") as file:
        json.dump(existing_data, file, indent=2)

    # Save to memory
    app.state.settings = existing_data

    return {
        "success": True,
        "message": f"Saved settings to {file_path}",
        "data": None,
    }


# Methods...


def start_homebrew_server():
    try:
        print("[homebrew api] Starting API server...")
        # Start the ASGI server
        uvicorn.run(app, host="0.0.0.0", port=app.PORT_HOMEBREW_API, log_level="info")
        return True
    except:
        print("[homebrew api] Failed to start API server")
        return False


if __name__ == "__main__":
    # Determine path to file based on prod or dev
    current_directory = os.getcwd()
    substrings = current_directory.split("\\")
    last_substring = substrings[-1]
    # This path detection is b/c of Node.js in dev vs prod mode
    if last_substring == "backends":
        path = "../shared/constants.json"
    else:
        path = "./shared/constants.json"
    # Open and read the JSON constants file
    with open(path, "r") as json_file:
        data = json.load(json_file)
        app.PORT_HOMEBREW_API = data["PORT_HOMEBREW_API"]
    # Starts the homebrew API server
    start_homebrew_server()
