import os
import uuid
import json
import re
import hashlib
from datetime import datetime
from typing import List, Optional
from typing import Any, Type
from chromadb import Documents, EmbeddingFunction, Embeddings, PersistentClient
from chromadb.api import Collection
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from llama_index import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    ServiceContext,
    Document,
    # set_global_service_context,
)
from llama_index.llms import LlamaCPP
from llama_index.storage.index_store import SimpleIndexStore
from llama_index.schema import BaseNode
from llama_index.logger import LlamaLogger
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from llama_index.vector_stores import ChromaVectorStore
from llama_index.storage.storage_context import StorageContext
from llama_index.indices import load_index_from_storage
from llama_index.prompts import PromptTemplate
from llama_index.evaluation.faithfulness import FaithfulnessEvaluator, ResponseEvaluator
from llama_index.ingestion import IngestionPipeline
from llama_index.storage.docstore import SimpleDocumentStore
from llama_index.embeddings import HuggingFaceEmbedding
from llama_index.response_synthesizers import ResponseMode
from transformers import AutoModel, AutoTokenizer
from server import classes
from .chunking import markdown_heading_split, markdown_document_split


# More templates found here: https://github.com/run-llama/llama_index/blob/main/llama_index/prompts/default_prompts.py
DEFAULT_SYSTEM_PROMPT = """You are an AI assistant that answers questions in a friendly manner, based on the given source documents. Here are some rules you always follow:
- Generate human readable output, avoid creating output with gibberish text.
- Generate only the requested output, don't include any other language before or after the requested output.
- Never say thank you, that you are happy to help, that you are an AI agent, etc. Just answer directly.
- Generate professional language typically used in business documents in North America.
- Never generate offensive or foul language.
"""
DEFAULT_PROMPT_TEMPLATE = (
    "We have provided context information below. \n"
    "---------------------\n"
    "{context_str}"
    "\n---------------------\n"
    "Given this information, please answer the question: {query_str}\n"
)

embed_model = None
embedding_model_names = dict(BAAI="BAAI/bge-large-en", GTE="thenlper/gte-base")
embed_model_name = embedding_model_names["GTE"]  # name on Huggingface
embed_model_folder_name = "embed_models"
embed_model_cache_dir = os.path.join(os.getcwd(), embed_model_folder_name)

CHUNKING_STRATEGIES = {
    "MARKDOWN_HEADING_SPLIT": markdown_heading_split,
    "MARKDOWN_DOCUMENT_SPLIT": markdown_document_split,
}

# Helpers


def get_collection_storage_dir(collection_name: str):
    return os.path.join(os.getcwd(), "chromadb", collection_name)


# @TODO Define this, might be easier to setup embedding pipeline this way.
class CustomEmbeddingFunction(EmbeddingFunction):
    def __call__(self, texts: Documents) -> Embeddings:
        # @TODO embed the documents somehow...
        # chunks = document_split()
        # embeddings = []
        # for t in texts:
        #     embedding = embedding_functions.DefaultEmbeddingFunction(t)
        #     embeddings.append(embedding)
        # @TODO How to split chunks and embed??
        return embedding_functions.DefaultEmbeddingFunction()


# Create document embeddings from chunks
def embed_pipeline(parser, vector_store, documents: List[Document]):
    pipeline = IngestionPipeline(
        transformations=[parser],
        vector_store=vector_store,
        docstore=SimpleDocumentStore(),  # enabled document management
    )
    # Ingest directly into a vector db
    pipeline.run(documents=documents)


# Load in one file at a time and return a list of llama-index Document objects
def load_files(file_path: str, sources_metadata: dict, checksum: str) -> List[Document]:
    print(f"[embedding api] Loading docs: {file_path}", flush=True)
    reader = SimpleDirectoryReader(input_files=[file_path])
    nodes = reader.load_data()
    if len(nodes) == 0:
        raise Exception("No documents found.")

    # Combine all text (loaders splits the file into several documents??)
    combined_text = ""
    for n in nodes:
        combined_text += n.get_content()

    # Create a custom document object
    file_paths = file_path.split(".")
    document = Document(text=combined_text, metadata=nodes[0].metadata)
    document.hash = checksum
    document.metadata["file_type"] = file_paths[len(file_paths) - 1]
    # document.metadata["sources"] = json.dumps(sources_metadata)
    document.doc_id = sources_metadata["id"]

    return [document]


