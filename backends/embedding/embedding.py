import os
import uuid
import copy
import json
import re
import hashlib
from datetime import datetime
from typing import List, Optional
import chromadb
from typing import Any, Type
from llama_index.llms import LlamaCPP
from chromadb.api import ClientAPI
from chromadb.config import Settings
from llama_index import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    ServiceContext,
)
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from llama_index.vector_stores import ChromaVectorStore
from llama_index.storage.storage_context import StorageContext
from llama_index.prompts import PromptTemplate
from llama_index.evaluation import FaithfulnessEvaluator  # ResponseEvaluator

# from llama_index.embeddings import HuggingFaceEmbedding


# @TODO Setup prompt templates in conjunction with llm when querying
# @TODO Pass a template like this as a prop when creating embeddings
DEFAULT_SYSTEM_PROMPT = """You are an AI assistant that answers questions in a friendly manner, based on the given source documents. Here are some rules you always follow:
- Generate human readable output, avoid creating output with gibberish text.
- Generate only the requested output, don't include any other language before or after the requested output.
- Never say thank you, that you are happy to help, that you are an AI agent, etc. Just answer directly.
- Generate professional language typically used in business documents in North America.
- Never generate offensive or foul language.
"""


# Define a specific embedding method
def create_embed_model():
    return "local"  # embed_model = HuggingFaceEmbedding(model_name="bert-base-multilingual-cased")


# Create a ChromaDB client singleton
def create_db_client(storage_directory: str):
    return chromadb.PersistentClient(
        path=storage_directory,
        settings=Settings(anonymized_telemetry=False, allow_reset=True),
    )


def create_checksum(file_path: str):
    BUF_SIZE = 65536
    sha1 = hashlib.sha1()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    print("[embedding api] SHA1: {0}".format(sha1.hexdigest()))
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
    print(f"[embedding api] Check extension: {file_extension}")
    return is_supported


# Return a list of documents
def get_document(
    collection_name: str,
    document_ids: List[str],
    db,
    include: Optional[List[str]] = None,
):
    collection = db.get_collection(collection_name)

    if include == None:
        data = collection.get(ids=document_ids)
    else:
        data = collection.get(ids=document_ids, include=include)

    # Return all document data in a single object
    documents_array = []
    for index, id in enumerate(document_ids):
        doc = {}
        metadatas = data["metadatas"]
        embeddings = data["embeddings"]
        documents = data["documents"]
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
    name, collection_name, description, tags, output_folder_path, input_file_path
):
    try:
        if not name or not collection_name:
            raise Exception("You must supply a collection and memory name.")
        if not os.path.exists(input_file_path):
            raise Exception("File does not exist.")
        if not check_file_support(input_file_path):
            raise Exception("Unsupported file format.")
    except (Exception, ValueError, TypeError, KeyError) as error:
        print(f"[embedding api] Pre-processing failed: {error}")
        raise Exception(error)
    else:
        # Read the form inputs
        new_filename = f"{name}.md"
        # Create output folder for parsed file
        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)
        target_output_path = os.path.join(output_folder_path, new_filename)
        # Format tags
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
        # Create a checksum for validation later
        checksum = create_checksum(target_output_path)
    finally:
        # Delete uploaded file
        if os.path.exists(input_file_path):
            os.remove(input_file_path)
            print(f"[embedding api] Removed temp file upload.")
        else:
            print(
                "[embedding api] Failed to delete temp file upload. The file does not exist."
            )

    print(f"[embedding api] Successfully processed {target_output_path}")
    return {
        "filename": new_filename,
        "path_to_file": target_output_path,
        "checksum": checksum,
    }


