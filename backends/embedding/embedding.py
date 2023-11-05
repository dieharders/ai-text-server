from llama_index import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    ServiceContext,
    LLMPredictor,
    load_index_from_storage,
)
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from llama_index.vector_stores import ChromaVectorStore
from llama_index.storage.storage_context import StorageContext
from llama_index.prompts import PromptTemplate
from llama_index.evaluation import FaithfulnessEvaluator  # ResponseEvaluator
import chromadb

# from llama_index.embeddings import HuggingFaceEmbedding


def create_embedding(file_path: str, storage_directory: str, collection_name: str, llm):
    try:
        # Define a specific embedding function
        # embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")

        # Load documents
        print(f"Load docs: {file_path}")
        documents = SimpleDirectoryReader(input_files=[file_path]).load_data()

        # Setup LLM
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

        # Create client and a new collection
        chroma_client = chromadb.Client()  # chromadb.EphemeralClient()
        chroma_collection = chroma_client.create_collection(collection_name)
        # Set up ChromaVectorStore and set as the storage service
        print("Setup chroma db")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        # Create embedding service
        llm_predictor = LLMPredictor(llm=llm)
        context_window = 3900
        llama_debug = LlamaDebugHandler(print_trace_on_end=True)
        callback_manager = CallbackManager([llama_debug])
        service_context = ServiceContext.from_defaults(
            embed_model="local",  # or embed_model
            llm_predictor=llm_predictor,
            context_window=context_window,
            callback_manager=callback_manager,
            chunk_size=512,  # TODO Is this limit working?
            chunk_overlap=20,
            chunk_size_limit=512,
        )
        # Create the index
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            service_context=service_context,
            show_progress=True,
        )
        # Persist the index to disk
        index.storage_context.persist(persist_dir=storage_directory)

        # Ask a question about data
        # response = query_embedding("Why does mass conservation break down?", index, llm)

        # Verify accuracy of response
        # verify_response(response, service_context)

        print(f"Finished embedding: {file_path}")
        return True
    except Exception as e:
        msg = f"Embedding failed:\n{e}"
        print(msg)
        raise Exception(msg)


# Determine which nodes contributed to the answer
def contributing_references(response, eval_result):
    num_source_nodes = len(response.source_nodes)
    print(f"Number of source nodes: {num_source_nodes}")
    print(f"Result is passing? {str(eval_result.passing)}")
    for s in response.source_nodes:
        print(f"Node Score: {s.score}")
        print(s.node.metadata)
    return {
        "num_refs": num_source_nodes,
    }


def verify_response(response, service_context):
    # Define evaluator, evaluates whether a response is faithful to the contexts
    print("Evaluating truthiness of response...")
    evaluator = FaithfulnessEvaluator(service_context=service_context)
    eval_result = evaluator.evaluate_response(response=response)
    # evaluator = ResponseEvaluator(service_context=service_context)
    # eval_result = evaluator.evaluate(query=query, response=response, contexts=[service_context])
    print(f"Truthy evaluation results: {eval_result}")
    contributing_references(response, eval_result)


def query_embedding(query, index, llm):
    # Query Data, note top_k is set to 3 so it will use the top 3 nodes it finds in vector index
    print("Query Data")
    llama_debug = LlamaDebugHandler(print_trace_on_end=True)
    callback_manager = CallbackManager([llama_debug])
    service_context = ServiceContext.from_defaults(
        llm=llm, embed_model="local", callback_manager=callback_manager
    )
    query_engine = index.as_query_engine(
        service_context=service_context,
        similarity_top_k=3,
        # streaming=True,
    )
    response = query_engine.query(query)
    print(f"Response from llamaIndex: {response}")
    return response


# Now you can load the index from disk when needed, and not rebuild it each time.
def load_embedding(llm, storage_directory):
    llama_debug = LlamaDebugHandler(print_trace_on_end=True)
    callback_manager = CallbackManager([llama_debug])
    # @TODO Do we need to define the chunk size?
    service_context = ServiceContext.from_defaults(
        llm=llm, chunk_size=512, embed_model="local", callback_manager=callback_manager
    )

    storage_context = StorageContext.from_defaults(persist_dir=storage_directory)
    index = load_index_from_storage(storage_context, service_context=service_context)

    return index
