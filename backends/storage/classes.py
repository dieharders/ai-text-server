from typing import List
from pydantic import BaseModel


class GetChatThreadResponse(BaseModel):
    success: bool
    message: str
    data: List[dict]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Returned chat messages.",
                    "success": True,
                    "data": {
                        "id": "06ufWDFiWDoWj92D50",
                        "createdAt": "Monday, January 21, 2012",
                        "title": "World's tallest buildings",
                        "summary": "A discussion about all the different buildings around the world that are the tallest.",
                        "numMessages": 1,
                        "messages": [
                            {
                                "id": "shdaDoWj92D501jaufWDFiW",
                                "content": "What is the tallest building in the world?",
                                "role": "user",
                                "createdAt": "Monday, January 21, 2012",
                                "order": 0,
                            }
                        ],
                    },
                }
            ]
        }
    }


class SaveChatThreadRequest(BaseModel):
    threadId: str
    thread: dict
