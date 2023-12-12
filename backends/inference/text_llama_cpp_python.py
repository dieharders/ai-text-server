import subprocess


async def start_text_inference_server(file_path: str, port: int, process: str):
    try:
        path = file_path.replace("\\", "/")

        # Command to execute
        serve_llama_cpp = [
            "python",
            "-m",
            "llama_cpp.server",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
            "--model",
            path,
            # "--help",
            "--n_ctx",
            "2048",
            # "--n_gpu_layers",
            # "2",
            # "--verbose",
            # "True",
            # "--cache",
            # "True",
            # "--cache_type",
            # "disk",
            # "--seed",
            # "0",
        ]
        # Execute the command
        proc = subprocess.Popen(serve_llama_cpp)
        print(
            f"[homebrew api] Starting Inference server from: {file_path} with pid: {proc.pid}"
        )
        return proc
    except:
        print("[homebrew api] Failed to start Inference server")
        return False