# Methods


def get_document_store(collection_name: str):
    dir = get_collection_storage_dir(collection_name)
    docstore = SimpleDocumentStore.from_persist_dir(persist_dir=dir)
    # print(f"docstore::{docstore.docs.values()}", flush=True)
    return docstore


def get_index_store(collection_name: str):
    dir = get_collection_storage_dir(collection_name)
    index_store = SimpleIndexStore.from_persist_dir(persist_dir=dir)
    # print(f"index_store::{index_store.to_dict()}", flush=True)
    return index_store


def get_document_chunks(collection_id, document: Document):
    chunk_list: List[BaseNode] = []

    if "chunk_ids" in document["metadata"]:
        node_ids = document["metadata"]["chunk_ids"]
        name = document["metadata"]["name"]

        try:
            docstore = get_document_store(collection_id)
            nodes = docstore.get_nodes(json.loads(node_ids), False)
            for n in nodes:
                print(
                    f"Document: '{name}' | chunked text:\n\n{n.text}\n\n",
                    flush=True,
                )
                chunk_list.append(n)
        except Exception as e:
            print(f"[embedding] Error: {e}", flush=True)
            pass
    return chunk_list


# Define a specific embedding method
# @TODO In future could return different models for different tasks.
def create_embed_model():
    if embed_model is None:
        tokenizer_name = embed_model_name  # usually the same as model_name
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        model = AutoModel.from_pretrained(embed_model_name)
        return HuggingFaceEmbedding(
            model_name=embed_model_name,
            model=model,
            tokenizer_name=tokenizer_name,
            tokenizer=tokenizer,
            cache_folder=embed_model_cache_dir,
        )
        # return "local"

    else:
        return embed_model


# Create a ChromaDB client singleton
def create_db_client(storage_directory: str):
    return PersistentClient(
        path=storage_directory,
        settings=Settings(anonymized_telemetry=False, allow_reset=True),
    )


def get_vectordb_client(app):
    if app.state.db_client == None:
        app.state.db_client = create_db_client(app.state.storage_directory)
    return app.state.db_client


def create_checksum(file_path: str):
    BUF_SIZE = 65536
    sha1 = hashlib.sha1()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    print("[embedding api] SHA1: {0}".format(sha1.hexdigest()), flush=True)
    return sha1.hexdigest()


def check_file_support(filePath: str):
    # Check supported file types
    input_file_path = filePath
    file_extension = input_file_path.rsplit(".", 1)[1]
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
    print(f"[embedding api] Check extension: {file_extension}", flush=True)
    return is_supported


# Create a filename for a parsed document memory
def create_parsed_filename(collection_name: str, document_name: str):
    return f"{collection_name}--{document_name}.md"


# Return a list of documents
def get_document(
    collection_name: str,
    document_ids: List[str],
    app: Any,
    include: Optional[List[str]] = None,
):
    db = get_vectordb_client(app)
    collection: Type[Collection] = db.get_collection(collection_name)

    if include == None:
        data = collection.get(ids=document_ids)
    else:
        data = collection.get(ids=document_ids, include=include)

    # Return all document data
    documents_array = []
    for index, id in enumerate(document_ids):
        doc = {}
        metadatas = data["metadatas"]
        embeddings = data["embeddings"]
        documents = data["documents"]
        # Create a custom object w/ all attrs
        if index < len(metadatas) and len(metadatas) > 0:
            if metadatas:
                doc["metadata"] = metadatas[index]
            if embeddings:
                doc["embeddings"] = embeddings[index]
            if documents:
                doc["documents"] = documents[index]
            documents_array.append(doc)
    return documents_array


