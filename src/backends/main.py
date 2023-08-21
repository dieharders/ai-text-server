import os
import re
import subprocess
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
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
global inference_process

# Configure CORS settings
origins = [
    "https://tauri.localhost",  # release version of origin
    "http://localhost:3000",  # for testing
    "https://hoppscotch.io",  # for testing
    "https://brain-dump-dieharders.vercel.app/",  # client app origin
]

text_inference_routes = [
    "/v1/completions",
    "/v1/embeddings",
    "/v1/chat/completions",
    "/v1/models",
]


# Redirect requests to external providers
@app.middleware("http")
async def redirect_middleware(request: Request, call_next):
    # Match route
    if request.url.path in text_inference_routes and request.url.port == PORT_API:
        # @TODO May need to adjust redirect url since in release origin == "tauri.localhost" since inference is on "localhost"
        print(f"Redirect match found: {request.url}")
        # Make new route with a different port
        pattern = r":([^/]+)"
        replacement = f":{PORT_TEXT_INFERENCE}"
        new_url_str = re.sub(pattern, replacement, str(request.url))
        # Remove "tauri."
        result_url_str = new_url_str.replace("tauri.", "")
        request.scope["path"] = result_url_str
        headers = dict(request.scope["headers"])
        # Set status code to determine Method when redirected
        # HTTP_303_SEE_OTHER for POST
        # HTTP_302_FOUND for GET
        # HTTP_307_TEMPORARY_REDIRECT should handle all
        # if request.method == "POST":
        #     status_code = status.HTTP_303_SEE_OTHER
        # else:
        #     status_code = status.HTTP_302_FOUND
        request.scope["headers"] = [(k, v) for k, v in headers.items()]
        return RedirectResponse(
            url=new_url_str,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Content-Type": "application/json"},
        )
    else:
        return await call_next(request)


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
        "success": True,
    }


# Load in the ai model to be used for inference.
@app.post("/api/text/v1/inference/load")
def load_inference(data: dict):
    try:
        model_id: str = data["modelId"]
        # Logic to load the specified ai model here...
        return {"message": f"AI model [{model_id}] loaded.", "success": True}
    except KeyError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON format: 'modelId' key not found"
        )


# Starts the text inference server
@app.post("/api/text/v1/inference/start")
def start_inference(data: dict):
    try:
        model_file_path: str = data["filePath"]
        isStarted = start_text_inference_server(model_file_path)
        return {"message": "AI inference started", "success": isStarted}
    except KeyError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON format: 'filePath' key not found"
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


def start_api_server():
    try:
        print("Starting API server...")
        # Start the ASGI server
        uvicorn.run(app, host="0.0.0.0", port=PORT_API, log_level="info")
        return True
    except:
        print("Failed to start API server")
        return False


def start_text_inference_server(file_path: str):
    try:
        print(f"Starting Inference server from: {file_path}")

        # curr_dir = os.getcwd()
        # model_filename = "llama-13b.ggmlv3.q3_K_S.bin"
        # path = os.path.join(curr_dir, f"models/{model_filename}").replace(
        #     "\\", "/"
        # )
        path = file_path.replace("\\", "/")

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
            path,
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
