# Publishing and Module Store Guide

> [!TIP]
> **When to read this**: When you need to publish your work to PyPI / Module Store. Skip if not needed, as it does not affect the use of other features.

Publish your developed module or adapter to the ErisPulse Module Store, allowing other users to easily discover and install it.

## Module Store Overview

The ErisPulse Module Store is a centralized module registry. Users can browse, search, and install community-contributed modules and adapters using the CLI tool.

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

You can also visit the [ErisPulse official website](https://www.erisdev.com/#market) or the "Module List" section of [ErisPulse Workbench](https://workbench.erisdev.com/) to browse the module store online. All account, module management, and hosting domain features of the workbench are described in [ErisPulse Workbench](../ecosystem/workbench.md).

### Supported Submission Types

| Type | Description | Entry-point Group |
|------|-------------|-------------------|
| Module | Extend bot functionality, implement business logic | `erispulse.module` |
| Adapter | Connect to new messaging platforms | `erispulse.adapter` |

## Quick Publishing

The entire process requires only three steps: configure the project → publish to PyPI → submit to the module store.

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

> **Note**: Package names are recommended to start with `ErisPulse-` for easy identification by users. The entry-point key (e.g., `"MyModule"`) will serve as the module's access name in the SDK.

### 2. Publish to PyPI

```bash
# Build + Publish (requires PyPI account)
pip install build twine
python -m build
python -m twine upload dist/*
```

After successful publishing, verify the installation:

```bash
pip install ErisPulse-MyModule
```

### 3. Submit to Module Store (ErisPulse Workbench)

Module listing and certification are unified by **ErisPulse Workbench**: **[https://workbench.erisdev.com/](https://workbench.erisdev.com/)**. After submission, the module is dispatched to the module index repository via `repository_dispatch`, and once the workflow completes, it is added to the store (usually within a few minutes). The login, token, ownership claim, and hosting domain features of the workbench are described in [ErisPulse Workbench](../ecosystem/workbench.md).

#### Method 1: Web Submission (Recommended for First Use)

1. Open the workbench and log in with a **GitHub / Codeberg** account (historical modules can be claimed back via "Claim this module" on the module details page)
2. Click "Submit New Module" on the left → Fill in the form: name / type (module · adapter) / PyPI package name / description (≥10 characters) / author / repository address (github.com or codeberg.org) / category (1 Tool · 2 Entertainment · 3 Management · 4 Notification · 5 AI · 6 Platform · 7 Analysis) / tags / minimum SDK version
3. Submitting will take effect immediately and mark it as "Unverified" (indicating it has not yet been officially reviewed; users will receive a risk warning upon installation requiring confirmation); after passing the "Certification Review," it will be marked as "Verified"

#### Method 2: API Submission (CLI / CI Scenarios)

**① Generate Access Token**: On the workbench's "Open API → Access Token" page → Fill in the name → "Generate Token." The format is `epat_` + 40 hexadecimal digits, **displayed only once**; accounts with two-factor authentication enabled can check "No TOTP Code" to avoid requiring `totp_code` for sensitive interfaces.

**② Request Convention**:

```http
Authorization: Bearer epat_…
Content-Type: application/json
```

The request body must be a **UTF-8 encoded JSON**. Windows terminals default to GBK, and Chinese characters will be written as non-UTF-8 bytes, which the server will reject (error `415 ENCODING_INVALID` and indicating the problematic field) — first execute `chcp 65001`, or save the request body as a UTF-8 file and submit using `curl --data-binary @body.json`.

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

**④ Query and Manage**: `GET /api/modules/ops?name=MyModule&type=module` to check submission/audit progress; `POST /api/modules/manage` to edit/verify/delete; `POST /api/modules/batch` for batch operations. The complete endpoint list is available in the workbench's built-in "Usage Documentation" (token/ownership claim/module management/FAQ).

### 4. Manage Published Modules

Log in to the workbench "Module List" → Your module's details page, where you can edit description, repository, tags, etc. (version number is automatically synchronized from PyPI), delete modules, initiate ownership claims; API side uses `manage` / `batch` endpoints.

> Newly submitted modules may take a few minutes to appear in the list.

## Update Published Modules

1. Update `pyproject.toml`'s `version`
2. Rebuild and upload: `python -m build && python -m twine upload dist/*`
3. The module store will automatically synchronize the latest version from PyPI

Users can upgrade using `epsdk upgrade MyModule`.

## Pre-Publish Checklist

Before pushing to PyPI, please confirm the following items one by one:

### Code Quality

- [ ] All public APIs have type annotations (function signatures and return values)
- [ ] All public methods have docstrings (`"""..."""` format, including `:param` / `:return` / `:raises`)
- [ ] Passed `ruff check` (no warnings)
- [ ] Test coverage ≥ 80%
- [ ] Passed `pytest` all test cases

### Compatibility

- [ ] `pyproject.toml` declares the minimum SDK version: `dependencies = ["ErisPulse>=x.y.z"]`
- [ ] The module declares the minimum SDK version at runtime in `get_meta()`'s `ModuleMeta(min_sdk_version="x.y.z")` (adapters use class attribute `min_sdk_version`) — when the user's environment SDK is too low, the framework will clearly report an error and skip loading at the loading stage, rather than reporting a difficult-to-locate runtime exception
- [ ] Tested on Python 3.10 / 3.11 / 3.12 / 3.13
- [ ] Tested on the target operating system (Windows / Linux / macOS, if applicable)
- [ ] No circular import dependencies

### Configuration

- [ ] If using declarative configuration (`ConfigClass` + `BaseConfig` / `BotAccountConfig`), configuration fields have `description` (recommended i18n format) and `ui` metadata
- [ ] If registered i18n translation keys, all five languages (zh-CN / zh-TW / en / ja / ru) are covered
- [ ] Sensitive fields marked with `secret=True`

### Documentation

- [ ] `README.md` has installation instructions and basic usage examples
- [ ] `README.md` explains the configuration method (configuration file example + environment variables)
- [ ] `CHANGELOG.md` records all changes
- [ ] Adapter updates the platform feature documentation (supported Send types, event types, etc.)

### Publishing

- [ ] `pyproject.toml` version number has been updated
- [ ] Build passed: `python -m build`
- [ ] Uploaded to PyPI: `python -m twine upload dist/*`
- [ ] Installation verified: `pip install ErisPulse-xxx && epsdk run`

## Development Mode Testing

Before the official release, you can use editable mode to test locally:

```bash
epsdk install -e /path/to/MyModule
# or
pip install -e /path/to/MyModule
```

## Frequently Asked Questions

### Does the package name have to start with `ErisPulse-`?

No, it is not mandatory, but strongly recommended. This helps users identify ErisPulse ecosystem packages on PyPI.

### Can one package register multiple modules?

Yes. You can configure multiple key-value pairs in `entry-points`:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### How long does the review take?

Typically 1-3 working days. You can check the verification status in the module store "My Modules."

## Distributing Applications via Docker Images

If your application is not suitable for publishing to PyPI (e.g., it includes private dependencies or requires a pre-configured environment), you can distribute it via **GitHub Container Registry (GHCR)**, allowing other users to `docker pull` and start it with one click.

### Applicable Scenarios

- You have a **complete bot application** (module + configuration + entry script) and want to distribute it with one click
- The module/adapter depends on **private packages** or has a special installation process that is unsuitable for PyPI
- You want to provide an **out-of-the-box deployment solution** to lower the user's usage threshold

### 1. Create Dockerfile

Based on the ErisPulse official image, you only need to add your module:

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

> `erispulse/erispulse:latest` already includes ErisPulse, ErisPulse-Dashboard, Python runtime, and uv, so there is no need to install them again.

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

> `GITHUB_TOKEN` is automatically provided by GitHub Actions, no need to manually create a key.

### 3. Trigger Build

Push code or tag to trigger the build:

```bash
# Push to main branch to trigger
git push origin main

# Or tag to trigger
git tag v1.0.0
git push origin v1.0.0
```

You can also manually trigger it in the GitHub repository's **Actions** page.

### 4. Set Image to Public

GHCR images are **private** by default. You need to set them to **Public** in GitHub so other users can pull without logging in:

1. Go to the repository → **Packages** → Click the corresponding Package
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. User Usage

After the build is complete, users can start it with `docker run` in one line:

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

Extend the workflow by adding Docker Hub login before the login step, and add the Docker Hub address to `images`:

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

> You need to add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` in the repository **Settings → Secrets**.

### Docker Image vs PyPI Publishing

| Feature | Docker Image (GHCR) | PyPI Publishing |
|------|---------------------|-----------|
| Distribution Method | `docker pull` to run in one step | `pip install` + manual configuration |
| Applicability | Complete application/solution | Single module/adapter |
| Private Dependencies | Native support | Requires private PyPI source |
| Module Store | Not applicable | Can be submitted to module store |
| Multi-Architecture | Supports amd64/arm64 | Architecture-agnostic |

These two methods are not mutually exclusive—you can simultaneously publish your module to the module store via PyPI and provide an out-of-the-box Docker image via GHCR.

## Next Steps

### Ensure Quality Before Publishing

- [Module Testing (ErisPulse-Testing)](testing.md) — Use automated tests to run through the checklist above first
- [Module Best Practices](modules/best-practices.md) / [Adapter Best Practices](adapters/best-practices.md) — Engineering finishing touches before publishing

### Make It Usable After Publishing

- [CLI Commands](../user-guide/cli-reference.md) — User-side `epsdk install` / `epsdk upgrade` behavior
- [Platform Features Guide](../platform-guide/README.md) — Landing point for adapter authors to maintain platform documentation