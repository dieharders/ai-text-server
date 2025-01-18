# Getting Started

## Running the release executable

If you get a "Permission Denied" error, try running the executable with Admin privileges.

There are two shortcuts installed, the normal executable and one for "headless" mode. In headless mode the backend will run in the background without a GUI window. This is ideal for automation or development since you can use command line arguments to specify how you run the service:

- --host=0.0.0.0
- --port=8008
- --headless=True
- --mode=dev or prod (this enables/disables logging)

## Running from source code

### Install Python dependencies

Install dependencies for python listed in requirements.txt file:

Be sure to run this command with admin privileges. This command is optional and is also run on each `yarn build`.

```bash
pip install -r requirements.txt
# or
yarn python-deps
```

### Install WebUI dependencies (for Front-End GUI)

Not strictly required, but if you intend to work with the UI files (html/css/js) and want linting, etc. then run:

```bash
yarn install
```

### Start the backend

Right-click over `backends/main.py` and choose "run python file in terminal" to start server:

Or

```bash
# from working dir
python backends/main.py
```

Or using yarn (recommended)

```bash
yarn server:dev
# or
yarn server:prod
# or to run headless (production)
yarn server:headless-prod
# or to run headless (development)
yarn server:headless-dev
```

The Obrew api server will be running on [https://localhost:8008](https://localhost:8008)

\*_Note_ if the server fails to start be sure to run `yarn makecert` command to create certificate files necessary for https (these go into `_deps/public` folder).

[Back to main README](../README.md)
