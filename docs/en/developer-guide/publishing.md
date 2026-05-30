# Publishing and Module Store Guide

Publish your developed modules or adapters to the ErisPulse Module Store, allowing other users to conveniently discover and install them.

## Module Store Overview

The ErisPulse Module Store is a centralized module registry where users can browse, search, and install community-contributed modules and adapters through CLI tools.

### Browse and Discover

```bash
# List all remote available packages
epsdk list-remote

# Only view modules
epsdk list-remote -t modules

# Only view adapters
epsdk list-remote -t adapters

# Force refresh remote package list
epsdk list-remote -r
```

You can also visit the [ErisPulse official website](https://www.erisdev.com/#market) to browse the Module Store online.

### Supported Submission Types

| Type | Description | Entry-point Group |
|------|------|----------------|
| Module | Extend bot functionality, implement business logic | `erispulse.module` |
| Adapter | Connect to new messaging platforms | `erispulse.adapter` |

## Quick Publishing

The entire publishing process only requires three steps: Configure Project → Publish to PyPI → Submit to Module Store.

### 1. Configure pyproject.toml

Ensure your project directory contains `pyproject.toml`, `README.md`, and configure entry-points based on the type:

#### Module

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Module functionality description"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [ { name = "yourname" } ]
dependencies = [
    "ErisPulse>=2.0.0",
]

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

#### Adapter

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "Adapter functionality description"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **Note**: It is recommended that package names start with `ErisPulse-` for easy recognition by users. The key name in the entry-point (such as `"MyModule"`) will serve as the access name for the module in the SDK.

### 2. Publish to PyPI

```bash
# Build + publish (requires PyPI account)
pip install build twine
python -m build
python -m twine upload dist/*
```

Verify successful installation after publishing:

```bash
pip install ErisPulse-MyModule
```

### 3. Submit to Module Store

Go to the [ErisPulse Module Store](https://www.erisdev.com/#market), click "Submit Module", fill in the module information after logging in.

Supported login methods: **GitHub**, **Codeberg**, **Cloud Lake**, any one of these is sufficient.

Key points to fill in:
- Module name, description, repository URL
- Minimum SDK version: If unsure, use the version number from the [latest ErisPulse release](https://pypi.org/project/ErisPulse/)

Submission takes effect immediately, users can install through the module source. The module will be marked as "Unverified" and changed to "Verified" after maintainer review.

> **Regarding Verification Status**:
> - "Unverified" only indicates that it has not undergone official review, not that there is an issue with the module
> - Users will receive a risk warning when installing unverified modules through `epsdk install` and need to confirm before proceeding with installation

### 4. Manage Published Modules

After clicking "Submit Module" in the Module Store and logging in, switch to the "My Modules" tab to:
- **Edit** — Modify module description, repository URL, tags and other information, version number will be automatically synchronized from PyPI
- **Delete** — Remove the module from the Module Store (irreversible)

> Newly submitted modules may take a few minutes to appear in the "My Modules" list.

## Update Published Modules

1. Update the `version` in `pyproject.toml`
2. Rebuild and upload: `python -m build && python -m twine upload dist/*`
3. The Module Store will automatically sync the latest version from PyPI

Users can upgrade by running `epsdk upgrade MyModule`.

## Development Mode Testing

Before formal publishing, you can test locally in editable mode:

```bash
epsdk install -e /path/to/MyModule
# or
pip install -e /path/to/MyModule
```

## Common Questions

### Do package names have to start with `ErisPulse-`?

Not mandatory, but strongly recommended. This helps users identify ErisPulse ecosystem packages on PyPI.

### Can a single package register multiple modules?

Yes. Configure multiple key-value pairs in `entry-points`:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### How long does the review take?

Usually completed within 1-3 business days. You can check the review status in the "My Modules" section of the Module Store.

## Distribute Applications via Docker Images

If your application is not suitable for publishing to PyPI (e.g., contains private dependencies, requires pre-configured environment), you can publish Docker images through **GitHub Container Registry (GHCR)** for other users to `docker pull` and start with one command.

### Applicable Scenarios

- You have a **complete bot application** (modules + configuration + entry script) and want one-click distribution
- The module/adapter depends on **private packages** or has special installation processes, not suitable for PyPI
- You want to provide a **ready-to-use** deployment solution to lower the user's entry barrier

### 1. Create Dockerfile

Build based on the official ErisPulse image:

```dockerfile
FROM erispulse/erispulse:latest

LABEL org.opencontainers.image.title="ErisPulse-MyModule" \
      org.opencontainers.image.description="Module functionality description" \
      org.opencontainers.image.url="https://github.com/yourname/ErisPulse-MyModule" \
      org.opencontainers.image.source="https://github.com/yourname/ErisPulse-MyModule"

COPY pyproject.toml README.md ./
COPY MyModule/ ./MyModule/

RUN uv pip install --system -e .
```

If the module requires additional system dependencies (e.g., SSH client), add this after `RUN uv pip install`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` already includes ErisPulse, ErisPulse-Dashboard, Python runtime, and uv, no need to reinstall.

### 2. Create GitHub Actions Workflow

Create in `.github/workflows/docker-publish.yml`:

```yaml
name: Publish Docker Image

on:
  workflow_dispatch:
  push:
    branches:
      - main
    tags:
      - "v*"

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository_owner }}/my-bot

jobs:
  docker-publish:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up QEMU (multi-arch support)
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: Build and push Docker image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

> `GITHUB_TOKEN` is automatically provided by GitHub Actions, no need to manually create secrets.

### 3. Trigger Build

Push code or create a Tag to automatically build:

```bash
# Push to main branch to trigger
git push origin main

# Or create a Tag to trigger
git tag v1.0.0
git push origin v1.0.0
```

You can also trigger manually in the repository's **Actions** page.

### 4. Set Image as Public

GHCR images are **private** by default, you need to set them as Public in GitHub for other users to pull without login:

1. Go to Repository → **Packages** → Click the corresponding Package
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. User Usage

After building, other users can run directly:

```bash
docker pull ghcr.io/<your-username>/my-bot:latest

docker run -d \
  --name my-bot \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  -e TZ=Asia/Shanghai \
  -e ERISPULSE_DASHBOARD_TOKEN=your-token \
  --restart unless-stopped \
  ghcr.io/<your-username>/my-bot:latest
```

Or use `docker-compose.yml`:

```yaml
services:
  my-bot:
    image: ghcr.io/<your-username>/my-bot:latest
    container_name: my-bot
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
    environment:
      - TZ=Asia/Shanghai
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    restart: unless-stopped
```

### Publish to Docker Hub Simultaneously

Extend the workflow by adding a Docker Hub login step and increasing Docker Hub address in `images`:

```yaml
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          registry: docker.io
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            docker.io/<your-dockerhub-username>/my-bot
            ghcr.io/${{ github.repository_owner }}/my-bot
```

> Need to add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` in repository **Settings → Secrets**.

### Docker Images vs PyPI Publishing

| Feature | Docker Image (GHCR) | PyPI Publishing |
|---------|---------------------|-----------------|
| Distribution Method | `docker pull` one-click run | `pip install` + manual configuration |
| Scope | Complete application/solution | Single module/adapter |
| Private Dependencies | Naturally supported | Requires private PyPI source |
| Module Store | Not applicable | Can be submitted to Module Store |
| Multi-arch | Supports amd64/arm64 | Architecture-independent |

The two methods are not mutually exclusive—you can publish modules to the Module Store via PyPI while also providing ready-to-use Docker images via GHCR.