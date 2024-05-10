import os
import signal
import sys
import threading
import uvicorn
import webbrowser
import httpx
import socket
import pyqrcode
import tkinter as tk
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    Request,
    APIRouter,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from embeddings import storage
from core import common, classes
from services.route import router as services
from embeddings.route import router as embeddings
from inference.route import router as text_inference
from settings.route import router as settings


server_info = None
api_version = "0.5.0"
SERVER_PORT = 8008
# Display where the admin can use the web UI
openbrew_studio_url = "https://studio.openbrewai.com"


# Parse runtime arguments passed to script
def parse_runtime_args():
    # Command-line arguments are accessed via sys.argv
    arguments = sys.argv[1:]
    # Initialize variables to store parsed arguments
    mode = None
    # Iterate through arguments and parse them
    for arg in arguments:
        if arg.startswith("--mode="):
            mode = arg.split("=")[1]
    return mode


# Check what env is running - prod/dev
build_env = parse_runtime_args()
is_debug = hasattr(sys, "gettrace") and sys.gettrace() is not None
is_dev = build_env == "dev" or is_debug
is_prod = build_env == "prod" or not is_dev
# Comment out if you want to debug on prod build
if is_prod:
    # Remove prints in prod when deploying in window mode
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

# Path to the .env file in the parent directory
current_directory = os.path.dirname(os.path.abspath(__file__))
parent_directory = os.path.dirname(current_directory)
env_path = os.path.join(parent_directory, ".env")
load_dotenv(env_path)


@asynccontextmanager
async def lifespan(application: FastAPI):
    print(f"{common.PRNT_API} Lifespan startup", flush=True)
    # https://www.python-httpx.org/quickstart/
    app.requests_client = httpx.Client()
    # Initialize global data here
    application.state.PORT_HOMEBREW_API = SERVER_PORT
    application.state.db_client = None
    application.state.llm = None  # Set each time user loads a model
    application.state.path_to_model = ""  # Set each time user loads a model
    application.state.model_id = ""
    application.state.embed_model = None
    app.state.loaded_text_model_data = {}
    app.state.is_prod = is_prod
    app.state.is_dev = is_dev
    app.state.is_debug = is_debug

    yield
    # Do shutdown cleanup here...
    print(f"{common.PRNT_API} Lifespan shutdown")


app = FastAPI(title="Obrew🍺Server", version=api_version, lifespan=lifespan)

# Get paths for SSL certificate
SSL_KEY: str = common.dep_path("public/key.pem")
SSL_CERT: str = common.dep_path("public/cert.pem")
# Configure CORS settings
CUSTOM_ORIGINS_ENV: str = os.getenv("CUSTOM_ORIGINS")
CUSTOM_ORIGINS = CUSTOM_ORIGINS_ENV.split(",") if CUSTOM_ORIGINS_ENV else []
origins = [
    "http://localhost:3000",  # (optional) for testing client apps
    # "https://hoppscotch.io",  # (optional) for testing endpoints
    # "https://brain-dump-dieharders.vercel.app",  # (optional) client app origin (preview)
    # "https://homebrew-ai-discover.vercel.app",  # (optional) client app origin (production/alias)
    openbrew_studio_url,  # (required) client app origin (production/domain)
    *CUSTOM_ORIGINS,
]


###############
### Methods ###
###############


def shutdown_server(*args):
    print(f"{common.PRNT_API} Force shutting down server...", flush=True)
    os.kill(os.getpid(), signal.SIGINT)
    # sys.exit(0)


def display_server_info():
    print(
        f"{common.PRNT_API} Navigate your browser to Obrew Studio for the admin web UI:\n-> {openbrew_studio_url}",
        flush=True,
    )
    # Display the local IP address of this server
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    # @TODO Can we infer the http protocol automatically somehow?
    remote_ip = f"https://{IPAddr}"
    local_ip = f"https://localhost"
    print(
        f"{common.PRNT_API} Refer to API docs for Obrew Server:\n-> {local_ip}:{SERVER_PORT}/docs \nOR\n-> {remote_ip}:{SERVER_PORT}/docs",
        flush=True,
    )
    return {
        "local_ip": local_ip,
        "remote_ip": remote_ip,
    }


def start_server():
    try:
        print(f"{common.PRNT_API} Starting API server...")
        # Start the ASGI server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=SERVER_PORT,
            log_level="info",
            # Include these to host over https
            # If server fails to start make sure the .pem files are generated in root dir
            ssl_keyfile=SSL_KEY,
            ssl_certfile=SSL_CERT,
        )
    except:
        print(f"{common.PRNT_API} Failed to start API server")


