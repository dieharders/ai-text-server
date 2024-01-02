from pydantic import BaseModel
from typing import List, Optional
from fastapi import Query


class PingResponse(BaseModel):
    success: bool
    message: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "pong",
                }
            ]
        }
    }


class ConnectResponse(BaseModel):
    success: bool
    message: str
    data: dict

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Connected to api server on port 8008.",
                    "data": {
                        "docs": "http://localhost:8008/docs",
                        "version": "0.2.0",
                    },
                }
            ]
        }
    }


# Load in the ai model to be used for inference.
class LoadInferenceRequest(BaseModel):
    modelId: str  # used to find the model config
    # __init__ args - https://llama-cpp-python.readthedocs.io/en/latest/api-reference/
    n_gpu_layers: Optional[int] = 0  # 32 for our purposes
    use_mmap: Optional[bool] = True
    use_mlock: Optional[bool] = False
    f16_kv: Optional[bool] = True
    seed: Optional[int] = 1337
    n_ctx: Optional[int] = 512  # 3900 for llama2
    n_batch: Optional[int] = 512
    n_threads: Optional[int] = None
    offload_kqv: Optional[bool] = False
    verbose: Optional[bool] = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "modelId": "llama-2-13b-chat-ggml",
                    "n_gpu_layers": 0,
                    "use_mmap": True,
                    "use_mlock": False,
                    "f16_kv": True,
                    "seed": 1337,
                    "n_ctx": 512,
                    "n_batch": 512,
                    "n_threads": None,
                    "offload_kqv": False,
                    "verbose": False,
                }
            ]
        }
    }


class LoadInferenceResponse(BaseModel):
    message: str
    success: bool

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "AI model [llama-2-13b-chat-ggml] loaded.",
                    "success": True,
                }
            ]
        }
    }


class ServicesApiResponse(BaseModel):
    success: bool
    message: str
    data: List[dict]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "These are api params for accessing services endpoints.",
                    "data": [
                        {
                            "name": "textInference",
                            "port": 8008,
                            "endpoints": [
                                {
                                    "name": "completions",
                                    "urlPath": "/v1/completions",
                                    "method": "POST",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
    }


class InferenceRequest(BaseModel):
    # homebrew server specific args
    collectionNames: Optional[List[str]] = []
    mode: Optional[str] = "completion"
    # __call__ args
    prompt: str
    # messages: Optional[List[str]] = None
    stream: Optional[bool] = True
    # suffix: Optional[str] = ""
    temperature: Optional[float] = 0.0  # precise
    max_tokens: Optional[
        int
    ] = 128  # this should prob be a factor (ctx/8) of the context window. Providing a few back and forth convo before limit is reached.
    stop: Optional[List[str]] = [
        # "\n",
        # "###",
        "[DONE]",
    ]  # A list of strings to stop generation when encountered
    echo: Optional[bool] = False
    model: Optional[
        str
    ] = "local"  # The name to use for the model in the completion object
    grammar: Optional[dict] = None  # A grammar to use for constrained sampling
    mirostat_tau: Optional[
        float
    ] = 5.0  # A higher value corresponds to more surprising or less predictable text, while a lower value corresponds to less surprising or more predictable text.
    tfs_z: Optional[
        float
    ] = 1.0  # Tail Free Sampling - https://www.trentonbricken.com/Tail-Free-Sampling/
    top_k: Optional[int] = 40
    top_p: Optional[float] = 0.95
    min_p: Optional[float] = 0.05
    seed: Optional[int] = 1337
    repeat_penalty: Optional[float] = 1.1
    presence_penalty: Optional[
        float
    ] = 0.0  # The penalty to apply to tokens based on their presence in the prompt
    frequency_penalty: Optional[
        float
    ] = 0.0  # The penalty to apply to tokens based on their frequency in the prompt

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "Why does mass conservation break down?",
                    "collectionNames": ["science"],
                    # Settings
                    "mode": "completion",  # completion | chat
                    "stream": True,
                    "temperature": 0.2,
                    "max_tokens": 1024,
                    "stop": ["###", "[DONE]"],
                    "echo": False,
                    "model": "llama2",
                    "seed": 1337,
                    "top_k": 40,
                    "top_p": 0.7,
                    "repeat_penalty": 1.0,
                }
            ]
        }
    }


