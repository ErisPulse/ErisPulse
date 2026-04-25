# Publishing and Module Store Guide

Publish your developed modules or adapters to the ErisPulse Module Store, allowing other users to easily discover and install them.

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

## Publishing Process

The entire publishing process is divided into four steps: Prepare Project → Publish to PyPI → Submit to Module Store → Review and Launch.

### Step 1: Prepare Project

Ensure your project contains the following files:

```
MyModule/
├── pyproject.toml      # Project configuration (required)
├── README.md           # Project description (required)
├── LICENSE             # Open source license (recommended)
└── MyModule/
    ├── __init__.py     # Package entry point
    └── ...
```

### Step 2: Configure pyproject.toml

According to the type you want to publish, correctly configure `entry-points`:

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

> **Note**: It's recommended that package names start with `ErisPulse-` for easy user recognition. The entry-point key name (such as `"MyModule"`) will be used as the access name for the module in the SDK.

### Step 3: Publish to PyPI

```bash
# Install build tools
pip install build twine

# Build distribution packages
python -m build

# Publish to PyPI
python -m twine upload dist/*
```

After successful publication, confirm that your package can be installed via `pip install`:

```bash
pip install ErisPulse-MyModule
```

### Step 4: Submit to ErisPulse Module Store

After confirming your package is published to PyPI, go to [ErisPulse-ModuleRepo](https://github.com/ErisPulse/ErisPulse-ModuleRepo/issues/new?template=module_submission.md) to submit your application.

Fill in the following information:

#### Submission Type

Select the type you want to submit:
- Module
- Adapter

#### Basic Information

| Field | Description | Example |
|------|------|------|
| **Name** | Module/Adapter name | Weather |
| **Description** | Brief functional description | Weather query module supporting global cities |
| **Author** | Your name or GitHub username | MyName |
| **Repository URL** | Code repository URL | https://github.com/MyName/MyModule |

#### Technical Information

| Field | Description |
|------|------|
| **Minimum SDK Version Requirement** | e.g. `>=2.0.0` (if applicable) |
| **Dependencies** | Additional dependencies besides ErisPulse (if applicable) |

#### Tags

Separate with commas to help users search and discover your module. For example: `weather, query, tool`

#### Checklist

Before submitting, please confirm:
- Code follows ErisPulse development standards
- Contains appropriate documentation (README.md)
- Contains test cases (if applicable)
- Published on PyPI

### Step 5: Review and Launch

After submission, maintainers will review your application. Review points:

1. The package can be installed normally from PyPI
2. Entry-point configuration is correct and can be properly discovered by the SDK
3. Functionality matches the description
4. No security issues or malicious code
5. No significant conflicts with existing modules

After passing the review, your module will automatically appear in the Module Store.

## Updating Published Modules

When you update a module version:

1. Update `version` in `pyproject.toml`
2. Rebuild and upload to PyPI:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```
3. The Module Store will automatically sync the latest version information from PyPI

Users can upgrade using the following command:

```bash
epsdk upgrade MyModule
```

## Development Mode Testing

Before official publication, you can test locally in editable mode:

```bash
# Install in editable mode
epsdk install -e /path/to/MyModule

# Or use pip
pip install -e /path/to/MyModule
```

## FAQ

### Q: Must package names start with `ErisPulse-`?

Not mandatory, but strongly recommended. This helps users identify ErisPulse ecosystem packages on PyPI.

### Q: Can a single package register multiple modules?

Yes. Configure multiple key-value pairs in `entry-points`:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### Q: How to specify minimum SDK version requirements?

Set in `dependencies` in `pyproject.toml`:

```toml
dependencies = [
    "ErisPulse>=2.0.0",
]
```

The Module Store will check version compatibility to prevent users from installing incompatible modules.

### Q: How long does the review take?

Usually completed within 1-3 business days. You can check the review progress in the Issue.