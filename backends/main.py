import os
import sys
import time
import socket
import signal
from dotenv import load_dotenv
from multiprocessing import Process
import pyqrcode

# Custom
from ui import view
from core import common
from api_server import ApiServer


class AppState:
    class State:
        def __init__(self):
            return

    def __init__(self):
        self.state = self.State()


# Inject these Python funcs into javascript context.
class MenuAPI:
    def __init__(self):
        pass

    # Save .env vals and other pre-launch settings
    def save_settings(self, settings: dict):
        try:
            # Save .env values
            for key, value in settings.items():
                if value and key:
                    os.environ[key] = value.strip().replace(" ", "")
            return
        except Exception as e:
            print(f"{common.PRNT_APP} Failed to update .env values: {e}")

    def update_settings_page(self):
        try:
            # Read in .env vals
            cors = os.getenv("CUSTOM_ORIGINS", "")
            adminWhitelist = os.getenv("WHITELIST_ADMIN_IP", "")
            llamaIndexAPIKey = os.getenv("LLAMA_CLOUD_API_KEY", "")
            page_data = dict(
                ssl=get_ssl_env(),
                cors=cors,
                adminWhitelist=adminWhitelist,
                llamaIndexAPIKey=llamaIndexAPIKey,
            )
            return page_data
        except Exception as e:
            print(f"{common.PRNT_APP} Failed to update 'Main' page: {e}")

    # Generate links for user to connect an external device to this machine's
    # locally running server instance.
    # QRcode generation -> https://github.com/arjones/qr-generator/tree/main
    def update_entry_page(self, port: str):
        try:
            PORT = port or app.state.port
            server_info = _display_server_info()
            remote_url = server_info["remote_ip"]
            local_url = server_info["local_ip"]
            # Generate QR code to remote url
            qr_code = pyqrcode.create(
                f"{remote_url}:{PORT}/?hostname={remote_url}&port={PORT}"
            )
            qr_data = qr_code.png_as_base64_str(scale=5)
            # qr_image = qr_code.png("image.png", scale=8) # Writes image file to disk

            page_data = dict(
                qr_data=qr_data,
                local_url=local_url,
                remote_url=remote_url,
                host=app.state.host,
                port=PORT,
                webui_url=webui_url,
            )
            return page_data
        except Exception as e:
            print(f"{common.PRNT_APP} Failed to update Main page: {e}")

    def start_server_process(self, config):
        process = Process(target=start_server, args=[config])
        app.state.server_process = process
        process.daemon = True
        process.start()

    # Send shutdown server request
    def shutdown_server(*args):
        try:
            app.state.api_server.shutdown()
            print(f"{common.PRNT_APP} Shutting down server.", flush=True)
            return
        except Exception as e:
            print(
                f"{common.PRNT_APP} Error, server forced to shutdown: {e}", flush=True
            )


# Parse runtime arguments passed to script
def parse_runtime_args():
    # Command-line arguments are accessed via sys.argv
    arguments = sys.argv[1:]
    # Initialize default variables to store parsed arguments
    mode = None
    host = "0.0.0.0"
    port = "8008"
    headless = "False"
    # Iterate through arguments and parse them
    for arg in arguments:
        if arg.startswith("--host="):
            host = arg.split("=")[1]
        if arg.startswith("--port="):
            port = arg.split("=")[1]
        if arg.startswith("--mode="):
            mode = arg.split("=")[1]
        if arg.startswith("--headless="):
            headless = arg.split("=")[1]
    return {
        "host": host,
        "port": port,
        "mode": mode,
        "headless": headless,
    }


def get_ssl_env():
    return os.getenv("ENABLE_SSL", "False").lower() in ("true", "1", "t")


# Path to the .env file in either the parent or /_deps directory
try:
    # Look in app's _deps dir
    if sys._MEIPASS:
        env_path = common.dep_path(".env")
except Exception:
    # Otherwise look in codebase root dir
    current_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.dirname(current_directory)
    env_path = os.path.join(parent_directory, ".env")
load_dotenv(env_path)

# Check what env is running - prod/dev
build_env = parse_runtime_args()

