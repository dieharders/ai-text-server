import uuid
import copy
import json
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


# Define a specific embedding method
def create_embed_model():
    return "local"  # embed_model = HuggingFaceEmbedding(model_name="bert-base-multilingual-cased")


# Create a ChromaDB client singleton
def create_db_client(storage_directory: str):
    return chromadb.PersistentClient(
        path=storage_directory,
        settings=Settings(anonymized_telemetry=False, allow_reset=True),
    )


# Create a vector embedding for the given document.
def create_embedding(
    file_path: str,
    created_at: str,
    checksum: str,
    storage_directory: str,
    form: Any,
    llm: Type[LlamaCPP],
    db_client: Type[ClientAPI],
):
    try:
        # @TODO Setup prompt templates in conjunction with llm when querying
        SYSTEM_PROMPT = """You are an AI assistant that answers questions in a friendly manner, based on the given source documents. Here are some rules you always follow:
        - Generate human readable output, avoid creating output with gibberish text.
        - Generate only the requested output, don't include any other language before or after the requested output.
        - Never say thank you, that you are happy to help, that you are an AI agent, etc. Just answer directly.
        - Generate professional language typically used in business documents in North America.
        - Never generate offensive or foul language.
        """
        query_wrapper_prompt = PromptTemplate(
            "[INST]<<SYS>>\n" + SYSTEM_PROMPT + "<</SYS>>\n\n{query_str}[/INST] "
        )
        # Load in document files
        print(f"[embedding api] Load docs: {file_path}")
        documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
        # Create a new document embedding
        collection_name: str = form.collection_name
        document_name: str = form.name
        description: str = form.description
        tags: str = form.tags
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
        new_source = {
            # Globally unique id
            "id": str(uuid.uuid4()),
            # Source id
            "name": document_name,
            # Update processing flag for this document
            "processing": "pending",
            # Update sources paths (where original uploaded files are stored)
            "filePath": file_path,
            # Update other metadata
            "description": description,
            "tags": tags,
        }
        updated_sources_array.append(new_source)
        # Convert data to json
        print("[embedding api] Convert metadata to json...")
        updated_sources_json = json.dumps(updated_sources_array)
        metadata["sources"] = updated_sources_json
        # Update the collection with new metadata
        chroma_collection.modify(metadata=metadata)
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
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        # Create the index
        print("[embedding api] Creating index...")
        index = VectorStoreIndex.from_documents(
            collection_name=collection_name,
            ids=[document_name],  # id of input file
            client=db_client,
            documents=[documents[0]],  # just one file for now
            storage_context=storage_context,
            service_context=service_context,
            persist_directory=storage_directory,
            show_progress=True,
        )
        # Update new document's metadata
        for src_item in updated_sources_array:
            if src_item["name"] == document_name:
                # Mark this document as done
                src_item["processing"] = "complete"
                src_item["createdAt"] = created_at
                src_item["checksum"] = checksum
                metadata["sources"] = json.dumps(updated_sources_array)
                chroma_collection.modify(metadata=metadata)
                break
        # Done
        print(f"[embedding api] Finished embedding: {file_path} {index}")
        return True
    except Exception as e:
        msg = f"[embedding api] Embedding failed:\n{e}"
        print(msg)
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
    # You MUST get with the same embedding function you supplied while creating the collection.
    chroma_collection = db_client.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    # Create index from vector db
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        service_context=service_context,
    )
    return index
