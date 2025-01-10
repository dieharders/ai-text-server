import os
import sys
import time
import threading
import webbrowser
import socket
import tkinter as tk
from tkinter import ttk
from dotenv import load_dotenv
import asyncio
import signal
from multiprocessing import Process

# Custom
from core import common
from api_server import ApiServer


class AppState:
    class State:
        def __init__(self):
            return

    def __init__(self):
        self.state = self.State()


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
server_info = None
SSL_ENABLED = os.getenv("ENABLE_SSL", "False").lower() in ("true", "1", "t")
XHR_PROTOCOL = "http"
if SSL_ENABLED is True:
    XHR_PROTOCOL = "https"
application = AppState()
application.state.API_SERVER_PORT = 8008
application.state.is_headless = (
    build_env["headless"] == "True"
)  # headless == no UI window shown
application.state.is_debug = hasattr(sys, "gettrace") and sys.gettrace() is not None
application.state.is_dev = build_env["mode"] == "dev" or application.state.is_debug
application.state.is_prod = build_env["mode"] == "prod" or not application.state.is_dev
application.state.keep_open = True

# Comment out if you want to debug on prod build
if application.state.is_prod:
    # Remove prints in prod when deploying in window mode
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

###############
### Methods ###
###############


def display_server_info():
    # Display the local IP address of this server
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    remote_ip = f"{XHR_PROTOCOL}://{IPAddr}"
    local_ip = f"{XHR_PROTOCOL}://localhost"
    return {
        "local_ip": local_ip,
        "remote_ip": remote_ip,
    }


def start_server():
    try:
        # Start the API server
        server_info = display_server_info()
        local_ip = server_info["local_ip"]
        remote_ip = server_info["remote_ip"]
        print(f"{common.PRNT_APP} Starting API server.")
        application.state.api_server = ApiServer(
            is_prod=application.state.is_prod,
            is_dev=application.state.is_dev,
            is_debug=application.state.is_debug,
            server_info=server_info,
            SSL_ENABLED=SSL_ENABLED,
            SERVER_PORT=application.state.API_SERVER_PORT,
            XHR_PROTOCOL=XHR_PROTOCOL,
        )
        application.state.api_server.startup()
        print(
            f"{common.PRNT_APP} Refer to API docs:\n-> {local_ip}:{application.state.API_SERVER_PORT}/docs \nOR\n-> {remote_ip}:{application.state.API_SERVER_PORT}/docs",
            flush=True,
        )
    except Exception as e:
        print(f"{common.PRNT_APP} Failed to start API server. {e}")


# Send shutdown server request
def shutdown_server(*args):
    try:
        application.state.api_server.shutdown()
        print(f"{common.PRNT_APP} Shutting down server.", flush=True)
    except Exception as e:
        print(f"{common.PRNT_APP} Error, server forced to shutdown: {e}", flush=True)


def run_app_window():
    # Start the API server in a separate thread from main
    window_thread = threading.Thread(target=GUI)
    window_thread.daemon = True  # let the parent kill the child thread at exit
    window_thread.start()
    return window_thread


def open_browser():
    server_info = display_server_info()
    local_ip = server_info["local_ip"]
    local_url = f"{local_ip}:{application.state.API_SERVER_PORT}"
    # Open browser to WebUI
    print(f"{common.PRNT_APP} Opening WebUI at {local_url}")
    webbrowser.open(local_url, new=2)


# Create and run the Tkinter window
def GUI():
    color_bg = "#333333"
    root = tk.Tk()
    root.title("Obrew Server")
    root.geometry("500x500")
    # Since /public folder is bundled inside _deps, we need to read from root `sys._MEIPASS`
    root.iconbitmap(default=common.dep_path(os.path.join("public", "favicon.ico")))
    root.configure(bg=color_bg)
    # Render title
    Font_tuple = ("Verdana", 64, "bold")
    root.bind("<Escape>", lambda e: e.widget.quit())
    tk.Label(root, text="O🍺brew", font=Font_tuple).pack(fill=tk.BOTH, expand=True)
    # Render button for connection page
    style = ttk.Style()
    style.configure(
        "TButton",
        font=("Verdana", 14),
        borderwidth=0,
        padding=10,
        background="grey",
        foreground="black",
    )
    style.map(
        "TButton",
        background=[("pressed", "black"), ("active", "grey")],
        foreground=[("pressed", "grey"), ("active", "black")],
    )
    button = ttk.Button(root, text="Start Here", command=open_browser, style="TButton")
    button.pack(pady=20)
    # Run UI
    root.mainloop()
    # Close app when user closes window
    application.state.keep_open = False
    application.state.server_process.terminate()


# Good for knowing when server has stopped/started
def monitor_server(server_process):
    """Monitor the server process and take action if it crashes."""
    while True:
        if not server_process.is_alive():
            print("Server process has stopped unexpectedly. Restarting...")
            start_server()  # You can restart the server here if needed.
            server_process.start()
        time.sleep(1)  # Check every second


def signal_handler(sig, frame):
    print(
        f"{common.PRNT_APP} Signal received. Main process interrupted. Shutting down."
    )
    sys.exit(0)


#############
### Start ###
#############


async def main():
    # Listen for signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # Start server as process
    process = Process(target=start_server)
    application.state.server_process = process
    process.daemon = True
    process.start()

    # Start monitoring the server process in a separate thread or process
    # monitor_process = Process(target=monitor_server, args=(process))
    # monitor_process.start()

    try:
        # Show a window
        if not application.state.is_headless:
            run_app_window()

        # Wait for process to complete (optional, in case of graceful shutdown)
        while application.state.keep_open:
            process.join()

        # Close everything and cleanup
        print(f"{common.PRNT_APP} Closing app.")
        process.terminate()
    except KeyboardInterrupt:
        print(f"{common.PRNT_APP} Main process interrupted. Shutting down.")
        application.state.keep_open = False
    except Exception as e:
        print(f"{common.PRNT_APP} Main process error: {e}")


# This script is the loader for the rest of the backend. It only handles UI and starting dependencies.
if __name__ == "__main__":
    print(f"{common.PRNT_APP} Starting app...", flush=True)
    asyncio.run(main())
