import os
import sys
import time
import webbrowser
import socket
from dotenv import load_dotenv
import signal
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

    # Return a "connect" GUI page for user to config and startup the API server,
    # then return the user to the supplied callback url with query params of config added.
    # QRcode generation -> https://github.com/arjones/qr-generator/tree/main
    def update_connect_page(self):
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
                qr_data=qr_data, local_url=local_url, remote_url=remote_url, port=port
            )
            return page_data
        except Exception as e:
            print(f"{common.PRNT_APP} Failed to update 'Connect' page: {e}")

    # Start the API server
    def start_server(self):
        try:
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
            )
            app.state.api_server.startup()
            print(
                f"{common.PRNT_APP} Refer to API docs:\n-> {local_ip}:{app.state.API_SERVER_PORT}/docs \nOR\n-> {remote_ip}:{app.state.API_SERVER_PORT}/docs",
                flush=True,
            )
        except Exception as e:
            print(f"{common.PRNT_APP} Failed to start API server. {e}")

    # Send shutdown server request
    def shutdown_server(*args):
        try:
            app.state.api_server.shutdown()
            print(f"{common.PRNT_APP} Shutting down server.", flush=True)
        except Exception as e:
            print(
                f"{common.PRNT_APP} Error, server forced to shutdown: {e}", flush=True
            )

    def open_browser(self):
        try:
            server_info = _display_server_info()
            local_ip = server_info["local_ip"]
            local_url = f"{local_ip}:{app.state.API_SERVER_PORT}"
            # Open browser to WebUI
            print(f"{common.PRNT_APP} Opening WebUI at {local_url}")
            webbrowser.open(local_url, new=2)
        except Exception as e:
            print(f"{common.PRNT_APP} Error opening WebUI at {local_url}: {e}")


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

# Comment out if you want to debug on prod build (or set --mode=prod flag in command)
if app.state.is_prod:
    # Remove prints in prod when deploying in window mode
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")


###############
### Methods ###
###############


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


# Close app when user closes window
def _close_app():
    app.state.keep_open = False
    app.state.server_process.terminate()
    app.state.webview_window.destroy()


# Good for knowing when server has stopped/started
def monitor_server(server_process):
    """Monitor the server process and take action if it crashes."""
    while True:
        if not server_process.is_alive():
            print("Server process has stopped unexpectedly. Restarting...")
            menu_api.start_server()  # You can restart the server here if needed.
            server_process.start()
        time.sleep(1)  # Check every second


def _signal_handler(sig, frame):
    print(
        f"{common.PRNT_APP} Signal received. Main process interrupted. Shutting down."
    )
    sys.exit(0)


#############
### Start ###
#############


def main():
    # Listen for signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, _signal_handler)

    # Start server as process
    process = Process(target=menu_api.start_server)
    app.state.server_process = process
    process.daemon = True
    process.start()

    # @TODO Implement a recovery system for api server
    # Start monitoring the server process in a separate thread or process
    # monitor_process = Process(target=monitor_server, args=(process))
    # monitor_process.start()

    try:
        # Show a window
        if not app.state.is_headless:
            app.state.webview_window = view.WEBVIEW(
                is_dev=app.state.is_dev, menu_api=menu_api, ssl=SSL_ENABLED
            )
            # Close app when user closes window
            _close_app()

        # Wait for process to complete (optional, in case of graceful shutdown)
        while app.state.keep_open:
            process.join()

        # Close everything and cleanup
        print(f"{common.PRNT_APP} Closing app.")
        process.terminate()
    except KeyboardInterrupt:
        print(f"{common.PRNT_APP} Main process interrupted. Shutting down.")
        app.state.keep_open = False
    except Exception as e:
        print(f"{common.PRNT_APP} Main process error: {e}")


# This script is the loader for the rest of the backend. It only handles UI and starting dependencies.
if __name__ == "__main__":
    print(f"{common.PRNT_APP} Starting app...", flush=True)
    main()
