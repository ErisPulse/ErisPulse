# Technical Standards

This document contains ErisPulse technical standards specifications to ensure consistency and compatibility between components.

## Standard Document List

1. [Session Types Standard](session-types.md) - ErisPulse session type definition and mapping specification
2. [Event Conversion Standard](event-conversion.md) - Platform event conversion spec, extension naming conventions, and message segment standards
3. [API Response Standard](api-response.md) - Standard for adapter API response formats and extension requirements
4. [Send Method Naming Conventions](send-method-spec.md) - Send class method naming, parameter specifications, and reverse conversion requirements

## Standard Overview

ErisPulse adopts OneBot12 as the core event standard, building upon this foundation with extensions and refinements.

### Core Principles

1. **Compatibility**: All standards must remain compatible with the OneBot12 standard
2. **Extensibility**: Platform-specific features are extended via prefixing to avoid conflicts
3. **Consistency**: Key fields such as timestamps and ID formats require unified handling
4. **Traceability**: Retain original data for debugging and issue troubleshooting

## Why Do We Need Standards?

### 1. Ensure Cross-Platform Compatibility

Event formats differ across various platforms, and standardized conversion ensures:
- Modular code only needs to be written once to run on all platforms
- Event handling logic remains consistent
- Reduces development and maintenance costs

### 2. Standardize API Interfaces

Unified API response formats ensure:
- Modules can handle API errors consistently
- Error messages are unified and easy to understand
- Returned data structures are consistent

### 3. Improve Code Quality

Standard specifications help:
- Maintain consistent code style
- Reduce naming conflicts
- Improve code readability

## Benefits of Following Standards

### For Adapter Developers

- Clear conversion rules
- Unified response formats
- Easy to debug and test

### For Module Developers

- Consistent event interfaces
- Predictable API behavior
- Simplified cross-platform development

### For End Users

- Stable system behavior
- Unified message formats
- Good compatibility

## Standard Compliance Checklist

### Event Conversion

- [ ] All standard fields are correctly mapped
- [ ] Platform-specific fields have been prefixed
- [ ] Timestamps have been converted to 10-digit second-level precision
- [ ] Raw data is saved in {platform}_raw
- [ ] Original event type is saved in {platform}_raw_type
- [ ] The alt_message for message segments has been generated

### API Response

- [ ] Includes the status field
- [ ] Includes the retcode field
- [ ] Includes the data field
- [ ] Includes the message_id field
- [ ] Includes the message field
- [ ] Return codes follow OneBot12 specifications

### Send Method Naming

- [ ] Uses PascalCase
- [ ] Returns a Task object
- [ ] Decorated methods return self
- [ ] Parameter naming complies with specifications

## Related Documentation

- [Platform Features Guide](../platform-guide/) - Understand the feature differences of each platform
- [Developer Guide](../developer-guide/) - Develop custom modules and adapters