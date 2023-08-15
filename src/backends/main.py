from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from inference import infer_text_api
import uvicorn

app = FastAPI()
port = 8008

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


# Tell client we are ready to accept requests
@app.get("/api/connect")
def connect():
    return {
        "message": f"Connected to api server on port {port}. Refer to 'http://localhost:{port}/docs' for api docs.",
    }


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
    print("endpoint: /completions")
    return infer_text_api.completions(data)


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


def start_server():
    try:
        print("Starting FastAPI server...")
        # Start the ASGI server
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        return True
    except:
        print("Failed to start FastAPI server")
        return False


if __name__ == "__main__":
    start_server()
