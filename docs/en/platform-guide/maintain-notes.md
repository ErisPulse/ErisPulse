# Documentation Maintenance Instructions

This document is maintained by each adapter developer to document the differences and extended features of the adapter in relation to the OneBot12 standard.  
Adapter developers should update this document when releasing new versions.

## Update Requirements

1. Accurately describe the platform-specific send methods and parameters.
2. Provide detailed explanations of the differences from the OneBot12 standard.
3. Offer clear code examples and parameter descriptions.
4. Maintain uniform document formatting for easy user access.
5. Keep version information and maintainer contact details up to date.

## Documentation Structure Guidelines

### 1. Basic Information Section
Each platform feature documentation should include the following basic information:
```markdown
# Platform Name Adapter Documentation

Adapter Name: [Adapter class name]
Platform Overview: [Brief platform introduction]
Supported Protocol/API Version: [Specific protocol or API version]
Maintainer: [Maintainer name/team]
Corresponding Module Version: [Version number]
```

### 2. Supported Message Sending Types
List all supported sending methods and their parameters in detail:
```markdown
## Supported Message Sending Types

All sending methods are implemented using a fluent syntax, for example:
[Code Example]

The supported sending types include:
- Method 1: Description
- Method 2: Description
- ...

### Parameter Description
| Parameter | Type | Description |
|-----------|------|-------------|
| Parameter Name | Type | Description |
```

### 3. Platform-Specific Event Types
Describe the platform-specific event types and their formats in detail:
```markdown
## Platform-Specific Event Types

[Platform Name] events are converted to the OneBot12 protocol, where standard fields fully comply with the OneBot12 protocol, but there are the following differences:

### Core Differences
1. Platform-Specific Event Types:
   - Event Type 1: Description
   - Event Type 2: Description
2. Extended Fields:
   - Field Description

### Special Field Example
[JSON Example]
```

### 4. Extended Field Description
```markdown
## Extended Field Description

- All platform-specific fields are prefixed with `[platform]_`
- Original data is preserved in the `[platform]_raw` field
- [Other special field descriptions]
```

### 5. Configuration Options (if applicable)
```markdown
## Configuration Options

The [Platform Name] adapter supports the following configuration options:

### Basic Configuration
- Configuration Item 1: Description
- Configuration Item 2: Description

### Special Configuration
- Special Configuration Item 1: Description
```

## Content Writing Guidelines

### Code Example Guidelines
1. All code examples must be complete and runnable examples.
2. Use standard import methods:
```python
from ErisPulse.Core import adapter
[Adapter Instance] = adapter.get("[Adapter Name]")
```
3. Provide examples for various usage scenarios.

### Documentation Format Guidelines
1. Use standard Markdown syntax.
2. Use clear heading levels, with a maximum of 4 levels.
3. Use standard Markdown table format for tables.
4. Use appropriate language identifiers for code blocks.

### Version Update Notes
When updating the documentation, update the version information at the top of the document:
```markdown
## Document Information

- Corresponding Module Version: [New Version Number]
- Maintainer: [Maintainer Information]
- Last Updated: [Date]
```

## Quality Checklist

Before submitting documentation updates, please check the following:

- [ ] The document structure meets the specification requirements
- [ ] All code examples can run successfully
- [ ] Parameter descriptions are complete and accurate
- [ ] Event format examples match actual outputs
- [ ] Links and references are correct
- [ ] No grammar or spelling errors
- [ ] Version information has been updated
- [ ] Maintainer information is accurate

## Reference Documents

When writing, please refer to the following documents to ensure consistency:
- [OneBot12 Specification](https://12.onebot.dev/)
- [ErisPulse Core Concepts](../getting-started/basic-concepts.md)
- [Event Conversion Standard](../standards/event-conversion.md)
- [API Response Specification](../standards/api-response.md)
- [Other Platform Adapter Documentation](./)

## Contributing Process

1. Fork the [ErisPulse](https://github.com/ErisPulse/ErisPulse) repository
2. Modify the corresponding platform documentation under the `docs/platform-features/` directory
3. Ensure the documentation complies with the above specification requirements
4. Submit a Pull Request and provide a detailed explanation of the changes

If you have any questions, please contact the relevant adapter maintainer or ask in the project Issues.