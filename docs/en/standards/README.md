# Technical Standards

This document contains the technical standards specification for ErisPulse, ensuring consistency and compatibility between components.

## Standard Documentation List

1. [Session Type Standard](session-types.md) - Definition and mapping specification for ErisPulse session types
2. [Event Conversion Standard](event-conversion.md) - Platform event conversion specification, extension naming conventions, and message segment standards
3. [API Response Standard](api-response.md) - Adapter API response format standard and extension requirements
4. [Send Method Specification](send-method-spec.md) - Naming, parameter specifications for Send class methods, and reverse conversion requirements
5. [Request Action Specification](request-action-spec.md) - Request event field requirements, HandleRequest DSL, and adapter implementation requirements
6. [API Action Standard](api-action-spec.md) - Unified interface for OneBot12 standard API actions (information query/group management/message management/file operations)

## Standard Overview

ErisPulse adopts OneBot12 as its core event standard and extends and refines it.

### Core Principles

1. **Compatibility**: All standards must remain compatible with the OneBot12 standard
2. **Extensibility**: Platform-specific features are extended using prefixes to avoid conflicts
3. **Consistency**: Key fields such as timestamps and ID formats require unified handling
4. **Traceability**: Original data is retained for debugging and issue troubleshooting

## Why Are Standards Needed?

### 1. Ensure Cross-Platform Compatibility

Different platforms have varying event formats; standardized conversion ensures:
- Module code needs to be written only once to run on all platforms
- Event handling logic remains consistent
- Development and maintenance costs are reduced

### 2. Standardize API Interfaces

A unified API response format ensures:
- Modules can consistently handle API errors
- Error messages are uniform and easy to understand
- Return data structures are consistent

### 3. Improve Code Quality

Standards help:
- Maintain consistent code style
- Reduce naming conflicts
- Improve code readability

## Benefits of Following Standards

### For Adapter Developers

- Clear conversion rules
- Unified response format
- Easy debugging and testing

### For Module Developers

- Consistent event interface
- Predictable API behavior
- Simplified cross-platform development

### For End Users

- Stable system behavior
- Unified message format
- Good compatibility

## Standard Compliance Checklist

### Event Conversion

- [ ] All standard fields have been correctly mapped
- [ ] Platform-specific fields have been prefixed
- [ ] Timestamps have been converted to 10-digit second-level
- [ ] Original data is saved in {platform}_raw
- [ ] Original event type is saved in {platform}_raw_type
- [ ] alt_message for message segments has been generated
- [ ] Request events include the request_id field

### API Response

- [ ] Includes the status field
- [ ] Includes the retcode field
- [ ] Includes the data field
- [ ] Includes the message_id field
- [ ] Includes the message field
- [ ] Return codes follow the OneBot12 specification

### Send Method Naming

- [ ] Uses PascalCase naming convention
- [ ] Returns a Task object
- [ ] Modifier methods return self
- [ ] Parameter naming follows the specification

### Request Operations

- [ ] The HandleRequest class has implemented _do_accept / _do_reject
- [ ] Operations return the standard API response format
- [ ] Unsupported operations return retcode=10002

## Related Documents

- [Platform Features Guide](../platform-guide/) - Understand the feature differences between platforms
- [Developer Guide](../developer-guide/) - Develop custom modules and adapters