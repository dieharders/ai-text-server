# imports
from llama_index import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.vector_stores import ChromaVectorStore
from llama_index.storage.storage_context import StorageContext
from llama_index.embeddings import HuggingFaceEmbedding
import chromadb


def create(file_path: str):
    try:
        # Create client and a new collection
        chroma_client = chromadb.EphemeralClient()
        chroma_collection = chroma_client.create_collection("relativity")

        # Define embedding function
        embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")

        # Load documents
        print(f"Load docs: {file_path}")
        documents = SimpleDirectoryReader(input_files=[file_path]).load_data()

        # Set up ChromaVectorStore and load in data
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        service_context = ServiceContext.from_defaults(embed_model=embed_model)
        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context, service_context=service_context
        )

        # Query Data
        query_engine = index.as_query_engine()
        response = query_engine.query("Why does mass conservation break down?")
        print(f"Response from llamaIndex: {response}")

        return response
    except:
        print("Embedding failed")
        return None
