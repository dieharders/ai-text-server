import os
import glob
import json
from typing import Any, List
from chromadb import Collection, PersistentClient
from chromadb.api import ClientAPI
from chromadb.config import Settings
from llama_index.core.schema import IndexNode
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.callbacks import CallbackManager
from server import common

VECTOR_DB_FOLDER = "chromadb"
VECTOR_STORAGE_PATH = common.app_path(VECTOR_DB_FOLDER)

# Helpers


def get_collection_sources(collection: Collection):
    # Get all sources in this collection
    sources_json = collection.metadata.get("sources")
    sources: List[dict] = json.loads(sources_json)
    return sources


# Create a ChromaDB client singleton
# @TODO May need to create this at start of app first run to prevent race condition from using this when creating DB first time.
def get_vector_db_client(app) -> ClientAPI:
    if app.state.db_client == None:
        # "Not recommended for production use" - use HttpClient
        db = PersistentClient(
            # tenant="", # @TODO For multi-tenant db's
            path=VECTOR_STORAGE_PATH,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )
        # Recommended
        # db = HttpClient(
        #     host: str = "localhost",
        #     port: str = "8000", # default port
        #     ssl: bool = False,
        #     headers: Dict[str, str] = {},
        #     settings=Settings(anonymized_telemetry=False, allow_reset=True),
        # )
        app.state.db_client = db
        return db
    return app.state.db_client


# Load a vector index from existing collection and add chunk IndexNode's to it
def add_chunks_to_collection(
    collection: Collection, nodes: List[IndexNode], callback_manager: CallbackManager
):
    # Assign chroma as the vector store to the context
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # The chunks will be persisted automatically by ChromaDB
    index = VectorStoreIndex(
        nodes=nodes,
        storage_context=storage_context,
        show_progress=True,
        callback_manager=callback_manager,
        # embed_model=embed_model, # set from Settings
    )
    # This will force store to disk any added docstore objects
    # index.storage_context.persist(f"./{out_path}")
    return index


# Add the source Document(s) to the Collection's metadata.sources list
def update_collection_sources(collection: Collection, sources: List[dict], mode="add"):
    # Get current collection's sources
    prev_sources = get_collection_sources(collection)
    new_sources: List = []
    # Create new sources
    if mode == "update":
        # @TODO implement updating prev added source
        new_sources = []
        # print(f"Updated sources:\n{new_sources}")
    elif mode == "add":
        if prev_sources:
            prev_sources.extend(sources)
            new_sources = prev_sources
        else:
            new_sources = sources
        # print(f"Added new sources:\n{new_sources}")
    elif mode == "delete":
        # @TODO Implement deletion
        new_sources = []
        # print(f"Removed sources:\n{new_sources}")
    # Update the collection's metadata
    collection.metadata["sources"] = json.dumps(new_sources)
    collection.modify(metadata=collection.metadata)


# Returns all collection names in the specified db
def list_collections(app: Any, tenant="default") -> List[str]:
    collections_list = get_vector_db_client(app).list_collections()
    collection_names = []
    for coll in collections_list:
        collection_names.append(coll.name)
    return collection_names


# Methods


# Returns all collections and their metadata in the specified db
def get_all_collections(app: Any, tenant="default") -> List[dict]:
    collection_names = list_collections(app)
    db = get_vector_db_client(app)
    collections = []
    for name in collection_names:
        # Deserialize some data for front-end
        collection = db.get_collection(name)
        sources = get_collection_sources(collection)
        collection.metadata["sources"] = sources
        collections.append(collection)
    return collections


# Returns a single collection and their metadata in the specified db
def get_collection(app: Any, name: str, tenant="default"):
    db = get_vector_db_client(app)
    collection = db.get_collection(name) or None
    # Deserialize some data for front-end
    sources = get_collection_sources(collection)
    collection.metadata["sources"] = sources
    return collection


def get_document_chunks(app: Any, collection_name: str, document_id: str):
    db = get_vector_db_client(app)
    collection = db.get_collection(collection_name)
    # Get all chunks
    doc_chunks = collection.get(
        where={"sourceId": document_id},  # find by field in each document
        # where={"sourceId": {"$in": chunkIds}},  # or find by field in list of ids
        # ids=ids, # or get directly with chunk ids instead of "where"
        # include=["metadatas", "documents"], # these are included by default
    )
    # Create a list of chunks
    chunks = []
    doc_chunk_ids = doc_chunks["ids"]
    for i, chunk_id in enumerate(doc_chunk_ids):
        chunk_text = doc_chunks["documents"][i]
        chunk_metadata = doc_chunks["metadatas"][i]
        # @TODO Do we need _node_content in metadata?
        chunk_metadata["_node_content"] = json.loads(chunk_metadata["_node_content"])
        result = dict(
            id=chunk_id,
            text=chunk_text,
            metadata=chunk_metadata,
        )
        chunks.append(result)
    # Return all chunks for this source
    print(f"Chunk ids: {doc_chunk_ids}")
    print(f"Returned {len(chunks)} chunks")
    return chunks


def delete_chunks(
    collection: Collection,
    vector_index: VectorStoreIndex,
    chunk_ids: List[str],
):
    # Delete the embeddings from collection
    collection.delete(ids=chunk_ids)
    # Delete embeddings from llama-index
    for c_id in chunk_ids:
        vector_index.delete(c_id)


def delete_source_files(source: dict):
    # Delete all files and references associated with embedded docs
    document_metadata = source["metadata"]
    source_file_path = document_metadata["filePath"]
    document_id = document_metadata["id"]
    # Remove file from disk
    print(f"{common.PRNT_API} Remove file {document_id} from {source_file_path}")
    if os.path.exists(source_file_path):
        os.remove(source_file_path)


# Remove all vector storage collections and folders
def delete_all_vector_storage():
    if os.path.exists(VECTOR_STORAGE_PATH):
        folders = glob.glob(f"{VECTOR_STORAGE_PATH}/*")
        for dir in folders:
            if "chroma.sqlite3" not in dir:
                files = glob.glob(f"{dir}/*")
                for f in files:
                    os.remove(f)  # del files
                os.rmdir(dir)  # del collection folder
    # Remove root vector storage folder and database file
    # os.remove(os.path.join(storage.VECTOR_STORAGE_PATH, "chroma.sqlite3"))
    # os.rmdir(storage.VECTOR_STORAGE_PATH)