class InferenceResponse(BaseModel):
    success: bool
    message: str
    data: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Successfull text inference",
                    "success": True,
                    "data": "This is a response.",
                }
            ]
        }
    }


class PreProcessRequest(BaseModel):
    document_id: Optional[str] = ""
    document_name: str
    collection_name: str
    description: Optional[str] = ""
    tags: Optional[str] = ""
    filePath: str


class PreProcessResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, str]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Successfully processed file",
                    "success": True,
                    "data": {
                        "document_id": "1010-1010",
                        "file_name": "filename.md",
                        "path_to_file": "C:\\app_data\\parsed",
                        "checksum": "xxx",
                    },
                }
            ]
        }
    }


class AddCollectionRequest(BaseModel):
    collectionName: str
    description: Optional[str] = ""
    tags: Optional[str] = List[None]


class AddCollectionResponse(BaseModel):
    success: bool
    message: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Successfully created new collection",
                    "success": True,
                }
            ]
        }
    }


class AddDocumentRequest(BaseModel):
    documentName: str
    collectionName: str
    description: Optional[str] = ""
    tags: Optional[str] = ""
    urlPath: Optional[str] = ""


class AddDocumentResponse(BaseModel):
    success: bool
    message: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "A new memory has been added",
                    "success": True,
                }
            ]
        }
    }


class GetAllCollectionsResponse(BaseModel):
    success: bool
    message: str
    data: list

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Returned 5 collection(s)",
                    "success": True,
                    "data": [
                        {
                            "name": "collection-name",
                            "id": "1010-10101",
                            "metadata": {
                                "description": "A description.",
                                "sources": ["document-id"],
                                "tags": "html5 react",
                            },
                        }
                    ],
                }
            ]
        }
    }


class GetCollectionRequest(BaseModel):
    id: str
    include: Optional[List[str]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "examples",
                    "include": ["embeddings", "documents"],
                }
            ]
        }
    }


class GetCollectionResponse(BaseModel):
    success: bool
    message: str
    data: dict

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Returned 5 source(s) in collection",
                    "success": True,
                    "data": {
                        "collection": {},
                        "numItems": 5,
                    },
                }
            ]
        }
    }


class GetDocumentRequest(BaseModel):
    collection_id: str
    document_ids: List[str]
    include: Optional[List[str]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "collection_id": "examples",
                    "document_ids": ["science"],
                    "include": ["embeddings", "documents"],
                }
            ]
        }
    }


class GetDocumentResponse(BaseModel):
    success: bool
    message: str
    data: List[dict]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Returned 1 document(s)",
                    "success": True,
                    "data": [{}],
                }
            ]
        }
    }


class FileExploreRequest(BaseModel):
    filePath: str


class FileExploreResponse(BaseModel):
    success: bool
    message: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Opened file explorer",
                    "success": True,
                }
            ]
        }
    }


class UpdateDocumentRequest(BaseModel):
    collectionName: str
    documentName: str
    documentId: str
    urlPath: Optional[str] = ""
    filePath: Optional[str] = ""
    metadata: Optional[dict] = {}


class UpdateDocumentResponse(BaseModel):
    success: bool
    message: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Updated memories",
                    "success": True,
                }
            ]
        }
    }


class DeleteDocumentsRequest(BaseModel):
    collection_id: str
    document_ids: List[str]


class DeleteDocumentsResponse(BaseModel):
    success: bool
    message: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Removed 1 document(s)",
                    "success": True,
                }
            ]
        }
    }


class DeleteCollectionRequest(BaseModel):
    collection_id: str


class DeleteCollectionResponse(BaseModel):
    success: bool
    message: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Removed collection",
                    "success": True,
                }
            ]
        }
    }


class WipeMemoriesResponse(BaseModel):
    success: bool
    message: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Removed all memories",
                    "success": True,
                }
            ]
        }
    }


class SaveSettingsRequest(BaseModel):
    data: dict


