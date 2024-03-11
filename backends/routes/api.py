from fastapi import APIRouter, Request
from server import classes
from embedding.embedding import CHUNKING_STRATEGIES
from llama_index.response_synthesizers import ResponseMode

router = APIRouter()


# Return api info for available services
@router.get("/api")
def get_services_api(request: Request) -> classes.ServicesApiResponse:
    app = request.app
    data = []
    rag_response_modes = list(ResponseMode.__members__.values())

    # Return text inference services
    text_inference_api = {
        "name": "textInference",
        "port": app.state.PORT_HOMEBREW_API, # @TODO Remove this as we will be using static port
        "configs": {
            "ragResponseModes": rag_response_modes,
        },
        "endpoints": [
            # Generate a text response from Ai engine
            {
                "name": "inference",  # @TODO Change to "generate" ?
                "urlPath": "/v1/text/inference",
                "method": "POST",
            },
            # Load the specified Ai model into memory
            {
                "name": "load",
                "urlPath": "/v1/text/load",
                "method": "POST",
            },
            # Eject the currently loaded Ai model from memory
            {
                "name": "unload",
                "urlPath": "/v1/text/unload",
                "method": "POST",
            },
            # Return the currently loaded model and its settings
            {
                "name": "model",
                "urlPath": "/v1/text/model",
                "method": "GET",
            },
            # Return a list of all currently installed models and their metadata
            {
                "name": "installed",
                "urlPath": "/v1/text/installed",
                "method": "GET",
            },
            # Open the directory of installed models
            {
                "name": "modelExplore",
                "urlPath": "/v1/text/modelExplore",
                "method": "GET",
            },
            # llama.cpp offers native embedding too
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

    # Return persistent file storage services
    storage_api = {
        "name": "storage",
        "port": app.state.PORT_HOMEBREW_API,
        "endpoints": [
            # Load Playground settings
            {
                "name": "getPlaygroundSettings",
                "urlPath": "/v1/persist/playground-settings",
                "method": "GET",
            },
            # Save Playground settings
            {
                "name": "savePlaygroundSettings",
                "urlPath": "/v1/persist/playground-settings",
                "method": "POST",
            },
            # Load bot settings
            {
                "name": "getBotSettings",
                "urlPath": "/v1/persist/bot-settings",
                "method": "GET",
            },
            # Save bot settings
            {
                "name": "saveBotSettings",
                "urlPath": "/v1/persist/bot-settings",
                "method": "POST",
            },
        ],
    }
    data.append(storage_api)

    # Return search over local files services
    memory_api = {
        "name": "memory",
        "port": app.state.PORT_HOMEBREW_API,
        "configs": {
            "chunkingStrategies": list(CHUNKING_STRATEGIES.keys()),
        },
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
