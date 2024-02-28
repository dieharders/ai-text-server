from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

DEFAULT_TEMPERATURE = 0.2
DEFAULT_CONTEXT_WINDOW = 2000
DEFAULT_SEED = 1337
DEFAULT_MAX_TOKENS = 0  # 0 means we should calc it
DEFAULT_CHAT_MODE = "instruct"

class CHAT_MODES(Enum):
    INSTRUCT = "instruct"
    CHAT = "chat"
    SLIDING = "sliding"

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


class LoadTextInferenceInit(BaseModel):
    n_gpu_layers: Optional[int] = 0  # 32 for our purposes
    use_mmap: Optional[bool] = True
    use_mlock: Optional[bool] = False
    f16_kv: Optional[bool] = True
    seed: Optional[int] = DEFAULT_SEED
    n_ctx: Optional[int] = DEFAULT_CONTEXT_WINDOW
    n_batch: Optional[int] = 512
    n_threads: Optional[int] = None
    offload_kqv: Optional[bool] = False
    verbose: Optional[bool] = False


class LoadTextInferenceCall(BaseModel):
    stream: Optional[bool] = True
    stop: Optional[List[str]] = []
    echo: Optional[bool] = False
    model: Optional[str] = "local"
    mirostat_tau: Optional[float] = 5.0
    tfs_z: Optional[float] = 1.0
    top_k: Optional[int] = 40
    top_p: Optional[float] = 0.95
    min_p: Optional[float] = 0.05
    repeat_penalty: Optional[float] = 1.1
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    temperature: Optional[float] = DEFAULT_TEMPERATURE
    grammar: Optional[dict] = None
    max_tokens: Optional[int] = DEFAULT_MAX_TOKENS


# Load in the ai model to be used for inference
class LoadInferenceRequest(BaseModel):
    modelPath: str
    modelId: str
    mode: Optional[str] = DEFAULT_CHAT_MODE
    # __init__ args - https://llama-cpp-python.readthedocs.io/en/latest/api-reference/
    init: LoadTextInferenceInit
    # __call__ args
    call: LoadTextInferenceCall

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "modelPath": "C:\\Users\\user\\Downloads\\llama-2-13b-chat.Q4_K_M.gguf",
                    "modelId": "llama-2-13b-chat-ggml",
                    "mode": DEFAULT_CHAT_MODE,
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


class RagTemplateData(BaseModel):
    id: str
    name: str
    text: str
    type: Optional[str] = None


class InferenceRequest(BaseModel):
    # __init__ args
    n_ctx: Optional[int] = DEFAULT_CONTEXT_WINDOW
    seed: Optional[int] = DEFAULT_SEED
    # homebrew server specific args
    collectionNames: Optional[List[str]] = []
    mode: Optional[str] = DEFAULT_CHAT_MODE
    systemMessage: Optional[str] = None
    messageFormat: Optional[str] = None
    promptTemplate: Optional[str] = None
    ragPromptTemplate: Optional[RagTemplateData] = None
    # __call__ args
    prompt: str
    messages: Optional[List[str]] = None
    stream: Optional[bool] = True
    # suffix: Optional[str] = ""
    temperature: Optional[float] = 0.0  # precise
    max_tokens: Optional[int] = DEFAULT_MAX_TOKENS
    stop: Optional[
        List[str]
    ] = []  # A list of strings to stop generation when encountered
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
    repeat_penalty: Optional[float] = 1.1
    presence_penalty: Optional[
        float
    ] = 0.0  # The penalty to apply to tokens based on their presence in the prompt
    frequency_penalty: Optional[
        float
    ] = 0.0  # The penalty to apply to tokens based on their frequency in the prompt
    similarity_top_k: Optional[int] = None
    response_mode: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "Why does mass conservation break down?",
                    "collectionNames": ["science"],
                    "mode": DEFAULT_CHAT_MODE,
                    "systemMessage": "You are a helpful Ai assistant.",
                    "messageFormat": "<system> {system_message}\n<user> {prompt}",
                    "promptTemplate": "Answer this question: {query_str}",
                    "ragPromptTemplate": {
                        "id": "summary",
                        "name": "Summary",
                        "text": "This is a template: {query_str}",
                    },
                    "messages": [
                        {"role": "user", "content": "What is meaning of life?"}
                    ],
                    # Settings
                    "stream": True,
                    "temperature": 0.2,
                    "max_tokens": 1024,
                    "n_ctx": 2000,
                    "stop": ["###", "[DONE]"],
                    "echo": False,
                    "model": "llama2",
                    "grammar": None,
                    "mirostat_tau": 5.0,
                    "tfs_z": 1.0,
                    "top_k": 40,
                    "top_p": 0.95,
                    "min_p": 0.05,
                    "seed": 1337,
                    "repeat_penalty": 1.1,
                    "presence_penalty": 0.0,
                    "frequency_penalty": 0.0,
                    "similarity_top_k": 1,
                    "response_mode": "compact",
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


class EmbedDocumentRequest(BaseModel):
    collectionName: str
    documentName: str
    description: Optional[str] = ""
    tags: Optional[str] = ""
    urlPath: Optional[str] = ""
    chunkSize: Optional[int] = None
    chunkOverlap: Optional[int] = None
    chunkStrategy: Optional[str] = None


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


class UpdateEmbeddedDocumentRequest(EmbedDocumentRequest):
    documentId: str
    filePath: Optional[str] = ""
    metadata: Optional[dict]  # @TODO What data struct ?


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


