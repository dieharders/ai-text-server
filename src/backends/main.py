# import os
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from inference import infer_text_api

# from llama_cpp.server.app import create_app
# from pydantic_settings import BaseSettings
import uvicorn

app = FastAPI(
    title="🍺 HomeBrew API server",
    version="0.0.1",
)
PORT_API = 8008
PORT_TEXT_INFERENCE = "8000"
inference_process = None

# Configure CORS settings
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://hoppscotch.io",
    "https://brain-dump-dieharders.vercel.app/",
]  # Add your frontend URL here
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Tell client we are ready to accept requests
@app.get("/api/connect")
def connect():
    return {
        "message": f"Connected to api server on port {PORT_API}. Refer to 'http://localhost:{PORT_API}/docs' for api docs.",
    }


# Load in the ai model to be used for inference.
@app.post("/api/text/v1/inference/load")
async def load_inference(data: dict):
    try:
        model_id: str = data["modelId"]
        # Logic to load the specified ai model here...
        return {"message": f"AI model [{model_id}] loaded.", "success": True}
    except KeyError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON format: 'modelId' key not found"
        )


# Starts the text inference server
@app.get("/api/text/v1/inference/start")
def start_inference():
    try:
        isStarted = start_text_inference_server()
        return {"message": "AI inference started", "success": isStarted}
    except:
        raise Exception(status_code=400, detail="Something went wrong...")


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


def start_api_server():
    try:
        print("Starting API server...")
        # Start the ASGI server
        uvicorn.run(app, host="0.0.0.0", port=PORT_API, log_level="info")
        return True
    except:
        print("Failed to start API server")
        return False


def start_text_inference_server():
    try:
        print("Starting Inference server")
        # curr_dir = os.getcwd()
        model_filename = "llama-13b.ggmlv3.q3_K_S.bin"
        # models_dir = os.path.join(curr_dir, "models")
        # model_dir = os.path.join(models_dir, model_filename)
        model_path = f"./src/backends/models/{model_filename}"

        # class Settings(BaseSettings):
        #     model: str
        #     alias_name: str
        #     n_ctx: int
        #     n_gpu_layers: int
        #     seed: int
        #     cache: bool
        #     cache_type: str
        #     verbose: bool

        # settings = Settings(
        #     model="models/llama-13b.ggmlv3.q3_K_S.bin",
        #     alias_name="Llama13b",
        #     n_ctx=512,
        #     n_gpu_layers=2,
        #     seed=-1,
        #     cache=True,
        #     cache_type="disk",
        #     verbose=True,
        # )

        # appInference = create_app(settings)
        # uvicorn.run(
        #     appInference,
        #     # host=os.getenv("HOST", "localhost"),
        #     host="0.0.0.0",
        #     # port=int(os.getenv("PORT", PORT_TEXT_INFERENCE)),
        #     port=PORT_TEXT_INFERENCE,
        #     log_level="info",
        # )

        # @TODO Pass all inference params to command
        # Command to execute
        serve_llama_cpp = [
            "python",
            "-m",
            "llama_cpp.server",
            "--host",
            "0.0.0.0",
            "--port",
            PORT_TEXT_INFERENCE,
            "--model",
            model_path,
        ]
        # Execute the command
        # Note, in llama_cpp/server/app.py -> `settings.model_name` needed changing to `settings.alias_name` due to namespace clash with Pydantic.
        inference_process = subprocess.Popen(serve_llama_cpp)
        # Can use `inference_process.terminate()` later to shutdown manually
        return True
    except:
        print("Failed to start Inference server")
        return False


if __name__ == "__main__":
    # Starts the text inference server
    # start_text_inference_server()
    # Starts the universal API server
    start_api_server()
