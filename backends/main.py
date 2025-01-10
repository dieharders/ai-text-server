import os
import sys
import time
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk
from core import common


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


# Check what env is running - prod/dev
build_env = parse_runtime_args()
is_debug = hasattr(sys, "gettrace") and sys.gettrace() is not None
is_dev = build_env["mode"] == "dev" or is_debug
is_prod = build_env["mode"] == "prod" or not is_dev
is_headless = build_env["headless"] == "True"  # headless == no UI window shown

# Comment out if you want to debug on prod build
if is_prod:
    # Remove prints in prod when deploying in window mode
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

# Initialize global data here
server_info = None
SERVER_PORT = 8008
application = AppState()
application.state.PORT_HOMEBREW_API = SERVER_PORT
application.state.is_prod = is_prod
application.state.is_dev = is_dev
application.state.is_debug = is_debug
application.keep_open = True
openbrew_studio_url = "https://studio.openbrewai.com"  # the web UI


###############
### Methods ###
###############


def start_server():
    try:
        # Start the API server
        print(f"{common.PRNT_API} Starting API server.")
    except Exception as e:
        print(f"{common.PRNT_API} API server shutdown. {e}")


def shutdown_server(*args):
    # send shutdown server request
    # ...
    print(f"{common.PRNT_API} Server forced to shutdown.", flush=True)
    application.keep_open = False


def run_app_window():
    # Start the API server in a separate thread from main
    window_thread = threading.Thread(target=GUI)
    window_thread.daemon = True  # let the parent kill the child thread at exit
    window_thread.start()
    return window_thread


def open_browser():
    ip = "localhost"
    local_url = f"{ip}:{SERVER_PORT}"
    # Open browser to WebUI
    print(f"{common.PRNT_API} Opening WebUI at {local_url}")
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
    # Close server when user closes window
    shutdown_server()


#############
### Start ###
#############


if __name__ == "__main__":
    print(f"Starting app...", flush=True)
    try:
        # Show a window
        if not is_headless:
            run_app_window()
        # Block main thread to keep program open
        while application.keep_open:
            time.sleep(1)
    except KeyboardInterrupt:
        # Close everything and cleanup
        shutdown_server()
