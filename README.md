# Text to Text Server

This project handles all backend requests from AI apps using a singular api.

---

## Introduction

This is a hybrid Next.js + Python app that uses Next.js as the frontend and FastAPI as the API backend. This uses Next.js as the UI to support manual configuration of the server which use Python AI libraries.

Project forked here [the Next.js GitHub repository](https://github.com/vercel/next.js/)

---

## Features

- Inference: Run AI text models
- Embeddings: Create vector embeddings from a string or document
- Storage: Save data (like messages) to memory, local drive or cloud database
- Search: Using a vector database and Llama Index to make semantic or similarity queries
- Messages: Retrieve chat history

---

## How It Works

The Python/FastAPI server is mapped into to Next.js app under `/api/`.

This is implemented using [`next.config.js` rewrites](https://github.com/digitros/nextjs-fastapi/blob/main/next.config.js) to map any request to `/api/:path*` to the FastAPI API, which is hosted in the `/api` folder.

On localhost, the rewrite will be made to `127.0.0.1:[port]`, which is where the FastAPI server is running.

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

Be sure to run this command with admin privileges. This command is also run on each `pnpm dev`.

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

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

The FastApi server will be running on [http://127.0.0.1:8000](http://127.0.0.1:8000) – feel free to change the port in `package.json` (you'll also need to update it in `next.config.js`).

---

## Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/) - learn about FastAPI features and API.

---

## Building

This project is meant to be deployed locally on the client's machine. It is a next.js app using serverless runtimes all wrapped by Electron to create a native app. We do this to package up dependencies to make installation easier on the user and to provide the app access to the local OS disk space.

---

## API

It deploys several different backend apps in the /api directory, for example inference. The idea is to separate all OS level logic and processing from the client facing app. This can make deployment to the cloud and swapping out functionality easier.

- /api/text endpoints can be found [here](http://localhost:8000/docs) after building the api server. Edit port if launched on non default port 8000.

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