def run_app_window():
    # Start the API server in a separate thread from main
    window_thread = threading.Thread(target=GUI)
    window_thread.daemon = True  # let the parent kill the child thread at exit
    window_thread.start()
    return window_thread


# Create and run the Tkinter window
def GUI():
    color_bg = "#333333"
    root = tk.Tk()
    root.title("Obrew Server")
    root.geometry("500x500")
    # Since /public folder is bundled inside _deps, we need to read from root `sys._MEIPASS`
    root.iconbitmap(default=common.dep_path("public/favicon.ico"))
    root.configure(bg=color_bg)
    # Set font
    Font_tuple = ("Verdana", 64, "bold")
    root.bind("<Escape>", lambda e: e.widget.quit())
    tk.Label(root, text="O🍺brew", font=Font_tuple).pack(fill=tk.BOTH, expand=True)
    root.mainloop()
    # Close server when user closes window
    shutdown_server()


##############
### Routes ###
##############

# Redirect requests to our custom endpoints
# from fastapi import Request
# @app.middleware("http")
# async def redirect_middleware(request: Request, call_next):
#     return await redirects.text(request, call_next, str(app.PORT_TEXT_INFERENCE))

# Add CORS support
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes
endpoint_router = APIRouter()

endpoint_router.include_router(services, prefix="/v1/services", tags=["services"])
endpoint_router.include_router(embeddings, prefix="/v1/memory", tags=["embeddings"])
endpoint_router.include_router(
    text_inference, prefix="/v1/text", tags=["text inference"]
)
endpoint_router.include_router(settings, prefix="/v1/persist", tags=["settings"])
# add more `router.include_router()` as needed for other files
app.include_router(endpoint_router)


# Return a "connect" GUI page for user to config and startup the API server,
# then return the user to the supplied callback url with query params of config added.
# QRcode generation -> https://github.com/arjones/qr-generator/tree/main
@app.get("/", response_class=HTMLResponse)
async def connect_page(request: Request):
    # Be sure to link `public/templates` to the app's dependency dir (_deps) via PyInstaller
    templates_dir = common.dep_path(os.path.join("public", "templates"))
    templates = Jinja2Templates(directory=templates_dir)
    remote_url = server_info["remote_ip"]
    local_url = server_info["local_ip"]
    # Generate QR code - direct to remote url
    qr_code = pyqrcode.create(
        f"{remote_url}:{SERVER_PORT}/?hostname={remote_url}&port={SERVER_PORT}"
    )
    qr_data = qr_code.png_as_base64_str(scale=5)
    # qr_image = qr_code.png("image.png", scale=8) # Write image file to disk

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "qr_data": qr_data,
            "title": "Connect to Obrew Server",
            "app_name": "Obrew🍺Server",
            "message": "Scan the code with your mobile device to access the WebUI remotely and/or click the link below.",
            "host": local_url,
            "remote_host": remote_url,
            "port": SERVER_PORT,
        },
    )


# Keep server/database alive
@app.get("/v1/ping")
def ping() -> classes.PingResponse:
    try:
        db = storage.get_vector_db_client(app)
        db.heartbeat()
        return {"success": True, "message": "pong"}
    except Exception as e:
        print(f"{common.PRNT_API} Error pinging server: {e}")
        return {"success": False, "message": ""}


# Tell client we are ready to accept requests
@app.get("/v1/connect")
def connect() -> classes.ConnectResponse:
    return {
        "success": True,
        "message": f"Connected to api server on port {SERVER_PORT}. Refer to 'https://localhost:{SERVER_PORT}/docs' for api docs.",
        "data": {
            "docs": f"https://localhost:{SERVER_PORT}/docs",
            "version": api_version,
        },
    }


#############
### Start ###
#############


if __name__ == "__main__":
    try:
        # Find IP info
        server_info = display_server_info()
        local_ip = server_info["local_ip"]
        local_url = f"{local_ip}:{SERVER_PORT}"
        # Open browser to WebUI
        print(f"{common.PRNT_API} API server started. Opening WebUI at {local_url}")
        webbrowser.open(local_url, new=2)
        print(f"{common.PRNT_API} Close this window to shutdown server.")
        # Show a window
        if is_prod:
            run_app_window()
        # Start API server
        start_server()
    except (KeyboardInterrupt, Exception):
        print(f"{common.PRNT_API} Something bad happenned, exiting...")
        shutdown_server()
