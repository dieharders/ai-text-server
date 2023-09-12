from fastapi import HTTPException


def completions(data):
    try:
        prompt: str = data["prompt"]
        # Logic to get completion task result from ai
        return {"message": f"openllm completing prompt [{prompt}] ..."}
    except KeyError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON format: 'prompt' key not found"
        )