def pre_process_documents(
    document_name: str,
    collection_name: str,
    description: str,
    tags: str,
    output_folder_path: str,
    input_file_path: str,
    document_id: str = "",  # supplied if document already exists
):
    try:
        if not document_name or not collection_name:
            raise Exception("You must supply a collection and memory name.")
        if not os.path.exists(input_file_path):
            raise Exception("File does not exist.")
        if not check_file_support(input_file_path):
            raise Exception("Unsupported file format.")
    except (Exception, ValueError, TypeError, KeyError) as error:
        print(f"[embedding api] Pre-processing failed: {error}", flush=True)
        raise Exception(error)
    else:
        # Read the supplied id or assign a new one
        source_id = document_id or str(uuid.uuid4())
        new_filename = create_parsed_filename(collection_name, source_id)
        # Create output folder for parsed file
        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)
        target_output_path = os.path.join(output_folder_path, new_filename)
        # Format tags for inclusion in document
        comma_sep_tags = re.sub("\s+", ", ", tags.strip())
        # Finalize parsed file
        # @TODO If the file is not text, then create a text description of the contents (via VisionAi, Human, OCR)
        # Copy text contents of original file into a new file, parsed for embedding
        with open(target_output_path, "w", encoding="utf-8") as output_file, open(
            input_file_path, "r", encoding="utf-8"
        ) as input_file:
            # Check if header exists
            first_line = input_file.readline()
            if first_line != "---\n":
                # Add a header to file
                output_file.write("---\n")
                output_file.write(f"collection: {collection_name}\n")
                output_file.write(f"document: {document_name}\n")
                output_file.write(f"description: {description}\n")
                output_file.write(f"tags: {comma_sep_tags}\n")
                output_file.write("---\n\n")
            input_file.seek(0)  # set back to start of file
            # Copy each line from source file
            output_file.writelines(line for line in input_file)
            # @TODO Copied text should be parsed and edited to include markdown syntax to describe important bits (headings, attribution, links)
            # @TODO Copied contents may include things like images/graphs that need special parsing to generate an effective text description
            # parsed_text = markdown.parse(copied_text)
        # Create a checksum for validation later
        checksum = create_checksum(target_output_path)
    finally:
        # Delete uploaded file
        if os.path.exists(input_file_path):
            os.remove(input_file_path)
            print(f"[embedding api] Removed temp file upload.", flush=True)
        else:
            print(
                "[embedding api] Failed to delete temp file upload. The file does not exist.",
                flush=True,
            )

    print(f"[embedding api] Successfully processed {target_output_path}", flush=True)
    return {
        "document_id": source_id,
        "file_name": new_filename,
        "path_to_file": target_output_path,
        "checksum": checksum,
    }


