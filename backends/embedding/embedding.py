# @TODO Rename this file to main.py
from typing import List, Any
from llama_index.core import (
    VectorStoreIndex,
    Document,
    Settings,
)
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler  # CBEventType
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from server import common
from .storage import (
    get_vector_db_client,
    add_chunks_to_collection,
    update_collection_sources,
)
from .file_parsers import process_documents
from .text_splitters import markdown_heading_split, markdown_document_split
from .chunking import chunks_from_documents, create_source_record
from .file_loaders import documents_from_sources

# from chromadb.utils import embedding_functions
# from llama_index.core.response_synthesizers import ResponseMode
# from llama_index.core.indices import load_index_from_storage, load_indices_from_storage

embedding_model_names = dict(
    BAAI_Small="BAAI/bge-small-en-v1.5",
    BAAI_Large="BAAI/bge-large-en",
    GTE="thenlper/gte-base",
)

# Constants

EMBEDDING_MODEL_CACHE_PATH = common.app_path("embed_models")
CHUNKING_STRATEGIES = {
    "MARKDOWN_HEADING_SPLIT": markdown_heading_split,
    "MARKDOWN_DOCUMENT_SPLIT": markdown_document_split,
}

# Helpers


# Create document embeddings from chunks
def embed_pipeline(parser, vector_store, documents: List[Document]):
    pipeline = IngestionPipeline(
        transformations=[parser],
        vector_store=vector_store,
        docstore=SimpleDocumentStore(),  # enabled document management
    )
    # Ingest directly into a vector db
    pipeline.run(documents=documents)


# Define a specific embedding method globally
# @TODO In future could return different models for different tasks.
# @TODO Use the embedder recorded in the metadata (when retrieving)
def define_embedding_model(app: Any):
    # from transformers import AutoModel, AutoTokenizer
    print(f"{common.PRNT_EMBED} Initializing embed model...", flush=True)
    embed_model = "local"

    if app.state.embed_model:
        embed_model = app.state.embed_model
    else:
        embed_model_name = embedding_model_names["GTE"]  # name on Huggingface
        embed_model = HuggingFaceEmbedding(
            model_name=embed_model_name,
            # model=AutoModel.from_pretrained(embed_model_name),
            cache_folder=EMBEDDING_MODEL_CACHE_PATH,
            # tokenizer=AutoTokenizer.from_pretrained(embed_model_name),
        )
        app.state.embed_model = embed_model

    Settings.embed_model = embed_model
    return embed_model


# Methods


# For debugging llama-index events
def create_index_callback_manager() -> CallbackManager:
    # Debugging - https://docs.llamaindex.ai/en/v0.10.19/examples/callbacks/LlamaDebugHandler.html
    llama_debug = LlamaDebugHandler(print_trace_on_end=True)
    callback_manager = CallbackManager([llama_debug])
    return callback_manager


# Load collection of document embeddings from disk
# @TODO Cleanup args, some (context_window, num_output, chunk_size, prompts) should be updated before a query is called
def load_embedding(app: dict, collection_name: str) -> VectorStoreIndex:
    vector_index = None
    try:
        # Initialize embedding func
        define_embedding_model(app)
        # Initialize client
        db = get_vector_db_client(app)
        # Get collection
        collection = db.get_or_create_collection(name=collection_name)
        # Assign chroma as the vector store of the context
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        # Load index from stored vectors
        vector_index = VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=storage_context,
            show_progress=True,
            callback_manager=create_index_callback_manager(),
            # store_nodes_override=True,  # this populates docstore.json with chunk nodes
        )
    except Exception as e:
        print(f"{common.PRNT_EMBED} Failed to load vector index: {e}", flush=True)
    return vector_index


# Create nodes from a single source Document
async def create_index_nodes(
    app: dict,
    input_file: dict,
    form: dict,
) -> List[Document]:
    print(f"{common.PRNT_EMBED} Creating nodes...", flush=True)
    # File attributes
    checksum: str = input_file.get("checksum")
    file_name = input_file.get("file_name")
    source_file_path: str = input_file.get("path_to_file")
    document_id: str = form["document_id"]
    document_name: str = form["document_name"]
    description: str = form["description"]
    tags: str = form["tags"]
    # Read in source files and build documents
    source_paths = [source_file_path]
    source_metadata = dict(
        name=document_name,
        description=description,
        checksum=checksum,
        fileName=file_name,
        filePath=source_file_path,
        tags=tags,
    )
    file_nodes = await documents_from_sources(
        app=app,
        sources=source_paths,
        source_id=document_id,
        source_metadata=source_metadata,
    )
    # Optional step, Post-Process source text for optimal embedding/retrieval for LLM
    is_dirty = False  # @TODO Have `documents_from_sources` determine when docs are already processed
    if is_dirty:
        file_nodes = process_documents(nodes=file_nodes)
    return file_nodes


# Create embeddings for one file (input) at a time
# We create one source per upload
def create_new_embedding(
    nodes: List[Document],
    form: dict,
    app: Any,
):
    try:
        print(f"{common.PRNT_EMBED} Creating embeddings...", flush=True)
        # File attributes
        chunk_size: int = form["chunk_size"] or 300
        chunk_overlap: int = form["chunk_overlap"] or 0
        chunk_strategy: str = (
            form["chunk_strategy"] or list(CHUNKING_STRATEGIES.keys())[0]
        )
        text_splitter = CHUNKING_STRATEGIES[chunk_strategy]
        collection_name: str = form["collection_name"]
        # Loop through each file
        for node in nodes:
            # Create source document records for Collection metadata
            source_record = create_source_record(document=node)
            # Split document texts
            splitter = text_splitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            # Build chunks
            print(f"{common.PRNT_EMBED} Chunking text...", flush=True)
            parsed_nodes = splitter.get_nodes_from_documents(
                documents=[node],  # pass list of files (in Document format)
                show_progress=True,
            )
            [chunks_ids, chunk_nodes] = chunks_from_documents(
                source_record=source_record,
                parsed_nodes=parsed_nodes,  # pass in text nodes to return as chunks
                documents=[node],
            )
            # Record the ids of each chunk
            source_record["chunkIds"] = chunks_ids
            # Setup embedding model
            define_embedding_model(app)
            # Create/load a vector index, add chunks and persist to storage
            print(f"{common.PRNT_EMBED} Adding chunks to collection...", flush=True)
            db = get_vector_db_client(app)
            collection = db.get_collection(name=collection_name)
            vector_index = add_chunks_to_collection(
                collection=collection,
                nodes=chunk_nodes,
                callback_manager=create_index_callback_manager(),
            )
            # Add/update `collection.metadata.sources` list
            print(f"{common.PRNT_EMBED} Updating collection metadata...", flush=True)
            update_collection_sources(
                collection=collection,
                sources=[source_record],
                mode="add",
            )
        print(f"{common.PRNT_EMBED} Embedding succeeded!", flush=True)
    except (Exception, KeyError) as e:
        msg = f"Embedding failed: {e}"
        print(f"{common.PRNT_EMBED} {msg}", flush=True)
