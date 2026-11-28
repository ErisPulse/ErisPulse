# Style Guide

This directory contains engineering discipline and writing standards for the ErisPulse project.

## Document List

- [Glossary (Single Source of Truth)](glossary.md) - The sole definition of drift-prone terms such as Client/HttpClient, storage/env/StorageManager, BaseConfig/AdapterConfig, the three dimensions of scope, ownership, and service contract/catalog/whitelist
- [Comment Style Guidelines](docstring.md) - Formatting standards for method comments and docstrings, and the tag parsing contract
- [Engineering Robustness Rules](engineering.md) - Exception trace grading, log leveling, centralized behavior parameters, API contracts, singleton back-reference prohibitions, cleanup and rollback discipline, and testing discipline
- [Documentation and External Writing Rules](docs-writing.md) - Documentation writing style, version annotations, the three-part structure for README and release pages, scenario-based expression, and changelog writing

## Audience

- ErisPulse core contributors  
- Module and adapter developers  
- Contributors maintaining README and external pages  
- Developers who need to generate API documentation

## Relationship with Other Specifications

- [Technical Standards](../standards/) - The **technical** specification for adapters (session types, event transformations, API shapes); this directory is about **engineering and writing** discipline; the two are complementary and do not overlap.
- `CONTRIBUTING.md` - Contribution process and CI gates (the machine-checkable parts of the rules in this directory are enforced by gate scripts).
- `CHANGELOG.md` header "Writing Guidelines" - Detailed specification for change logs (this document only references it and does not repeat the main content).