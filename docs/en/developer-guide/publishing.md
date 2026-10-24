# Publishing and Module Store Guide

> [!TIP]
> **When to read this**: When publishing your work to PyPI / the Module Store. Skip it otherwise; it does not affect the use of other features.

Publish the modules or adapters you develop to the ErisPulse Module Store, so that other users can easily discover and install them.

## Module Store Overview

The ErisPulse Module Store is a centralized module registry where users can browse, search, and install community-contributed modules and adapters via CLI tools.

### Browsing and Discovery

```bash
# List all packages available remotely
epsdk list-remote

# View modules only
epsdk list-remote -t modules

# View adapters only
epsdk list-remote -t adapters

# Force refresh the remote package list
epsdk list-remote -r
```

You can also visit the [ErisPulse official website](https://www.erisdev.com/#market) to browse the Module Store online.

### Supported Submission Types

| Type | Description | Entry-point Group |
|------|------|----------------|
| Module | Extends bot functionality and implements business logic | `erispulse.module` |
| Adapter | Connects to new messaging platforms | `erispulse.adapter` |

## Quick Publish

The whole process takes just three steps: configure the project → publish to PyPI → submit to the Module Store.

### 1. Configure pyproject.toml

Make sure your project directory contains `pyproject.toml` and `README.md`, and configure entry-points according to the type:

#### Module

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Module description"
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
description = "Adapter description"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **Note**: It is recommended that package names start with `ErisPulse-` so users can easily identify them. The entry-point key (e.g., `"MyModule"`) will serve as the module's access name in the SDK.

### 2. Publish to PyPI

```bash
# Build + publish (requires a PyPI account)
pip install build twine
python -m build
python -m twine upload dist/*
```

Verify the installation after a successful publish:

```bash
pip install ErisPulse-MyModule
```

### 3. Submit to the Module Store

Go to the [ErisPulse Module Store](https://www.erisdev.com/#market), click "Submit Module", log in, and fill in the module information.

Supported login methods: **GitHub**, **Codeberg**, and **Yunhu** — choose any one of them.

Key information to fill in:
- Module name, description, and repository URL
- Minimum SDK version: if unsure, simply enter the version number of the [latest ErisPulse release](https://pypi.org/project/ErisPulse/)

Submissions take effect immediately, and users can install via the module source. The module will be marked as "Unverified" and changed to "Verified" once it passes review by maintainers.

> **About verification status**:
> - "Unverified" only means the module has not yet been officially reviewed; it does not indicate any problem with the module
> - When installing an unverified module via `epsdk install`, users will receive a risk warning and must confirm before the installation can continue

### 4. Manage Published Modules

After clicking "Submit Module" on the Module Store and logging in, switch to the "My Modules" tab, where you can:

- **Edit** — Modify the module description, repository URL, tags, and other information; the version number is automatically synced from PyPI
- **Delete** — Remove the module from the Module Store (irreversible)

> Modules that were just submitted may take a few minutes to appear in the "My Modules" list.

## Updating Published Modules

1. Update `version` in `pyproject.toml`
2. Rebuild and upload: `python -m build && python -m twine upload dist/*`
3. The Module Store will automatically sync the latest version from PyPI

Users can upgrade with `epsdk upgrade MyModule`.

## Pre-Publish Checklist

Before pushing to PyPI, please confirm the following items one by one:

### Code Quality

- [ ] All public APIs have type annotations (function signatures and return values)
- [ ] All public methods have docstrings (`"""..."""` format, including `:param` / `:return` / `:raises`)
- [ ] Passes `ruff check` (no warnings)
- [ ] Test coverage ≥ 80%
- [ ] All `pytest` test cases pass

### Compatibility

- [ ] `pyproject.toml` declares the minimum SDK version: `dependencies = ["ErisPulse>=x.y.z"]`
- [ ] The module declares the runtime minimum SDK version in `get_meta()` via `ModuleMeta(min_sdk_version="x.y.z")` (adapters use the class attribute `min_sdk_version`) — when the SDK in the user's environment is too old, the framework clearly reports an error and skips loading it, instead of throwing hard-to-diagnose runtime exceptions
- [ ] Tested on Python 3.10 / 3.11 / 3.12 / 3.13
- [ ] Tested on target operating systems (Windows / Linux / macOS, as applicable)
- [ ] No circular import dependencies

### Configuration

- [ ] If using declarative configuration (`ConfigClass` + `BaseConfig` / `BotAccountConfig`), configuration fields have `description` (i18n format recommended) and `ui` metadata
- [ ] If i18n translation keys are registered, all 5 languages are covered (zh-CN / zh-TW / en / ja / ru)
- [ ] Sensitive fields are marked with `secret=True`

### Documentation

- [ ] `README.md` includes installation instructions and basic usage examples
- [ ] `README.md` explains how to configure it (config file example + environment variables)
- [ ] `CHANGELOG.md` records all changes
- [ ] Adapters have updated platform feature documentation (supported Send types, event types, etc.)

### Publishing

- [ ] The version number in `pyproject.toml` has been updated
- [ ] Build passes: `python -m build`
- [ ] Pushed to PyPI: `python -m twine upload dist/*`
- [ ] Installation verified: `pip install ErisPulse-xxx && epsdk run`

## Development Mode Testing

Before the official release, you can test locally using editable mode:

```bash
epsdk install -e /path/to/MyModule
# or
pip install -e /path/to/MyModule
```

## FAQ

### Must package names start with `ErisPulse-`?

It is not mandatory, but strongly recommended. It helps users identify ErisPulse ecosystem packages on PyPI.

### Can a single package register multiple modules?

Yes. Simply configure multiple key-value pairs in `entry-points`:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### How long does the review take?

Usually completed within 1-3 business days. You can check the verification status under "My Modules" on the Module Store.

## Distributing Applications via Docker Images

If your application is not suitable for publishing to PyPI (e.g., it contains private dependencies or requires a pre-configured environment), you can publish a Docker image via **GitHub Container Registry (GHCR)**, allowing other users to start it with a single `docker pull`.

### Use Cases

- You have a **complete bot application** (module + configuration + entry script) and want one-click distribution
- The module/adapter depends on **private packages** or has a special installation process, making it unsuitable for PyPI
- You want to provide an **out-of-the-box** deployment solution to lower the barrier for users

### 1. Create a Dockerfile

Build on top of the official ErisPulse image; you only need to add your module:

```dockerfile
FROM erispulse/erispulse:latest

LABEL org.opencontainers.image.title="ErisPulse-MyModule" \
      org.opencontainers.image.description="Module description" \
      org.opencontainers.image.url="https://github.com/yourname/ErisPulse-MyModule" \
      org.opencontainers.image.source="https://github.com/yourname/ErisPulse-MyModule"

COPY pyproject.toml README.md ./
COPY MyModule/ ./MyModule/

RUN uv pip install --system -e .
```

If the module requires additional system dependencies (such as an SSH client), add the following after `RUN uv pip install`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` already includes ErisPulse, ErisPulse-Dashboard, the Python runtime, and uv, so there is no need to install them again.

### 2. Create a GitHub Actions Workflow

Create `.github/workflows/docker-publish.yml`:

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

      - name: Set up QEMU (multi-architecture support)
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
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

> `GITHUB_TOKEN` is automatically provided by GitHub Actions; there is no need to create the secret manually.

### 3. Trigger the Build

Pushing code or creating a tag will trigger an automatic build:

```bash
# Trigger by pushing to the main branch
git push origin main

# Or trigger by creating a tag
git tag v1.0.0
git push origin v1.0.0
```

You can also trigger it manually from the **Actions** page of the GitHub repository.

### 4. Set the Image to Public

GHCR images are **private** by default; you need to set them to Public on GitHub so other users can pull them without logging in:

1. Go to the repository → **Packages** → click the corresponding Package
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. User Usage

After the build completes, users can start it with a single `docker run` command:

```bash
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

### Publishing to Docker Hub as Well

Extend the workflow by adding a Docker Hub login step before the login step, and add the Docker Hub address to `images`:

```yaml
      - name: Log in to Docker Hub
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

> You need to add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` under the repository **Settings → Secrets**.

### Docker Image vs PyPI Publishing

| Feature | Docker Image (GHCR) | PyPI Publishing |
|------|---------------------|-----------|
| Distribution method | Run with a single `docker pull` | `pip install` + manual configuration |
| Scope | Complete applications/solutions | Individual modules/adapters |
| Private dependencies | Natively supported | Requires a private PyPI source |
| Module Store | Not applicable | Can be submitted to the Module Store |
| Multi-architecture | Supports amd64/arm64 | Architecture-independent |

The two approaches are not mutually exclusive — you can publish modules to the Module Store via PyPI while also providing an out-of-the-box Docker image via GHCR.

## Next Steps

### Ensure Quality Before Publishing

- [Module Testing (ErisPulse-Testing)](testing.md) — Run through the checklist above with automated tests first
- [Module Best Practices](modules/best-practices.md) / [Adapter Best Practices](adapters/best-practices.md) — Final engineering touches before publishing

### Help Users Get Started After Publishing

- [CLI Commands](../user-guide/cli-reference.md) — How `epsdk install` / `epsdk upgrade` behave on the user side
- [Platform Feature Guide](../platform-guide/README.md) — Where adapter authors maintain platform documentation