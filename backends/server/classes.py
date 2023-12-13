from pydantic import BaseModel
from typing import List, Optional


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
                    "data": {"docs": "http://localhost:8008/docs"},
                }
            ]
        }
    }


# Load in the ai model to be used for inference.
class LoadInferenceRequest(BaseModel):
    modelId: str
    pathToModel: str
    textModelConfig: dict

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "modelId": "llama-2-13b-chat-ggml",
                    "pathToModel": "C:\\homebrewai-app\\models\\llama-2-13b.GGUF",
                    "textModelConfig": {
                        "promptTemplate": "Instructions:{{PROMPT}}\n\n### Response:",
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
                    },
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
    prompt: str
    collectionNames: Optional[List[str]] = []
    mode: Optional[str] = "completion"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "Why does mass conservation break down?",
                    "collectionNames": ["science"],
                    "mode": "completion",
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
# class StartInferenceRequest(BaseModel):
#     modelConfig: dict

#     model_config = {
#         "json_schema_extra": {
#             "examples": [
#                 {
#                     "modelConfig": {
#                         "promptTemplate": "Instructions:{{PROMPT}}\n\n### Response:",
#                         "savePath": "C:\\Project Files\\brain-dump-ai\\models\\llama-2-13b-chat.ggmlv3.q2_K.bin",
#                         "id": "llama2-13b",
#                         "numTimesRun": 0,
#                         "isFavorited": False,
#                         "validation": "success",
#                         "modified": "Tue, 19 Sep 2023 23:25:28 GMT",
#                         "size": 1200000,
#                         "endChunk": 13,
#                         "progress": 67,
#                         "tokenizerPath": "/some/path/to/tokenizer",
#                         "checksum": "90b27795b2e319a93cc7c3b1a928eefedf7bd6acd3ecdbd006805f7a028ce79d",
#                     },
#                 }
#             ]
#         }
#     }


# class StartInferenceResponse(BaseModel):
#     success: bool
#     message: str
#     data: dict

#     model_config = {
#         "json_schema_extra": {
#             "examples": [
#                 {
#                     "success": True,
#                     "message": "AI text inference started.",
#                     "data": {
#                         "port": 8080,
#                         "docs": "http://localhost:8080/docs",
#                         "textModelConfig": {
#                             "promptTemplate": "Instructions:{{PROMPT}}\n\n### Response:",
#                             "savePath": "C:\\Project Files\\brain-dump-ai\\models\\llama-2-13b-chat.ggmlv3.q2_K.bin",
#                             "id": "llama2-13b",
#                             "numTimesRun": 0,
#                             "isFavorited": False,
#                             "validation": "success",
#                             "modified": "Tue, 19 Sep 2023 23:25:28 GMT",
#                             "size": 1200000,
#                             "endChunk": 13,
#                             "progress": 67,
#                             "tokenizerPath": "/some/path/to/tokenizer",
#                             "checksum": "90b27795b2e319a93cc7c3b1a928eefedf7bd6acd3ecdbd006805f7a028ce79d",
#                         },
#                     },
#                 }
#             ]
#         }
#     }