# Create a vector embedding for the given document.
def create_embedding(
    file_path: str,
    checksum: str,
    storage_directory: str,
    form: Any,
    llm: Type[LlamaCPP],
    db_client: Type[ClientAPI],
):
    try:
        # Load in document files
        print(f"[embedding api] Load docs: {file_path}")
        documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
        # Create a new document embedding
        collection_name: str = form["collection_name"]
        document_name: str = form["document_name"]
        document_id: str = form["document_id"]
        description: str = form["description"]
        tags: str = form["tags"]
        # You MUST use the same embedding function to create as you do to get collection.
        chroma_collection = db_client.get_collection(collection_name)
        # Update sources (document ids) metadata
        print("[embedding api] Update collection metadata")
        metadata = copy.deepcopy(chroma_collection.metadata)  # deepcopy
        updated_sources_array = []
        if metadata != None and "sources" in metadata:
            sources_json = metadata["sources"]
            sources_array = json.loads(sources_json)
            updated_sources_array = list(sources_array)  # copy
        # Add/lookup sources by their universally unique id
        new_source_id = document_id or str(uuid.uuid4())
        new_source_metadata = {
            # Globally unique id
            "id": new_source_id,
            # Source id
            "name": document_name,
            # Update sources paths (where original uploaded files are stored)
            "filePath": file_path,
            # Update other metadata
            "description": description,
            "tags": tags,
            "checksum": checksum,
            "createdAt": datetime.utcnow().strftime("%B %d %Y - %H:%M:%S"),
        }
        # Find and replace source id or add it
        if new_source_id in updated_sources_array:
            source_index = updated_sources_array.index(new_source_id)
            updated_sources_array[source_index] = new_source_id
        else:
            updated_sources_array.append(new_source_id)
        # Convert data to json
        print("[embedding api] Convert metadata to json...")
        updated_sources_json = json.dumps(updated_sources_array)
        metadata["sources"] = updated_sources_json
        # Debugging
        llama_debug = LlamaDebugHandler(print_trace_on_end=True)
        callback_manager = CallbackManager([llama_debug])
        # Create embedding service
        service_context = ServiceContext.from_defaults(
            embed_model=create_embed_model(),
            llm=llm,
            context_window=3900,
            callback_manager=callback_manager,
            chunk_size=512,
            chunk_overlap=20,
            chunk_size_limit=512,
        )
        # Create a vector db
        print("[embedding api] Creating index...")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        # Create an index used for querying. This will be saved to disk for later use.
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        document = documents[0]
        document_text = document.get_content()
        index = VectorStoreIndex.from_documents(
            collection_name=collection_name,
            ids=[document_id],
            client=db_client,
            metadatas=[new_source_metadata],
            documents=[document],  # just one file for now
            storage_context=storage_context,
            service_context=service_context,
            persist_directory=storage_directory,
            show_progress=True,
            # use_async=True,
        )
        # Update the collection with new metadata
        chroma_collection.modify(metadata=metadata)
        # Update if embedding already exists
        if document_id:
            set_chroma_collection = chroma_collection.update
        # Add new document to collection
        else:
            set_chroma_collection = chroma_collection.add
        set_chroma_collection(
            ids=[new_source_id],
            metadatas=[new_source_metadata],
            documents=[document_text],
            # embeddings=embeddings, # optionally add your own
        )
        # Save index to disk. We can read from disk later without needing to re-construct.
        index.storage_context.persist(
            persist_dir=os.path.join(storage_directory, collection_name)
        )
        # Done
        print(f"[embedding api] Finished embedding, path: {file_path}")
        return True
    except Exception as e:
        msg = f"Embedding failed:\n{e}"
        print(f"[embedding api] {msg}")
        raise Exception(msg)


# Determine which nodes contributed to the answer
def contributing_references(response, eval_result):
    num_source_nodes = len(response.source_nodes)
    print(f"[embedding api] Number of source nodes: {num_source_nodes}")
    print(f"[embedding api] Result is passing? {str(eval_result.passing)}")
    for s in response.source_nodes:
        print(f"[embedding api] Node Score: {s.score}")
        print(s.node.metadata)
    return {
        "num_refs": num_source_nodes,
    }


def verify_response(response, service_context):
    # Define evaluator, evaluates whether a response is faithful to the contexts
    print("[embedding api] Evaluating truthiness of response...")
    evaluator = FaithfulnessEvaluator(service_context=service_context)
    eval_result = evaluator.evaluate_response(response=response)
    # evaluator = ResponseEvaluator(service_context=service_context)
    # eval_result = evaluator.evaluate(query=query, response=response, contexts=[service_context])
    print(f"[embedding api] Truthy evaluation results: {eval_result}")
    contributing_references(response, eval_result)


# Query Data, note top_k is set to 3 so it will use the top 3 nodes it finds in vector index
def query_embedding(query, index):
    print("[embedding api] Query Data")
    # system_prompt = sys_prompt or DEFAULT_SYSTEM_PROMPT
    # query_wrapper_prompt = PromptTemplate(
    #     f"[INST]<<SYS>>\n{system_prompt}<</SYS>>\n\n{query}[/INST] "
    # )
    query_engine = index.as_query_engine(
        similarity_top_k=3,
        # streaming=True,
    )
    response = query_engine.query(query)
    return response


# Load index from disk
def load_embedding(llm, db_client, collection_name: str):
    # Debugging
    llama_debug = LlamaDebugHandler(print_trace_on_end=True)
    callback_manager = CallbackManager([llama_debug])
    # Create embedding service
    service_context = ServiceContext.from_defaults(
        llm=llm, embed_model=create_embed_model(), callback_manager=callback_manager
    )
    # You MUST get() with the same embedding function you supplied while creating the collection.
    chroma_collection = db_client.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    # Create index from vector db
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        service_context=service_context,
    )
    return index
