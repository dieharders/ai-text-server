# Managing Python dependencies

It is highly recommended to use an package/environment manager like Anaconda to manage Python installations and the versions of dependencies they require. This allows you to create virtual environments from which you can install different versions of software and build/deploy from within this sandboxed environment.

To update PIP package installer:

```bash
conda update pip
```

## Switching between virtual environments

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

[Back to main README](../README.md)
