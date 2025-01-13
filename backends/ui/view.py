# import os
# import tkinter as tk
# from tkinter import ttk
import webview

# import threading
# from core import common


# def _run_app_window():
#     # Start the API server in a separate thread from main
#     window_thread = threading.Thread(target=GUI)
#     window_thread.daemon = True  # let the parent kill the child thread at exit
#     window_thread.start()
#     return window_thread

# Create and run the Tkinter window
# def GUI(menu_api):
#     color_bg = "#333333"
#     root = tk.Tk()
#     root.title("Obrew Server")
#     root.geometry("500x500")
#     # Since /public folder is bundled inside _deps, we need to read from root `sys._MEIPASS`
#     root.iconbitmap(default=common.dep_path(os.path.join("public", "favicon.ico")))
#     root.configure(bg=color_bg)
#     # Render title
#     Font_tuple = ("Verdana", 64, "bold")
#     root.bind("<Escape>", lambda e: e.widget.quit())
#     tk.Label(root, text="O🍺brew", font=Font_tuple).pack(fill=tk.BOTH, expand=True)
#     # Render button for connection page
#     style = ttk.Style()
#     style.configure(
#         "TButton",
#         font=("Verdana", 14),
#         borderwidth=0,
#         padding=10,
#         background="grey",
#         foreground="black",
#     )
#     style.map(
#         "TButton",
#         background=[("pressed", "black"), ("active", "grey")],
#         foreground=[("pressed", "grey"), ("active", "black")],
#     )
#     button = ttk.Button(
#         root, text="Start Here", command=menu_api.open_browser, style="TButton"
#     )
#     button.pack(pady=20)
#     # Run UI
#     root.mainloop()


# WebView window
def WEBVIEW(is_dev, menu_api, ssl):
    webview_window = webview.create_window(
        "Obrew Studio Server",
        "ui/index.html",
        js_api=menu_api,
        width=1200,
        height=1050,
        min_size=(350, 450),
        fullscreen=False,
        # transparent=True,
        # frameless=True,
        # easy_drag=True,
    )

    def toggle_fullscreen(window):
        # Has access to window object here
        webview_window.toggle_fullscreen()

    # Expose an inline func before runtime
    webview_window.expose(toggle_fullscreen)

    # Start the window
    def callback():
        webview.start(ssl=ssl, debug=is_dev)

    return dict(handle=webview_window, callback=callback)