# Create a vector embedding for the given document.
def create_embedding(
    processed_file: dict,
    form: dict,
    app: Any,
):
    try:
        # File attributes
        file_name: str = processed_file["file_name"]
        file_path: str = processed_file["path_to_file"]
        checksum: str = processed_file["checksum"]

        # Create source document metadata
        print("[embedding api] Creating sources metadata...", flush=True)
        collection_name: str = form["collection_name"]
        document_name: str = form["document_name"]
        document_id: str = form["document_id"]
        description: str = form["description"]
        tags: str = form["tags"]
        chunk_size: int = form["chunk_size"] or 300
        chunk_overlap: int = form["chunk_overlap"] or 0
        chunk_strategy: str = (
            form["chunk_strategy"] or list(CHUNKING_STRATEGIES.keys())[0]
        )
        # @TODO Use this to set chunk_size, etc from doc metadata
        # is_update = form["is_update"]
        if not document_id or not collection_name or not document_name:
            raise Exception("Missing input values.")
        sources_metadata = {
            # Globally unique source document id
            "id": document_id,
            # Source document name
            "name": document_name,
            # Sources path (where original uploaded file is stored)
            "filePath": file_path,
            # Update other metadata
            "description": description,
            "tags": tags,
            "checksum": checksum,
            "createdAt": datetime.utcnow().strftime("%B %d %Y - %H:%M:%S"),
            "fileName": file_name,
            "chunk_ids": [],
        }

        # Load files
        documents = load_files(file_path, sources_metadata, checksum)

        # Debugging
        llama_debug = LlamaDebugHandler(print_trace_on_end=True)
        callback_manager = CallbackManager([llama_debug])

        # Create/load a vector store
        print("[embedding api] Transforming data...", flush=True)
        # You MUST use the same embedding function to create as you do to get collection.
        db = get_vectordb_client(app)
        chroma_collection: Type[Collection] = db.get_or_create_collection(
            collection_name
        )
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Split documents text into chunks
        print("[embedding api] Chunking documents...", flush=True)
        llm: Type[LlamaCPP] = app.state.llm
        text_splitter = CHUNKING_STRATEGIES[chunk_strategy]
        parser = text_splitter(chunk_size, chunk_overlap)
        chunks = parser.get_nodes_from_documents(documents)
        print(
            f"[embedding api] Loaded {len(documents)} document(s), {len(chunks)} chunk(s)",
            flush=True,
        )
        for ichunk, ch in enumerate(chunks):
            print(f"[embedding api] Chunk ({ichunk}):\n\n{ch}")

        # Create document embeddings from chunks
        service_context = ServiceContext.from_defaults(
            llm=llm,
            embed_model=create_embed_model(),
            callback_manager=callback_manager,
            llama_logger=LlamaLogger,
            # node_parser=parser, # optional, pass custom parser
        )
        print("[embedding api] Creating embedding...", flush=True)
        vector_index = VectorStoreIndex(
            nodes=chunks,
            storage_context=storage_context,
            service_context=service_context,
            show_progress=True,
            store_nodes_override=True,  # this populates docstore.json with chunk nodes
        )

        # Update the collection's sources catalog
        collection_metadata = dict(**chroma_collection.metadata)  # copy
        collection_sources_json = collection_metadata["sources"]
        collection_sources: List = json.loads(collection_sources_json)
        # Find and replace source id or add it
        if document_id in collection_sources:
            source_index = collection_sources.index(document_id)
            collection_sources[source_index] = document_id
        else:
            collection_sources.append(document_id)
        collection_metadata["sources"] = json.dumps(collection_sources)
        chroma_collection.modify(metadata=collection_metadata)

        # Store embeddings and text in vector storage
        print("[embedding api] Storing vector embeddings...", flush=True)
        ids = []
        document_texts = []
        metadatas = []
        # Get embeddings we just generated to store in vector db
        embeddings = []
        collection: Type[Collection] = db.get_collection(collection_name)
        data = collection.get(ids=ids, include=["embeddings"])
        embedding_data: List[int] = data["embeddings"]
        # Update document metadatas with its' chunk ids
        chunk_ids = []
        for c in chunks:
            chunk_ids.append(c.id_)
        sources_metadata["chunk_ids"] = json.dumps(chunk_ids)
        # Set document data to store
        for index, d in enumerate(documents):
            ids.append(d.id_)
            document_texts.append(d.text)
            metadatas.append(sources_metadata)
            embeddings.append(embedding_data[index])
        # Insert new document(s)
        chroma_collection.upsert(
            ids=ids,
            documents=document_texts,
            metadatas=metadatas,  # This tells us what is in the collection
            embeddings=embeddings,  # Add our pre-calc vectors
        )

        # Save index to disk. We can read from disk later without needing to re-construct.
        storage_directory = app.state.storage_directory
        vector_index.storage_context.persist(
            persist_dir=os.path.join(storage_directory, collection_name)
        )

        # Done
        print(f"[embedding api] Finished embedding, path: {file_path}", flush=True)
        return True
    except Exception as e:
        msg = f"Embedding failed:\n{e}"
        print(f"[embedding api] {msg}", flush=True)
        raise Exception(msg)


# Determine which nodes contributed to the answer
def contributing_references(response, eval_result):
    num_source_nodes = len(response.source_nodes)
    print(f"[embedding api] Number of source nodes: {num_source_nodes}", flush=True)
    print(f"[embedding api] Result is passing? {str(eval_result.passing)}", flush=True)
    for s in response.source_nodes:
        print(f"[embedding api] Node Score: {s.score}", flush=True)
        print(s.node.metadata, flush=True)
    return {
        "num_refs": num_source_nodes,
    }


# Verifies whether a response is faithful to the contexts
def verify_response(response, service_context, query=""):
    print("[embedding api] Verifying truthiness of response...", flush=True)
    evaluator = FaithfulnessEvaluator(service_context=service_context)
    eval_result = evaluator.evaluate_response(query=query, response=response)
    print(f"[embedding api] Faithfulness results: {eval_result}", flush=True)
    contributing_references(response, eval_result)


# Evaluates whether a response is faithful to the query
def evaluate_response(response, service_context, query=""):
    # Define evaluator, evaluates whether a response is faithful to the contexts
    print("[embedding api] Evaluating correctness of response...", flush=True)
    evaluator = ResponseEvaluator(service_context=service_context)
    eval_result = evaluator.evaluate(
        query=query, response=response, contexts=[service_context]
    )
    print(f"[embedding api] Verification results: {eval_result}", flush=True)
    contributing_references(response, eval_result)


