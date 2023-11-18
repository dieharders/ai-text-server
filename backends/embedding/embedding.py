import os
import copy
import json
import chromadb
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
        path=storage_directory, settings=Settings(anonymized_telemetry=False)
    )


# Create a vector embedding for the given document.
def create_embedding(
    file_path: str,
    storage_directory: str,
    form,
    llm,
    db_client,
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
        # Load documents
        print(f"[embedding api] Load docs: {file_path}")
        documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
        # Create a new document embedding
        print("Find collection")
        collection_name: str = form.collection_name
        document_name: str = form.name
        description: str = form.description
        tags: str = form.tags
        # You MUST use the same embedding function to create as you do to get collection.
        chroma_collection = db_client.get_collection(collection_name)
        # Update collection metadata
        updated_sources_array = []
        updated_filePaths_array = []
        if "sources" in chroma_collection.metadata:
            print(f"@@@@@@@@@@@@@ I fart {chroma_collection}")
            sources_json = chroma_collection.metadata["sources"]
            sources_array = json.loads(sources_json)
            updated_sources_array = list(sources_array)  # copy
        if "filePaths" in chroma_collection.metadata:
            filePaths_json = chroma_collection.metadata["filePaths"]
            filePaths_array = json.loads(filePaths_json)
            updated_filePaths_array = list(filePaths_array)  # copy
        metadata = copy.deepcopy(chroma_collection.metadata)  # deepcopy
        metadata["description"] = description
        # Update tags @TODO Remove special chars, commas. Parse as string of space seperated words.
        metadata["tags"] = tags
        # Update sources (document ids)
        updated_sources_array.append(document_name)
        updated_sources_json = json.dumps(updated_sources_array)
        metadata["sources"] = updated_sources_json
        # Update sources paths (where original uploaded files are stored)
        updated_filePaths_array.append(file_path)
        updated_filePaths_json = json.dumps(updated_filePaths_array)
        metadata["filePaths"] = updated_filePaths_json
        # @TODO Update the "processing" attr for this document in the collection.metadata.processing array as "pending"
        # ...
        # Update the collection with new metadata
        chroma_collection.modify(metadata=metadata)

        # chroma_collection.add(
        #     documents=documents,
        #     metadatas=[
        #         {
        #             "name": document_name,
        #             "description": "",
        #             "tags": [],
        #             "file_path": file_path,
        #             "processing": "pending",
        #         }
        #     ],
        #     ids=[document_name],
        # )

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
        print("Creating index...")
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            service_context=service_context,
            show_progress=True,
        )
        # Save index to disk
        index.storage_context.persist(
            persist_dir=os.path.join(storage_directory, collection_name)
        )
        # @TODO Update the "processing" attr for this document in the collection.metadata.processing array as "complete"
        # @TODO Update document's metadata
        # Done
        print(f"Finished embedding: {file_path}")
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
