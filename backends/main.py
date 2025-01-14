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


class MenuAPI:
    def __init__(self):
        pass

    # Save .env vals and other pre-launch settings
    def save_settings(self, settings):
        try:
            # @TODO Save .env values to file
            # ...
            return
        except Exception as e:
            print(f"{common.PRNT_APP} Failed to update .env values: {e}")

    def update_settings_page(self):
        try:
            page_data = dict(obrew_studio_url=obrew_studio_url)
            return page_data
        except Exception as e:
            print(f"{common.PRNT_APP} Failed to update 'Main' page: {e}")

    # Return a "connect" GUI page for user to config and startup the API server,
    # then return the user to the supplied callback url with query params of config added.
    # QRcode generation -> https://github.com/arjones/qr-generator/tree/main
    def update_entry_page(self):
        try:
            port = app.state.API_SERVER_PORT
            server_info = _display_server_info()
            remote_url = server_info["remote_ip"]
            local_url = server_info["local_ip"]
            # Generate QR code - direct to remote url
            qr_code = pyqrcode.create(
                f"{remote_url}:{port}/?hostname={remote_url}&port={port}"
            )
            qr_data = qr_code.png_as_base64_str(scale=5)
            # qr_image = qr_code.png("image.png", scale=8) # Writes image file to disk

            page_data = dict(
                qr_data=qr_data,
                local_url=local_url,
                remote_url=remote_url,
                port=port,
                obrew_studio_url=obrew_studio_url,
            )
            return page_data
        except Exception as e:
            print(f"{common.PRNT_APP} Failed to update 'Connect' page: {e}")

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
    # Initialize variables to store parsed arguments
    mode = None
    headless = "False"
    # Iterate through arguments and parse them
    for arg in arguments:
        if arg.startswith("--mode="):
            mode = arg.split("=")[1]
        if arg.startswith("--headless="):
            headless = arg.split("=")[1]
    return {
        "mode": mode,
        "headless": headless,
    }


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

# Initialize global data here
menu_api = MenuAPI()
SSL_ENABLED = os.getenv("ENABLE_SSL", "False").lower() in ("true", "1", "t")
XHR_PROTOCOL = "http"
if SSL_ENABLED is True:
    XHR_PROTOCOL = "https"
app = AppState()
app.state.API_SERVER_PORT = 8008
app.state.is_headless = (
    build_env["headless"] == "True"
)  # headless == no UI window shown
app.state.is_debug = hasattr(sys, "gettrace") and sys.gettrace() is not None
app.state.is_dev = build_env["mode"] == "dev" or app.state.is_debug
app.state.is_prod = build_env["mode"] == "prod" or not app.state.is_dev
app.state.keep_open = True
obrew_studio_url = "https://studio.openbrewai.com"

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
        # @TODO Get settings from 'config'
        server_info = _display_server_info()
        local_ip = server_info["local_ip"]
        remote_ip = server_info["remote_ip"]
        print(f"{common.PRNT_APP} Starting API server...", flush=True)
        app.state.api_server = ApiServer(
            is_prod=app.state.is_prod,
            is_dev=app.state.is_dev,
            is_debug=app.state.is_debug,
            server_info=server_info,
            SSL_ENABLED=SSL_ENABLED,
            SERVER_PORT=app.state.API_SERVER_PORT,
            XHR_PROTOCOL=XHR_PROTOCOL,
            studio_url=obrew_studio_url,
        )
        app.state.api_server.startup()
        print(
            f"{common.PRNT_APP} Refer to API docs:\n-> {local_ip}:{app.state.API_SERVER_PORT}/docs \nOR\n-> {remote_ip}:{app.state.API_SERVER_PORT}/docs",
            flush=True,
        )
        return
    except Exception as e:
        print(f"{common.PRNT_APP} Failed to start API server. {e}")


def _display_server_info():
    # Display the local IP address of this server
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    remote_ip = f"{XHR_PROTOCOL}://{IPAddr}"
    local_ip = f"{XHR_PROTOCOL}://localhost"
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
            menu_api.start_server()  # You can restart the server here if needed.
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
            # @TODO Get config vals from the command line args used to start this app
            config = dict()
            menu_api.start_server_process(config)

        # @TODO Implement a recovery system for api server, Start monitoring the server process in a separate thread or process
        # monitor_process = Process(target=monitor_server, args=(process))
        # monitor_process.start()

        # Show a window (in non-headless mode)
        if not app.state.is_headless:
            view_instance = view.WEBVIEW(
                is_dev=app.state.is_dev, menu_api=menu_api, ssl=SSL_ENABLED
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
