# Publishing and Module Store Guide

> [!TIP]
> **When to read this** : When publishing your work to PyPI / the module store. Skip if not needed, as it does not affect the use of other features.

Publish your developed module or adapter to the ErisPulse module store so other users can easily discover and install it.

## Overview of the Module Store

The ErisPulse module store is a centralized module registry where users can browse, search, and install community-contributed modules and adapters using the CLI tool.

### Browsing and Discovery

```bash
# List all available packages remotely
epsdk list-remote

# List only modules
epsdk list-remote -t modules

# List only adapters
epsdk list-remote -t adapters

# Force refresh the remote package list
epsdk list-remote -r
```

You can also visit the [ErisPulse official website](https://www.erisdev.com/#market) or the "Module List" section of [ErisPulse Workbench](https://workbench.erisdev.com/) to browse the module store online.

### Supported Submission Types

| Type | Description | Entry-point Group |
|------|-------------|-------------------|
| Module | Extends bot functionality, implements business logic | `erispulse.module` |
| Adapter | Connects to new messaging platforms | `erispulse.adapter` |

## Quick Publishing

The entire process only requires three steps: configure the project → publish to PyPI → submit to the module store.

### 1. Configure pyproject.toml

Ensure the project directory contains `pyproject.toml` and `README.md`, and configure entry-points according to the type:

#### Module

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Module feature description"
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
description = "Adapter feature description"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **Note**: Package names are recommended to start with `ErisPulse-` for easy identification. The entry-point key (e.g., `"MyModule"`) will serve as the module's access name in the SDK.

### 2. Publish to PyPI

```bash
# Build + publish (requires a PyPI account)
pip install build twine
python -m build
python -m twine upload dist/*
```

After successful publishing, verify installation:

```bash
pip install ErisPulse-MyModule
```

### 3. Submit to the Module Store (ErisPulse Workbench)

Module inclusion and certification are handled by **ErisPulse Workbench**: **[https://workbench.erisdev.com/](https://workbench.erisdev.com/)**. After submission, a `repository_dispatch` is sent to the module index repository, and the workflow completes, adding the module to the store (usually within a few minutes).

#### Method 1: Web Submission (Recommended for First-Time Use)

1. Open the workbench and log in with a **GitHub / Codeberg** account (historical modules can be claimed via the "Claim This Module" option on the module details page).
2. On the left, select "Submit New Module" → fill in the form: Name / Type (module · adapter) / PyPI package name / Description (≥10 characters) / Author / Repository URL (github.com or codeberg.org) / Category (1 Tool · 2 Entertainment · 3 Management · 4 Notification · 5 AI · 6 Platform · 7 Analysis) / Tags / Minimum SDK version.
3. Submission takes effect immediately and is marked as "Unverified" (indicating it has not yet been officially reviewed; users will receive a risk prompt requiring confirmation upon installation); after passing "Certification Review," it is marked as "Verified."

#### Method 2: API Submission (CLI / CI Scenarios)

**① Generate Access Token**: In the workbench, navigate to "Open API → Access Tokens" → fill in the name → "Generate Token." The format is `epat_` + 40 hexadecimal digits, **displayed only once during generation**; accounts with two-step verification can check "No Dynamic Code" to avoid requiring `totp_code` for sensitive interfaces.

**② Request Conventions**:

```http
Authorization: Bearer epat_…
Content-Type: application/json
```

The request body must be **UTF-8 encoded JSON**. Windows terminals default to GBK, causing Chinese characters to be written as non-UTF-8 bytes, which the server directly rejects (error `415 ENCODING_INVALID` with the problematic field indicated) — first execute `chcp 65001`, or save the request body as a UTF-8 file and submit using `curl --data-binary @body.json`.

**③ Submit Module**:

```bash
curl -X POST https://workbench.erisdev.com/api/modules/submit \
  -H "Authorization: Bearer epat_…" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyModule",
    "type": "module",
    "package": "ErisPulse-MyModule",
    "description": "Module description, at least 10 characters",
    "author": "Your Name",
    "repository": "https://github.com/you/MyModule",
    "category": 1,
    "tags": ["Tool"],
    "i18n": ["zh", "en"],
    "min_sdk_version": ">=2.7.0"
  }'
```

**④ Query and Manage**: `GET /api/modules/ops?name=MyModule&type=module` checks submission and review progress; `POST /api/modules/manage` edits, validates, or deletes; `POST /api/modules/batch` performs batch operations. The full endpoint list is available in the workbench's built-in "Usage Documentation" (token / ownership claim / module management / FAQ).

### 4. Manage Published Modules

Log in to the workbench "Module List" → your module details page, where you can edit description, repository, tags, etc. (version numbers are automatically synchronized from PyPI), delete modules, or initiate ownership claims; API-side operations use the `manage` / `batch` endpoints.

> Newly submitted modules may take a few minutes to appear in the list.

## Update Published Modules

1. Update the `version` in `pyproject.toml`
2. Rebuild and upload: `python -m build && python -m twine upload dist/*`
3. The module store will automatically sync the latest version from PyPI

Users can upgrade using `epsdk upgrade MyModule`.

## Pre-Publish Checklist

Before pushing to PyPI, please confirm the following items one by one:

### Code Quality

- [ ] All public APIs have type annotations (function signatures and return values)
- [ ] All public methods have docstrings (`"""..."""` format, including `:param` / `:return` / `:raises`)
- [ ] Passed `ruff check` (no warnings)
- [ ] Test coverage ≥ 80%
- [ ] Passed `pytest` all tests

### Compatibility

- [ ] `pyproject.toml` declares the minimum SDK version: `dependencies = ["ErisPulse>=x.y.z"]`
- [ ] Module declares the minimum SDK version at runtime in `get_meta()` with `ModuleMeta(min_sdk_version="x.y.z")` (adapters use class attribute `min_sdk_version`) — if the user's environment has an older SDK, the framework will report an error at load time and skip, rather than throwing a hard-to-locate runtime exception
- [ ] Tested on Python 3.10 / 3.11 / 3.12 / 3.13
- [ ] Tested on target operating systems (Windows / Linux / macOS, if applicable)
- [ ] No circular import dependencies

### Configuration

- [ ] If using declarative configuration (`ConfigClass` + `BaseConfig` / `BotAccountConfig`), configuration fields have `description` (recommended i18n format) and `ui` metadata
- [ ] If i18n translation keys are registered, all 5 languages (zh-CN / zh-TW / en / ja / ru) are covered
- [ ] Sensitive fields are marked with `secret=True`

### Documentation

- [ ] `README.md` has installation instructions and basic usage examples
- [ ] `README.md` explains the configuration method (configuration file example + environment variables)
- [ ] `CHANGELOG.md` records all changes
- [ ] Adapter updates platform feature documentation (supported Send types, event types, etc.)

### Publishing

- [ ] `pyproject.toml` version number has been updated
- [ ] Build succeeded: `python -m build`
- [ ] Pushed to PyPI: `python -m twine upload dist/*`
- [ ] Installation verified: `pip install ErisPulse-xxx && epsdk run`

## Development Mode Testing

Before formal release, you can test locally in editable mode:

```bash
epsdk install -e /path/to/MyModule
# or
pip install -e /path/to/MyModule
```

## Frequently Asked Questions

### Must package names start with `ErisPulse-`?

Not mandatory, but strongly recommended. This helps users identify packages in the ErisPulse ecosystem on PyPI.

### Can one package register multiple modules?

Yes. Configure multiple key-value pairs in `entry-points`:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### How long does the review take?

Typically within 1-3 business days. You can check the verification status in the module store "My Modules" section.

## Distributing Applications via Docker Images

If your application is not suitable for publishing to PyPI (e.g., containing private dependencies, requiring pre-configured environments), you can distribute it via **GitHub Container Registry (GHCR)**, allowing other users to `docker pull` and launch it with one click.

### Applicable Scenarios

- You have a **complete bot application** (module + configuration + entry script) and want to distribute it with one click
- Your module/adapter depends on **private packages** or has special installation procedures, making it unsuitable for PyPI
- You want to provide an **out-of-the-box** deployment solution, lowering the user's entry barrier

### 1. Create Dockerfile

Based on the ErisPulse official image, simply add your module:

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

If the module requires additional system dependencies (e.g., SSH client), add them after `RUN uv pip install`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` already includes ErisPulse, ErisPulse-Dashboard, Python runtime, and uv, so no need to install them again.

### 2. Create GitHub Actions Workflow

In `.github/workflows/docker-publish.yml`, create:

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

> `GITHUB_TOKEN` is automatically provided by GitHub Actions, no need to manually create a key.

### 3. Trigger Build

Push code or tag to automatically build:

```bash
# Push to main branch to trigger
git push origin main

# Or tag to trigger
git tag v1.0.0
git push origin v1.0.0
```

You can also manually trigger it in the GitHub repository's **Actions** page.

### 4. Set Image to Public

GHCR images are private by default; you need to change them to public in GitHub so others can pull without logging in:

1. Go to the repository → **Packages** → click the corresponding package
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. User Usage

After building, users can start with `docker run` in one line:

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

### Publish Simultaneously to Docker Hub

Extend the workflow by adding Docker Hub login before the login step, and add Docker Hub address to `images`:

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

> You need to add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` in the repository **Settings → Secrets**.

### Docker Image vs PyPI Publishing

| Feature | Docker Image (GHCR) | PyPI Publishing |
|------|---------------------|-----------|
| Distribution Method | `docker pull` one-click run | `pip install` + manual configuration |
| Applicability | Complete applications/solutions | Single modules/adapters |
| Private Dependencies | Native support | Requires private PyPI source |
| Module Store | Not applicable | Can submit to module store |
| Multi-Architecture | Supports amd64/arm64 | Architecture-agnostic |

The two methods are not conflicting—you can simultaneously publish modules to the module store via PyPI and provide out-of-the-box Docker images via GHCR.

## Next Steps

### Ensure Quality Before Publishing

- [Module Testing (ErisPulse-Testing)](testing.md) — Run the checklist above with automated tests first
- [Module Best Practices](modules/best-practices.md) / [Adapter Best Practices](adapters/best-practices.md) — Engineering finishing touches before publishing

### Make It Usable After Publishing

- [CLI Commands](../user-guide/cli-reference.md) — User-side `epsdk install` / `epsdk upgrade` behavior
- [Platform Features Guide](../platform-guide/README.md) — Landing point for adapter authors to maintain platform documentation