import os
import json
from datetime import datetime, timezone
from typing import Any, List
from server import classes, common
from fastapi import APIRouter, Request, Depends, File, BackgroundTasks, UploadFile
from embeddings import storage, file_parsers, main

router = APIRouter()

###############
### Methods ###
###############


# Given source(s), delete all associated document chunks, metadata and files
def delete_sources(
    app: Any, collection_name: str, sources: List[classes.SourceMetadata]
):
    db = storage.get_vector_db_client(app)
    collection = db.get_collection(name=collection_name)
    vector_index = main.load_embedding(app, collection_name)
    # Delete each source chunk and parsed file
    for source in sources:
        chunk_ids = source.get("chunkIds")
        # Delete all chunks
        storage.delete_chunks(
            collection=collection,
            vector_index=vector_index,
            chunk_ids=chunk_ids,
        )
        # Delete associated files
        storage.delete_source_files(source)
    # Update collection metadata.sources to remove this source
    storage.update_collection_sources(
        collection=collection,
        sources=sources,
        mode="delete",
    )


async def modify_document(
    app: Any,
    form: classes.EmbedDocumentRequest,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    is_update: bool = False,
):
    document_name = form.documentName
    prev_document_id = form.documentId
    source_name = form.documentName
    collection_name = form.collectionName
    description = form.description
    tags = common.parse_valid_tags(form.tags)
    url_path = form.urlPath
    local_file_path = form.filePath
    text_input = form.textInput
    chunk_size = form.chunkSize
    chunk_overlap = form.chunkOverlap
    chunk_strategy = form.chunkStrategy
    parsing_method = form.parsingMethod
    new_document_id = file_parsers.create_parsed_id(collection_name=collection_name)
    if is_update:
        source_id = prev_document_id
    else:
        source_id = new_document_id
    form_data = {
        "collection_name": collection_name,
        "document_name": document_name,
        "document_id": source_id,
        "description": description,
        "tags": tags,
        "embedder": app.state.embed_model,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "chunk_strategy": chunk_strategy,
        "parsing_method": parsing_method,
    }
    # Verify input values
    if (
        file == None  # file from client
        and url_path == ""  # file on web
        and text_input == ""  # text input from client
        and local_file_path == ""  # file on server disk
    ):
        raise Exception("Please supply a file upload, file path, url or text.")
    if not collection_name or collection_name == "undefined" or not source_name:
        raise Exception("Please supply a collection name and/or memory name.")
    if is_update and not prev_document_id:
        raise Exception("Please supply a document id.")
    if not document_name:
        raise Exception("Please supply a document name.")
    if not source_id:
        raise Exception("Server error, id misconfigured.")
    if not common.check_valid_id(source_name):
        raise Exception(
            "Invalid memory name. No '--', uppercase, spaces or special chars allowed."
        )
    if tags == None:
        raise Exception("Invalid value for 'tags' input.")
    # If updating, Remove specified source(s) from database
    if is_update:
        collection = storage.get_collection(app, name=collection_name)
        sources_to_delete = storage.get_sources_from_ids(
            collection=collection, source_ids=[prev_document_id]
        )
        delete_sources(
            app=app, collection_name=collection_name, sources=sources_to_delete
        )
    # Write uploaded file to disk temporarily
    input_file = await file_parsers.copy_file_to_disk(
        app=app,
        url_path=url_path,
        file_path=local_file_path,
        text_input=text_input,
        file=file,
        id=source_id,
    )
    path_to_parsed_file = input_file.get("path_to_file")
    # Read in files and create index nodes
    nodes = await main.create_index_nodes(
        app=app,
        input_file=input_file,
        form=form_data,
    )
    # Create embeddings
    # @TODO Note that you must NOT perform CPU intensive computations in the background_tasks of the app,
    # because it runs in the same async event loop that serves the requests and it will stall your app.
    # Instead submit them to a thread pool or a process pool.
    background_tasks.add_task(
        main.create_new_embedding,
        nodes=nodes,
        form=form_data,
        app=app,
    )
    return path_to_parsed_file


@router.get("/v1/memory/addCollection")
def create_memory_collection(
    request: Request,
    form: classes.AddCollectionRequest = Depends(),
) -> classes.AddCollectionResponse:
    app = request.app

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
            "icon": form.icon or "",
            "createdAt": datetime.now(timezone.utc).strftime("%B %d %Y - %H:%M:%S"),
            "tags": parsed_tags,
            "description": form.description,
            "sources": json.dumps([]),
        }
        db_client = storage.get_vector_db_client(app)
        db_client.create_collection(
            name=collection_name,
            metadata=metadata,
        )
        msg = f'Successfully created new collection "{collection_name}"'
        print(f"{common.PRNT_API} {msg}")
        return {
            "success": True,
            "message": msg,
        }
    except Exception as e:
        msg = f'Failed to create new collection "{collection_name}": {e}'
        print(f"{common.PRNT_API} {msg}")
        return {
            "success": False,
            "message": msg,
        }


