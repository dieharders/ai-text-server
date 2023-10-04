import re
from fastapi import Request, status
from fastapi.responses import RedirectResponse

# These are direct api endpoints to the text inference engine
direct_routes = [
    "/v1/completions",
    "/v1/embeddings",
    "/v1/chat/completions",
    "/v1/models",
]


# Redirect requests to external providers
async def text(request: Request, call_next, PORT_TEXT_INFERENCE):
    def setRedirect(new_path: str):
        # Replace the port
        pattern = r":([^/]+)"
        replacement = f":{PORT_TEXT_INFERENCE}"
        new_url_str = re.sub(pattern, replacement, str(request.url))
        # Make new route with a different port
        request.scope["path"] = new_url_str
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

    # Match our custom routes and re-route it
    match request.url.path:
        case "/v1/text/completions":
            setRedirect("/v1/completions")
        case _:
            # Pass-through request
            return await call_next(request)
