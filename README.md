# 🍺 HomebrewAi - Ai Inference Engine

This project handles all requests from client chat apps using a single api. The goal is to provide a modular architecture that allows rapid development of chat-based front-end apps. Client apps need only make HTTP requests to perform any function related to ai workloads.

---

## Introduction

This is a hybrid Next.js + Python app that uses Next.js as the frontend and FastAPI as the API backend. It ships with a GUI to allow you to manually configure the backend ai services which use Python libraries. Configuration can also be done programmatically. Launch this desktop app locally, then navigate your browser to any web app that supports this project's api and start using ai locally with your own private data for free:

Project forked here [the Next.js GitHub repository](https://github.com/vercel/next.js/)
Using this vercel project as starting point: https://github.com/vercel/next.js/tree/canary/examples/with-electron

---

## Features (goals)

- Inference: Run open-source AI text models.
- Embeddings: Create vector embeddings from a string or document.
- Search: Using a vector database and Llama Index to make semantic or similarity queries.
- Threads: Save/Retrieve chat message history to memory, disk or cloud db.
- Desktop app binaries (free, use our infra locally)

## Features (upcoming)

- Cloud platform (subscription, host your infra with us)
- Enterprise service (subscription & paid support, bring your own infra)

---

## How It Works

- Startup and shutdown of the backend services are done via the front-end.

- The Python/FastAPI server (homebrew api) operates under `localhost:8008`.

- 3rd party client apps will call the homebrew api to perform all functions needed.

---

## Getting Started

### Dependencies

First, install the dependencies for javascript:

```bash
yarn install
```

Install dependencies for python listed in your requirements.txt file:

Be sure to run this command with admin privileges. This command is optional and is also run on each `yarn build`.

```bash
pip install -r requirements.txt
# or
yarn python-deps
```

---

## Testing locally

### Run Front-End

Run development front-end webserver (unstable):

```bash
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Run Backend API

If you wish to run the backend server seperately, right-click over `src/backends/main.py` and choose "run python file in terminal" to start server:

```bash
# from working dir
python src/backends/main.py
```

The homebrew api server will be running on [http://localhost:8008](http://localhost:8008)

### Run the app in development

This is the perferred method of running the app:

```bash
yarn start
```

---

## Building

This project is meant to be deployed locally on the client's machine. It is a next.js app using serverless runtimes all wrapped by Electron to create a native app. We do this to package up dependencies to make installation easier on the user and to provide the app access to the local OS disk space.

### Explanation of build scripts

Bundling Python exe (the -F flag bundles everything into one .exe ). This is handled automatically by npm scripts and you do not need to execute these manually.

To install the pyinstaller tool:

```bash
pip install -U pyinstaller
```

Then use it to bundle a python script:

```bash
pyinstaller -c -F your_program.py
```

Building app for production:

```bash
yarn build
```

### Package application with Electron for release

This will build the production deps and then bundle them with pre-built Electron binaries into an installer/distributable.
Please note, "yarn" should be used as the package manager as npm/pnpm will not work for packaging node_modules for some reason.
Electron Builder commands: https://www.electron.build/cli.html

This will create an installer (perferred). Copy the file from `/release/[app-name][version].exe` and put into your Github releases.

```bash
yarn release
```

This will create a folder with all the raw files in `/release/win-unpacked` (when built for windows). Useful for dev since you can inspect the loose files in folder.

```bash
yarn unpacked
```

---

## API

This project deploys several different backend apps exposed via the /api endpoint. The idea is to separate all OS level logic and processing from the client facing app. This can make deployment to the cloud and swapping out functionality easier.

Endpoints can be found [here](http://localhost:8008/docs) for the homebrew api server.

### /v1/ping

Used to keep the inference server alive.

### /v1/connect

Used by client apps to detect when services are ready to be used.

### /v1/services/shutdown

Terminates all running services.

### /v1/services/api

Gets all parameters for making calls to the homebrew api.

### /v1/models

Gets all inference model configuration.

### /v1/text/load

### /v1/text/start

This is entry for all text inference functions. Endpoints can be found [here](http://localhost:8000/docs) after server is started.

---

## Models

To get the sha256 of each file, click on the model you want from the "Files" page and copy from the page or raw pointer.

## Inference

- [Project used for ai inference](https://github.com/abetlen/llama-cpp-python)
- [TODO-Use vLLM](https://github.com/vllm-project/vllm)

## Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/) - learn about FastAPI features and API.