# Initialize global data
menu_api = MenuAPI()
app = AppState()
app.state.host = build_env["host"]
app.state.port = build_env["port"]
app.state.is_headless = build_env["headless"] == "True"  # no UI
app.state.is_debug = hasattr(sys, "gettrace") and sys.gettrace() is not None
app.state.is_dev = build_env["mode"] == "dev" or app.state.is_debug
app.state.is_prod = build_env["mode"] == "prod" or not app.state.is_dev
app.state.keep_open = True
webui_url = "https://studio.openbrewai.com"

# Comment out if you want to debug on prod build (or set --mode=prod flag in command)
if app.state.is_prod:
    # Remove prints in prod when deploying in window mode
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")


###############
### Methods ###
###############


# Start the API server
def start_server(config):
    try:
        server_info = _display_server_info()
        remote_ip = server_info["remote_ip"]
        print(f"{common.PRNT_APP} Starting API server...", flush=True)
        app.state.api_server = ApiServer(
            is_prod=app.state.is_prod,
            is_dev=app.state.is_dev,
            is_debug=app.state.is_debug,
            SSL_ENABLED=get_ssl_env(),
            remote_url=remote_ip,
            SERVER_HOST=config["host"],
            SERVER_PORT=int(config["port"]),
            webui_url=config.get("webui", webui_url),  # not always present
        )
        app.state.api_server.startup()
        return
    except Exception as e:
        print(f"{common.PRNT_APP} Failed to start API server. {e}")


def _display_server_info():
    # Display the local IP address of this server
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    ssl = get_ssl_env()
    if ssl:
        SCHEME = "https"
    else:
        SCHEME = "http"
    remote_ip = f"{SCHEME}://{IPAddr}"
    local_ip = f"{SCHEME}://localhost"
    return {
        "local_ip": local_ip,
        "remote_ip": remote_ip,
    }


# Graceful shutdown, close everything and cleanup
def _close_app():
    try:
        app.state.keep_open = False
        if hasattr(app.state, "server_process"):
            app.state.server_process.terminate()
            app.state.server_process.join()
        if hasattr(app.state, "webview_window"):
            app.state.webview_window.destroy()
        print(f"{common.PRNT_APP} Closing app.")
    except:
        print("Failed to close App.")


# Good for knowing when server has stopped/started
def monitor_server(server_process):
    """Monitor the server process and take action if it crashes."""
    while True:
        if not server_process.is_alive():
            print("Server process has stopped unexpectedly. Restarting...")
            # You can restart the server here if needed...
            menu_api.start_server_process(dict())
            server_process.start()
        time.sleep(1)  # Check every second


# Handle premature keyboard interrupt
def _signal_handler(sig, frame):
    print(
        f"{common.PRNT_APP} Signal received. Main process interrupted. Shutting down."
    )
    _close_app()
    # sys.exit(0)


#############
### Start ###
#############


def main():
    try:
        # Listen for signal handler for SIGINT (Ctrl+C, KeyboardInterrupt)
        signal.signal(signal.SIGINT, _signal_handler)

        # Start server process on startup for headless mode (otherwise, we do this via webui or cli)
        if app.state.is_headless:
            config = dict(host=app.state.host, port=app.state.port)
            menu_api.start_server_process(config)

        # @TODO Implement a recovery system for api server, Start monitoring the server process in a separate thread or process
        # monitor_process = Process(target=monitor_server, args=(process))
        # monitor_process.start()

        # Show a window (non-headless mode)
        if not app.state.is_headless:
            view_instance = view.WEBVIEW(
                is_dev=app.state.is_dev, menu_api=menu_api, ssl=get_ssl_env()
            )
            app.state.webview_window = view_instance.get("handle")
            start_ui = view_instance.get("callback")
            start_ui()
            # Close app when user closes window
            _close_app()

        # Prevent premature exit in headless mode
        while app.state.keep_open:
            time.sleep(1)
    except Exception as e:
        print(f"{common.PRNT_APP} Main process error: {e}")


# This script is the loader for the rest of the backend. It only handles UI and starting dependencies.
if __name__ == "__main__":
    print(f"{common.PRNT_APP} Starting app...", flush=True)
    main()
