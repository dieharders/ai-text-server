from fastapi import APIRouter, Request
from server import classes

router = APIRouter()


# Return api info for available services
@router.get("/api")
def get_services_api(request: Request) -> classes.ServicesApiResponse:
    app = request.app
    data = []

    # Return text inference services available from Homebrew
    text_inference_api = {
        "name": "textInference",
        "port": app.state.PORT_HOMEBREW_API,
        "endpoints": [
            {
                "name": "inference",
                "urlPath": "/v1/text/inference",
                "method": "POST",
                "promptTemplate": app.state.text_model_config["promptTemplate"],
            },
            # Return the currently loaded model and its settings
            {
                "name": "models",
                "urlPath": "/v1/text/models",
                "method": "GET",
            },
            # llama.cpp offers native embedding
            {
                "name": "embedding",
                "urlPath": "/v1/text/embedding",
                "method": "POST",
            },
            # Structured Data Extraction
            {
                "name": "extraction",
                "urlPath": "/v1/text/extraction",
                "method": "POST",
            },
            # Function Calling
            {
                "name": "functions",
                "urlPath": "/v1/text/functions",
                "method": "POST",
            },
            # Vision to Text (llama.cpp uses LLaVa but BakLLaVa is another option)
            {
                "name": "vision",
                "urlPath": "/v1/text/vision",
                "method": "POST",
            },
            # Code completion via Copilot
            {
                "name": "copilot",
                "urlPath": "/v1/text/copilot",
                "method": "POST",
            },
        ],
    }
    data.append(text_inference_api)

    # Return services that are ready now
    memory_api = {
        "name": "memory",
        "port": app.state.PORT_HOMEBREW_API,
        "endpoints": [
            {
                "name": "addCollection",
                "urlPath": "/v1/memory/addCollection",
                "method": "GET",
            },
            {
                "name": "getAllCollections",
                "urlPath": "/v1/memory/getAllCollections",
                "method": "GET",
            },
            {
                "name": "getCollection",
                "urlPath": "/v1/memory/getCollection",
                "method": "POST",
            },
            {
                "name": "deleteCollection",
                "urlPath": "/v1/memory/deleteCollection",
                "method": "GET",
            },
            {
                "name": "addDocument",
                "urlPath": "/v1/memory/addDocument",
                "method": "POST",
            },
            {
                "name": "getDocument",
                "urlPath": "/v1/memory/getDocument",
                "method": "POST",
            },
            {
                "name": "deleteDocuments",
                "urlPath": "/v1/memory/deleteDocuments",
                "method": "POST",
            },
            {
                "name": "fileExplore",
                "urlPath": "/v1/memory/fileExplore",
                "method": "GET",
            },
            {
                "name": "updateDocument",
                "urlPath": "/v1/memory/updateDocument",
                "method": "POST",
            },
            {
                "name": "wipe",
                "urlPath": "/v1/memory/wipe",
                "method": "GET",
            },
        ],
    }
    data.append(memory_api)

    return {
        "success": True,
        "message": "These are the currently available service api's",
        "data": data,
    }