class GenericEmptyResponse(BaseModel):
    success: bool
    message: str
    data: None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "This is a message",
                    "success": True,
                    "data": None,
                }
            ]
        }
    }


class Text_Model_Metadata(BaseModel):
    savePath: str
    id: str
    numTimesRun: int
    isFavorited: bool
    validation: str
    modified: str
    size: int
    endChunk: int
    progress: int
    tokenizerPath: str
    checksum: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "savePath": "C:\\Project Files\\brain-dump-ai\\models\\llama-2-13b-chat.ggmlv3.q2_K.bin",
                    "id": "llama2-13b",
                    "numTimesRun": 0,
                    "isFavorited": False,
                    "validation": "success",
                    "modified": "Tue, 19 Sep 2023 23:25:28 GMT",
                    "size": 1200000,
                    "endChunk": 13,
                    "progress": 67,
                    "tokenizerPath": "/some/path/to/tokenizer",
                    "checksum": "90b27795b2e319a93cc7c3b1a928eefedf7bd6acd3ecdbd006805f7a028ce79d",
                }
            ]
        }
    }


class Text_Model_Metadatas(BaseModel):
    current_text_model: str
    current_download_path: str
    installed_text_models: Text_Model_Metadata

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "current_text_model": "llama-2-13b-chat",
                    "current_download_path": "C:\\Users\\cybro\\Downloads\\llama-2-13b-chat.Q4_K_M.gguf",
                    "installed_text_models": [
                        {
                            "id": "llama-2-13b-chat",
                            "savePath": "C:\\Users\\cybro\\Downloads\\llama-2-13b-chat.Q4_K_M.gguf",
                            "numTimesRun": 0,
                            "isFavorited": False,
                            "validation": "success",
                            "modified": "Mon, 13 Nov 2023 13:02:52 GMT",
                            "size": 7865956224,
                            "endChunk": 1,
                            "progress": 100,
                            "tokenizerPath": "",
                            "checksum": "7ddfe27f61bf994542c22aca213c46ecbd8a624cca74abff02a7b5a8c18f787f",
                        }
                    ],
                }
            ]
        }
    }


class Model_Config(BaseModel):
    id: str
    name: str
    type: str
    provider: str
    licenses: List[str]
    description: str
    fileSize: float
    fileName: str
    modelType: str
    modelUrl: str
    context_window: int
    quantTypes: List[str]
    downloadUrl: str
    sha256: str
    promptTemplate: str
    systemPrompt: str


# This is a combination of model config and metadata
class Text_Model_Install_Settings(BaseModel):
    id: str
    name: str
    savePath: str
    size: int
    type: str
    ownedBy: str
    permissions: List[str]
    promptTemplate: str
    systemPrompt: str
    n_ctx: int


class Text_Model_Install_Settings_Response(BaseModel):
    success: bool
    message: str
    data: List[Text_Model_Install_Settings]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Success",
                    "data": [
                        {
                            "id": "llama-2-13b-chat",
                            "name": "llama2",
                            "savePath": "C:\\Users\\cybro\\Downloads\\llama-2-13b-chat.Q4_K_M.gguf",
                            "size": 7865956224,
                            "type": "llama",
                            "ownedBy": "Meta",
                            "permissions": ["MIT"],
                            "promptTemplate": "Instructions:{{PROMPT}}\n\n### Response:",
                            "systemPrompt": "You are an AI assistant that answers questions in a friendly manner",
                            "n_ctx": 3900,
                        }
                    ],
                }
            ]
        }
    }


class Text_Model_Response(BaseModel):
    success: bool
    message: str
    data: Text_Model_Install_Settings

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Success",
                    "data": {
                        "id": "llama-2-13b-chat",
                        "name": "llama2",
                        "savePath": "C:\\Users\\cybro\\Downloads\\llama-2-13b-chat.Q4_K_M.gguf",
                        "size": 7865956224,
                        "type": "llama",
                        "ownedBy": "Meta",
                        "permissions": ["MIT"],
                        "promptTemplate": "Instructions:{{PROMPT}}\n\n### Response:",
                        "systemPrompt": "You are an AI assistant that answers questions in a friendly manner",
                        "n_ctx": 3900,
                    },
                }
            ]
        }
    }
