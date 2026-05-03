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
name