import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

path = os.path.abspath("src/backends/inference/openllm")
sys.path.append(path)
from index import completions

app = FastAPI()


# Configure CORS settings
origins = [
    "http://localhost:3001",
    "https://hoppscotch.io",
]  # Add your frontend URL here
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_credentials=True,
    allow_methods=["GET", "POST"],
    # allow_headers=["*"],
)


# Load in the ai model to be used for inference.
@app.post("/api/text/v1/inference/load")
async def load_inference(data: dict):
    try:
        model_id: str = data["modelId"]
        # Logic to load the specified ai model here...
        return {"message": f"AI model [{model_id}] loaded."}
    except KeyError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON format: 'modelId' key not found"
        )


# Main text inference endpoint for prompting.
@app.post("/api/text/v1/inference/completions")
def run_completion(data: dict):
    return completions(data)


# Pre-process docs into a text format specified by user.
@app.post("/api/text/v1/embed/pre-process")
def pre_process_documents():
    return {"message": "pre_process_documents"}


# Create vector embeddings from the pre-processed documents, then store in database.
@app.post("/api/text/v1/embed/create")
def create_embeddings():
    return {"message": "create_embeddings"}


# Use Llama Index to run queries on vector database embeddings.
@app.post("/api/text/v1/search/similiar")
def search_similiar():
    return {"message": "search_similiar"}


# Return chat history messages.
@app.get("/api/text/v1/threads/get")
def get_threads():
    return {"message": "get_threads"}


# @app.post("/api/text/v1/inference/start")
# async def run_inference(data: dict):
#     try:
#         port: int = data["port"]
#         # Logic to start the inference server on the specified port here...
#         # Start the FastAPI server
#         subprocess.Popen(
#             ["uvicorn", "api.index:app", "--host", "127.0.0.1", "--port", {port}]
#         )
#         # OR
#         uvicorn.run(app, host='127.0.0.1', port=8000)
#         # Return affirmative response
#         return {"message": f"Inference server started on port {port}."}
#     except KeyError:
#         raise HTTPException(
#             status_code=400, detail="Invalid JSON format: 'port' key not found"
#         )