##############
### Routes ###
##############


# Create a memory for Ai.
# This is a multi-step process involving several endpoints.
# It will first process the file, then embed its data into vector space and
# finally add it as a document to specified collection.
@router.post("/addDocument")
async def create_memory(
    request: Request,
    form: classes.EmbedDocumentRequest = Depends(),
    file: UploadFile = File(None),  # File(...) means required
    background_tasks: BackgroundTasks = None,  # This prop is auto populated by FastAPI
) -> classes.AddDocumentResponse:
    tmp_input_file_path = ""
    app = request.app

    try:
        tmp_input_file_path = await modify_document(
            app=app,
            form=form,
            file=file,
            background_tasks=background_tasks,
            is_update=False,
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


# Re-process and re-embed document
@router.post("/updateDocument")
async def update_memory(
    request: Request,
    form: classes.EmbedDocumentRequest = Depends(),
    file: UploadFile = File(None),  # File(...) means required
    background_tasks: BackgroundTasks = None,  # This prop is auto populated by FastAPI
) -> classes.AddDocumentResponse:
    tmp_input_file_path = ""
    app = request.app

    try:
        tmp_input_file_path = await modify_document(
            app=app,
            form=form,
            file=file,
            background_tasks=background_tasks,
            is_update=True,
        )
    except (Exception, KeyError) as e:
        # Error
        msg = f"Failed to update memory: {e}"
        print(f"{common.PRNT_API} {msg}", flush=True)
        return {
            "success": False,
            "message": msg,
        }
    else:
        msg = "A memory has been added to the update queue. It will be available for use shortly."
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


@router.get("/getAllCollections")
def get_all_collections(
    request: Request,
) -> classes.GetAllCollectionsResponse:
    app = request.app

    try:
        collections = storage.get_all_collections(app=app)

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
@router.post("/getCollection")
def get_collection(
    request: Request,
    props: classes.GetCollectionRequest,
) -> classes.GetCollectionResponse:
    app = request.app

    try:
        name = props.id
        collection = storage.get_collection(app=app, name=name)

        return {
            "success": True,
            "message": f"Returned collection(s) {name}",
            "data": collection,
        }
    except Exception as e:
        print(f"{common.PRNT_API} Error: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": {},
        }


# Get all chunks for a source document
@router.post("/getChunks")
def get_chunks(request: Request, params: classes.GetDocumentChunksRequest):
    collection_id = params.collectionId
    document_id = params.documentId
    num_chunks = 0
    app = request.app

    try:
        chunks = storage.get_source_chunks(
            app, collection_name=collection_id, source_id=document_id
        )
        if chunks != None:
            num_chunks = len(chunks)

        return {
            "success": True,
            "message": f"Returned {num_chunks} chunks for document.",
            "data": chunks,
        }
    except Exception as e:
        print(f"{common.PRNT_API} Error: {e}")
        return {
            "success": False,
            "message": f"{e}",
            "data": None,
        }


# Open an OS file exporer on host machine
@router.get("/fileExplore")
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


# Delete one or more source documents by id
@router.post("/deleteDocuments")
def delete_document_sources(
    request: Request,
    params: classes.DeleteDocumentsRequest,
) -> classes.DeleteDocumentsResponse:
    app = request.app

    try:
        collection_name = params.collection_id
        source_ids = params.document_ids
        num_documents = len(source_ids)
        # Find source data
        collection = storage.get_collection(app, name=collection_name)
        sources_to_delete = storage.get_sources_from_ids(
            collection=collection, source_ids=source_ids
        )
        # Remove specified source(s)
        delete_sources(
            app=app, collection_name=collection_name, sources=sources_to_delete
        )

        return {
            "success": True,
            "message": f"Removed {num_documents} source(s): {source_ids}",
        }
    except Exception as e:
        print(f"{common.PRNT_API} Error: {e}")
        return {
            "success": False,
            "message": str(e),
        }


# Delete a collection by id
@router.get("/deleteCollection")
def delete_collection(
    request: Request,
    params: classes.DeleteCollectionRequest = Depends(),
) -> classes.DeleteCollectionResponse:
    app = request.app

    try:
        collection_id = params.collection_id
        db = storage.get_vector_db_client(app)
        collection = db.get_collection(collection_id)
        # Remove all the sources in this collection
        sources = storage.get_collection_sources(collection)
        # Remove all associated source files
        delete_sources(app=app, collection_name=collection_id, sources=sources)
        # Remove the collection
        db.delete_collection(name=collection_id)
        # Remove persisted vector index from disk
        common.delete_vector_store(collection_id, storage.VECTOR_STORAGE_PATH)
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
@router.get("/wipe")
def wipe_all_memories(
    request: Request,
) -> classes.WipeMemoriesResponse:
    app = request.app

    try:
        # Delete all db values
        db = storage.get_vector_db_client(app)
        db.reset()
        # Delete all parsed files in /memories
        file_parsers.delete_all_files()
        # Remove all vector storage collections and folders
        storage.delete_all_vector_storage()
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