# @TODO Extend from LoadTextInferenceInit
class AppSettingsInitData(BaseModel):
    preset: Optional[str] = None
    n_ctx: Optional[int] = None
    seed: Optional[int] = None
    n_threads: Optional[int] = None
    n_batch: Optional[int] = None
    offload_kqv: Optional[bool] = None
    n_gpu_layers: Optional[int] = None
    f16_kv: Optional[bool] = None
    use_mlock: Optional[bool] = None
    use_mmap: Optional[bool] = None
    verbose: Optional[bool] = None


class AppSettingsCallData(BaseModel):
    preset: Optional[float] = None
    systemMessage: Optional[str] = None
    promptTemplate: Optional[str] = None
    ragPromptTemplate: Optional[RagTemplateData] = None
    temperature: Optional[float] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    stop: Optional[List[str]] = []
    max_tokens: Optional[int] = None
    repeat_penalty: Optional[float] = None
    stream: Optional[bool] = None
    echo: Optional[bool] = None
    similarity_top_k: Optional[int] = None
    response_mode: Optional[str] = None
    # Yet to be used params
    # model: str = None
    # mirostat_tau: float = None
    # tfs_z: float = None
    # min_p: float = None
    # presence_penalty: float = None
    # frequency_penalty: float = None
    # grammar: dict = None


class AttentionSettings(BaseModel):
    mode: str = None

class PerformanceSettings(BaseModel):
  n_gpu_layers: int = None
  use_mlock: bool = None
  seed: int = None
  n_ctx: int = None
  n_batch: int = None
  n_threads: int = None
  offload_kqv: bool = None
  chat_format: str = None
  f16_kv: bool = None

class SystemSettings(BaseModel):
  systemMessage: str = None
  systemMessageName: str = None

class ModelSettings(BaseModel):
  id: str = None
  botName: str = None

class PromptSettings(BaseModel):
  promptTemplate: dict = None
  ragTemplate: dict = None
  ragMode: dict = None

class KnowledgeSettings(BaseModel):
  type: str = None
  index: List[str] = None

class ResponseSettings(BaseModel):
  temperature: float = None
  max_tokens: int = None
  top_p: float = None
  echo: bool = None
  stop: List[str] = []
  repeat_penalty: float = None
  top_k: int = None
  stream: bool = None


class BotSettings(BaseModel):
    attention: AttentionSettings = None
    performance: PerformanceSettings = None
    system: SystemSettings = None
    model: ModelSettings = None
    prompt: PromptSettings = None
    knowledge: KnowledgeSettings = None
    response: ResponseSettings = None

class BotSettingsResponse(BaseModel):
    success: bool
    message: str
    data: List[BotSettings] = None


class GetPlaygroundSettingsResponse(BaseModel):
    success: bool
    message: str
    data: Optional[BotSettings] = None


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


class InstalledTextModelMetadata(BaseModel):
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


class InstalledTextModel(BaseModel):
    current_download_path: str
    installed_text_models: List[InstalledTextModelMetadata]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "current_download_path": "C:\\Users\\user\\Downloads\\llama-2-13b-chat.Q4_K_M.gguf",
                    "installed_text_models": [
                        {
                            "id": "llama-2-13b-chat",
                            "savePath": "C:\\Users\\user\\Downloads\\llama-2-13b-chat.Q4_K_M.gguf",
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


class ModelConfig(BaseModel):
    id: str
    name: Optional[str] = None
    type: Optional[str] = None
    provider: Optional[str] = None
    licenses: Optional[List[str]] = None
    description: Optional[str] = None
    fileSize: Optional[float] = None
    fileName: str
    modelType: Optional[str] = None
    modelUrl: Optional[str] = None
    context_window: Optional[int] = None
    quantTypes: Optional[List[str]] = None
    downloadUrl: str
    sha256: Optional[str] = None


# This is a combination of model config and metadata
class TextModelInstallMetadata(BaseModel):
    id: Optional[str] = None
    savePath: Optional[str] = None
    numTimesRun: Optional[int] = None
    isFavorited: Optional[bool] = None
    validation: Optional[str] = None
    modified: Optional[str] = None
    size: Optional[int] = None
    endChunk: Optional[int] = None
    progress: Optional[float] = None
    tokenizerPath: Optional[str] = None
    checksum: Optional[str] = None


class TextModelInstallMetadataResponse(BaseModel):
    success: bool
    message: str
    data: List[TextModelInstallMetadata]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Success",
                    "data": [
                        {
                            "id": "llama-2-13b-chat",
                            "savePath": "C:\\Users\\user\\Downloads\\llama-2-13b-chat.Q4_K_M.gguf",
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


class InstalledTextModelResponse(BaseModel):
    success: bool
    message: str
    data: TextModelInstallMetadata

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Success",
                    "data": {
                        "id": "llama-2-13b-chat",
                        "savePath": "C:\\Users\\user\\Downloads\\llama-2-13b-chat.Q4_K_M.gguf",
                        "numTimesRun": 0,
                        "isFavorited": False,
                        "validation": "success",
                        "modified": "Mon, 13 Nov 2023 13:02:52 GMT",
                        "size": 7865956224,
                        "endChunk": 1,
                        "progress": 100,
                        "tokenizerPath": "",
                        "checksum": "7ddfe27f61bf994542c22aca213c46ecbd8a624cca74abff02a7b5a8c18f787f",
                    },
                }
            ]
        }
    }


class ContextRetrievalOptions(BaseModel):
    response_mode: Optional[str] = None
    similarity_top_k: Optional[int] = None
