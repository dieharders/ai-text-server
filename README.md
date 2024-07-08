# 🍺 Obrew Server - Ai Engine

## Introduction

The goal of this project is to be an all-in-one solution for running Ai that is easy to install. It is a native app that runs a server which handles all basic building blocks of Ai: inference, memory, model file manager, agent builder, app installer, GUI.

## How It Works

The Obrew Engine is a Python server built with FastAPI. We provide a Web UI called [Obrew Studio](https://studio.openbrewai.com/) to access this server. You can also access it programmatically via the [API](#api-overview).

Launch the desktop app locally, then navigate your browser to any web app that supports this project's api and start using ai locally with your own private data for free:

## App Features Roadmap

- ✅ Run locally
- ✅ Provide easy to use desktop installers
- ✅ Save chat history
- ✅ CPU & GPU support
- ✅ Windows OS installer
- ❌ MacOS/Linux installer
- ❌ Docker config for easy server deployment
- ❌ Support deployment to hosted server with Admin login support
- ❌ Production ready: This project is currently under active development, there may be bugs

## Ai Features Roadmap

- ✅ Inference: Run open-source AI models for free
- ✅ Embeddings: Create vector embeddings from a text or document files
- ✅ Search: Using a vector database and Llama Index to make semantic or similarity queries
- ✅ Build custom bots
- ✅ Agents: Bots with tools
- ❌ Workloads: Agent jobs
- ❌ Support multi-modal & vision models
- ❌ Source citations in retrieved responses
- ❌ Chat conversations
- ❌ Infinite context & Long-term memory across conversations (personal memory)
- ❌ Voice to text (User query) and text-to-speech (Ai responses)

## Supported Model Providers

This is a local first project. The ultimate goal is to support all providers via one API.

- ✅ [Open-Source](https://huggingface.co)
- ❌ [Google Gemini](https://gemini.google.com)
- ❌ [OpenAI](https://openai.com/chatgpt)
- ❌ [Anthropic](https://www.anthropic.com)
- ❌ [Mistral AI](https://mistral.ai)
- ❌ [Groq](https://groq.com)

## Getting Started

### Install Dependencies

Install dependencies for python listed in requirements.txt file:

Be sure to run this command with admin privileges. This command is optional and is also run on each `yarn build`.

```bash
pip install -r requirements.txt
# or
yarn python-deps
```

## Run

### Run production executable

If you get a "Permission Denied" error, try running the executable with Admin privileges.

### Testing

Right-click over `src/backends/main.py` and choose "run python file in terminal" to start server:

Or

```bash
# from working dir
python src/backends/main.py
```

Or, using yarn (recommended)

```bash
yarn server:dev
# or
yarn server:local-prod
# or
yarn server:hosted-prod
```

The Obrew api server will be running on [https://localhost:8008](https://localhost:8008)

\*_Note_ if the server fails to start be sure to run `yarn makecert` command to create certificate files necessary for https (these go into `_deps/public` folder).

## Build steps for GPU Support

These steps outline the process of supporting GPU's. If all you need is CPU, then you can skip this.

### Building llama.cpp

When you do the normal `pip install llama-cpp-python`, it installs with only CPU support by default.

If you want GPU support for various platforms you must build llama.cpp from source and then pip --force-reinstall.

Follow these steps to build llama-cpp-python for your hardware and platform.

#### Build for Nvidia GPU (cuBLAS) support on Windows

1. Install Visual Studio (Community 2019 is fine) with components:

- C++ CMake tools for Windows
- C++ core features
- Windows 10/11 SDK
- Visual Studio Build Tools

2. Install the CUDA Toolkit:

- Download CUDA Toolkit from https://developer.nvidia.com/cuda-toolkit
- Install only components for CUDA
- If the installation fails, you will need to uncheck everything and only install `visual_studio_integration`. Next proceed to install packages one at a time or in batches until everything is installed.
- Add CUDA_PATH (C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2) to your environment variables

3. llama-cpp-python build steps:

If on Windows, run the following using "Command Prompt" tool. If you are developing in a python virtual or Anaconda env, be sure you have the env activated first and then run from Windows cmd prompt.

```cmd
set FORCE_CMAKE=1 && set CMAKE_ARGS=-DLLAMA_CUBLAS=on && pip install llama-cpp-python --force-reinstall --ignore-installed --upgrade --no-cache-dir --verbose
```

- If CUDA is detected but you get `No CUDA toolset found` error, copy all files from:

`C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.3\extras\visual_studio_integration\MSBuildExtensions`

into

`C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Microsoft\VC\v160\BuildCustomizations`

(Adjust the path/version as necessary)

4. Once everything is installed, be sure to set `n_gpu_layers` to an integer higher than 0 to offload inference layers to gpu. You will need to play with this number depending on VRAM and context size of model.

#### Build GPU support for other platforms

See here https://github.com/ggerganov/llama.cpp#build

and here https://github.com/abetlen/llama-cpp-python/blob/main/README.md#installation-with-specific-hardware-acceleration-blas-cuda-metal-etc

for steps to compile to other targets.

## Bundling - Take all deps, dlls, code and bundle with an executable

Be sure to generate self-signed certs for easy SSL setup in local environment.

### Bundling Nvida CUDA toolkit deps:

If you already have the required toolkit files installed and have built for GPU then the necessary GPU drivers/dlls should be detected by PyInstaller and included in the `_deps` dir.

### Bundling with PyInstaller:

This is handled automatically by npm scripts so you do not need to execute these manually. The -F flag bundles everything into one .exe file.

To install the pyinstaller tool:

```bash
pip install -U pyinstaller
```

Then use it to bundle a python script:

```bash
pyinstaller -c -F your_program.py
```

### Bundling with auto-py-to-exe (recommended)

This is a GUI tool that greatly simplifies the process. You can also save and load configs. It uses PyInstaller under the hood and requires it to be installed. Please note if using a conda or virtual environment, be sure to install both PyInstaller and auto-py-to-exe in your virtual environment and also run them from there, otherwise one or both will build from incorrect deps.

\*_Note_, you will need to edit paths for the following in `auto-py-to-exe` to point to your base project directory:

- Settings -> Output directory
- Additional Files
- Script Location

To run:

```bash
auto-py-to-exe
```

## Packaging - compress & pack bundled code into install wizard

### Inno Installer Setup Wizard

This utility will take your exe and dependencies and compress the files, then wrap them in a user friendly executable that guides the user through installation.

1. Download Inno Setup from (here)[https://jrsoftware.org/isinfo.php]

2. Install and run the setup wizard for a new script

3. Follow the instructions and before it asks to compile the script, cancel and inspect the script where it points to your included files/folders

4. Be sure to append `/[your_included_folder_name]` after the `DestDir: "{app}"`. So instead of `{app}` we have `{app}/assets`. This will ensure it points to the correct paths of the added files you told pyinstaller to include.

5. After that compile the script and it should output your setup file where you specified (or project root).

## Deploy to Production

### Deploy to public hosted internet

For production deployments you will either want to run the server behind a reverse proxy using something like Traefic-Hub (free and opens your self hosted server to public internet using encrypted https protocol).

### Deploy to local network over https

If you wish to deploy this on your private network for local access from any device on that network, you will need to run the server using https which requires SSL certificates. Be sure to set the .env var `ENABLE_SSL`.

Rename the included `.env.example` file to `.env` in the `/_deps` folder and modify the vars accordingly.

This command will create a self-signed key and cert files in your current dir that are good for 100 years. These files should go in the `_deps/public` folder. You should generate your own and overwrite the files in `_deps/public`, do not use the provided certs in a production environment.

```bash
openssl req -x509 -newkey rsa:4096 -nodes -out public/cert.pem -keyout public/key.pem -days 36500
# OR (an alias for same command as above)
yarn makecert
```

This should be enough for any webapp served over https to access the server. If you see "Warning: Potential Security Risk Ahead" in your browser when using the webapp, you can ignore it by clicking `advanced` then `Accept the Risk` button to continue.

## Releasing

### Create a release on Github with link to installer

1. Create a tag with:

Increase the patch version by 1 (x.x.1 to x.x.2)

```bash
yarn version --patch
```

Increase the minor version by 1 (x.1.x to x.2.x)

```bash
yarn version --minor
```

Increase the major version by 1 (1.x.x to 2.x.x)

```bash
yarn version --major
```

2. Create a new release in Github and choose the tag just created or enter a new tag name for Github to make.

3. Drag & Drop the binary file you wish to bundle with the release. Then hit done.

4. If the project is public then the latest release's binary should be available on the web to anyone with the link:

https://github.com/[github-user]/[project-name]/releases/latest/download/[installer-file-name]

## API Overview

This project deploys several servers/processes (databases, inference, etc.) exposed using the `/v1` endpoint. The goal is to separate all OS level logic and processing from the client apps. This can make deploying new apps and swapping out functionality easier.

A complete list of endpoint documentation can be found at [http://localhost:8000/docs](http://localhost:8000/docs) after Obrew Server is started.

### Client api library

There is currently a javascript library under development and being used by [Obrew Studio](https://github.com/dieharders/brain-dump). Once the project becomes stable, it will be broken out into its own module and repo. Stay tuned.

### API Keys and .env variables

Development: Put your .env file in the base directory of the project.

Installed App: Put your .env file in `_deps` folder in the executable's root directory.

## Managing Python dependencies

It is highly recommended to use an package/environment manager like Anaconda to manage Python installations and the versions of dependencies they require. This allows you to create virtual environments from which you can install different versions of software and build/deploy from within this sandboxed environment.

To update PIP package installer:

```bash
conda update pip
```

### Switching between virtual environments

The following commands should be done in `Anaconda Prompt` terminal. If on Windows, `run as Admin`.

1. Create a new environment. This project uses `3.12`:

```bash
conda create --name env1 python=3.12
```

2. To work in this env, activate it:

```bash
conda activate env1
```

3. When you are done using it, deactivate it:

```bash
conda deactivate
```

4. If using an IDE like VSCode, you must apply your newly created virtual environment by selecting the `python interpreter` button at the bottom when inside your project directory.

## Adding Custom Tools for Agents

Some notes on how to create a new function for tool use:

1. Its filename and function name should be the same
2. 1 function per tool file
3. Functions must be written in Python: `tool_name.py`
4. Each function needs a description to help the llm
5. Each function needs a Pydantic class assigned to input args

Where to store the function code:
From the project's root `public\tools\functions`
OR
In the installed app's root directory `_deps\public\tools\functions`

## Learn More

- Server: [FastAPI](https://fastapi.tiangolo.com/) - learn about FastAPI features and API.
- Inference: [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) for Ai inference.
- Memory: [Llama-Index](https://github.com/run-llama/llama_index) for data retrieval and [ChromaDB](https://github.com/chroma-core/chroma) for vector database.
- Web UI: [Next.js](https://nextjs.org/) for front-end and [Vercel](https://vercel.com) for hosting.
