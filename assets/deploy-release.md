# Deploy to Production

## Deploy to public hosted internet

For production deployments you will either want to run the server behind a reverse proxy using something like Traefic-Hub (free and opens your self hosted server to public internet using encrypted https protocol).

## Start server on local/cloud network over https

If you wish to deploy this on your private network for local access from any device on that network, you will need to run the server using https which requires SSL certificates. Be sure to set the .env var `ENABLE_SSL`.

Rename the included `.env.example` file to `.env` in the `/_deps` folder and modify the vars accordingly.

This command will create a self-signed key and cert files in your current dir that are good for 100 years. These files should go in the `_deps/public` folder. You should generate your own and overwrite the files in `_deps/public`, do not use the provided certs in a production environment.

```bash
openssl req -x509 -newkey rsa:4096 -nodes -out public/cert.pem -keyout public/key.pem -days 36500
# OR (an alias for same command as above)
yarn makecert
```

This should be enough for any webapp served over https to access the server. If you see "Warning: Potential Security Risk Ahead" in your browser when using the webapp, you can ignore it by clicking `advanced` then `Accept the Risk` button to continue.

# Releasing

## Create a release on Github with link to installer

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

[Back to main README](../README.md)