# Query Private Data
def query_embedding(
    query: str,
    prompt_template_str: classes.RagTemplateData,
    index: VectorStoreIndex,
    options: classes.ContextRetrievalOptions,
):
    print("[embedding api] Query Data", flush=True)
    custom_qa_prompt = PromptTemplate(
        template=prompt_template_str.text, prompt_type=prompt_template_str.type
    )
    # Used when no good response is returned and we want to further "handle" the answer before its delivered to user.
    # @TODO Hardcoded for now, Set this from passed args in request
    refine_template_str = (
        "The original question is as follows: {query_str}\nWe have provided an"
        " existing answer: {existing_answer}\nWe have the opportunity to refine"
        " the existing answer (only if needed) with some more context"
        " below.\n------------\n{context_msg}\n------------\nUsing both the new"
        " context and your own knowledge, update or repeat the existing answer.\n"
    )
    custom_refine_prompt = PromptTemplate(refine_template_str)

    # Call query() in query mode
    query_engine = index.as_query_engine(
        streaming=True,
        # service_context=service_context,
        # summary_template=summary_template,
        # simple_template=simple_template,
        text_qa_template=custom_qa_prompt,
        refine_template=custom_refine_prompt,
        similarity_top_k=options["similarity_top_k"],
        response_mode=options["response_mode"],
    )
    # OR in chat mode
    # chat_engine = index.as_chat_engine(...)

    streaming_response = query_engine.query(query)
    for node in streaming_response.source_nodes:
        print(
            f"[embedding api] chunk id::{node.id_} | score={node.score}\ntext=\n{node.text}",
            flush=True,
        )
    return streaming_response


# Load embedding index from disk
# @TODO Cleanup args, some (context_window, num_output, chunk_size, prompts) should be updated before a query is called
def load_embedding(
    app,
    collection_name: str,
    # query_string: Optional[str] = "",
    # rag_prompt_template: Optional[classes.RagTemplateData] = None,
    num_output: Optional[int] = 0,
    context_window: Optional[int] = 2000,
    system_prompt: Optional[str] = None,
):
    db = get_vectordb_client(app)
    persist_dir = get_collection_storage_dir(collection_name)

    # Debugging
    llama_debug = LlamaDebugHandler(print_trace_on_end=True)
    callback_manager = CallbackManager([llama_debug])

    # Construct args
    llm: Type[LlamaCPP] = app.state.llm
    sys_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
    # promptTemplateText = rag_prompt_template.text or DEFAULT_PROMPT_TEMPLATE
    # query_wrapper_prompt = PromptTemplate(
    #     template=promptTemplateText,
    #     prompt_type=rag_prompt_template.type,
    # )
    # completion_template = query_wrapper_prompt.format(
    #     context_str="", query_str=query_string
    # )
    # chat_template = query_wrapper_prompt.format_messages(
    #     context_str="", query_str=query_string
    # )

    # Create service
    service_context = ServiceContext.from_defaults(
        llm=llm,
        embed_model=create_embed_model(),
        callback_manager=callback_manager,
        # Prompt helper kwargs
        context_window=context_window,
        num_output=num_output,
        # chunk_size=chunk_size,
        llama_logger=LlamaLogger,
        # prompt_helper={},  # @TODO helps deal with LLM context window token limitations
        # Prompt templating
        system_prompt=sys_prompt,
        # query_wrapper_prompt=promptTemplateText,
    )

    # You MUST get() with the same embedding function you supplied while creating the collection.
    chroma_collection = db.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(
        chroma_collection=chroma_collection,
        collection_name=collection_name,
        persist_dir=persist_dir,
        show_progress=True,
    )

    # Load index from disk
    index = None
    try:
        storage_context = StorageContext.from_defaults(
            persist_dir=persist_dir,
            vector_store=vector_store,
            docstore=get_document_store(collection_name),
            index_store=get_index_store(collection_name),
        )
        index = load_index_from_storage(
            storage_context=storage_context,
            service_context=service_context,
        )
    except Exception as e:
        print(f"Error: {e}")

    return index
