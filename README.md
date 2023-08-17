# Text to Text Server

This project handles all requests from client chat apps using a singular api. The goal is to provide a modular architecture that allows rapid development of text-based front-end apps. Client apps need only make HTTP requests to perform any function related to text-based ai workloads.

---

## Introduction

This is a hybrid Next.js + Python app that uses Next.js as the frontend and FastAPI as the API backend. It ships with a GUI to allow you to manually configure the backend ai services which use Python libraries. Configuration can also be done programmatically. Launch this desktop app locally, then navigate your browser to any web app that supports this project's api and start using ai locally with your own private data for free:

- Links to supported apps...

Project forked here [the Next.js GitHub repository](https://github.com/vercel/next.js/)

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

- Startup and shutdown of the backend services are done via `/api/start` and `/api/stop` on `localhost:3001`.

- The Python/FastAPI server (universal api) is mapped to the Next.js app under `/api/text` on `localhost:8008` (default port:8008).

- 3rd party client apps will call the universal api to perform all functions needed.

In production, the FastAPI server will be hosted as [Python serverless functions](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python) on Vercel. However since this project will be deployed locally as an Electron app these will evaluate locally.

---

## Getting Started

### Deps

First, install the dependencies for javascript:

```bash
npm install
# or
pnpm install
```

Install dependencies for python listed in your requirements.txt file:

Be sure to run this command with admin privileges. This command is optional and is also run on each `pnpm dev`.

```
pip install -r requirements.txt
```

### Run

Then, run both development webserver and api server in parallel:

```bash
npm run dev
# or
pnpm dev
```

Or run the webserver (front-end) first to setup the api backend manually or programmatically on a specific port:

```bash
npm run next-dev
# or
pnpm run next-dev
```

Open [http://localhost:3001](http://localhost:3001) with your browser to see the result.

The FastApi server will be running on [http://localhost:8008](http://localhost:8008) – feel free to change the port in `package.json`.

---

## Building

This project is meant to be deployed locally on the client's machine. It is a next.js app using serverless runtimes all wrapped by Electron to create a native app. We do this to package up dependencies to make installation easier on the user and to provide the app access to the local OS disk space.

Bundling Python exe (the -F flag bundles everything into one .exe )

- pip install -U pyinstaller
- pyinstaller -c -F your_program.py
- pnpm tauri dev

Building api server for production:

- pnpm build:fastapi
- pnpm tauri build

The installer is located here:

- C:\Project Files\brain-dump-ai\backend-ai-text-server\src-tauri\target\release\bundle\nsis

---

## API

This project deploys several different backend apps exposed via the /api directory, for example inference. The idea is to separate all OS level logic and processing from the client facing app. This can make deployment to the cloud and swapping out functionality easier.

- **/api/text** endpoints can be found [here](http://localhost:8000/docs) after building the api server. Edit port if launched on non default port 8000.

To start the universal api server via HTTP:

```
POST http://localhost:3000/api/start
// with a body of
{
    "port": number
}
```

To stop the universal api server via HTTP:

```
POST http://localhost:3000/api/stop
{
    "pid": number
}
```

These commands are also used by the GUI to configure the universal api server.

---

## Inference

- [Project used for ai inference](https://github.com/abetlen/llama-cpp-python)

## Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/) - learn about FastAPI features and API.
