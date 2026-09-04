# Technical Standards

This document contains the technical standards specification for ErisPulse, ensuring consistency and compatibility between components.

## Standard Documentation List

1. [Session Type Standard](session-types.md) - ErisPulse session type definition and mapping specification
2. [Event Conversion Standard](event-conversion.md) - Platform event conversion specification, extension naming convention, and message segment standard
3. [API Response Standard](api-response.md) - Adapter API response format standard and extension requirements
4. [Send Method Specification](send-method-spec.md) - Naming, parameter specification for Send class methods, and reverse conversion requirements
5. [Request Action Specification](request-action-spec.md) - Request event field requirements, HandleRequest DSL, and adapter implementation requirements
6. [API Action Standard](api-action-spec.md) - Unified interface for OneBot12 standard API actions (user/group/channel/message management/file with chunking/meta actions)

## Standard Overview

ErisPulse adopts OneBot12 as its core event standard, and extends and refines it based on this foundation.

### Core Principles

1. **Compatibility**: All standards must remain compatible with the OneBot12 standard.
2. **Extensibility**: Platform-specific features are extended using prefixes to avoid conflicts.
3. **Consistency**: Critical fields such as timestamps and ID formats must be uniformly handled.
4. **Traceability**: Original data is retained for debugging and issue troubleshooting.

## Why Do We Need Standards?

### 1. Ensure Cross-Platform Compatibility

Different platforms have varying event formats. Standardized transformation ensures:
- Module code needs to be written only once and can run on all platforms
- Event handling logic remains consistent
- Development and maintenance costs are reduced

### 2. Standardize API Interfaces

A unified API response format ensures:
- Modules can consistently handle API errors
- Error messages are uniform and easy to understand
- Return data structures remain consistent

### 3. Improve Code Quality

Standard specifications help:
- Maintain consistent code style
- Reduce naming conflicts
- Improve code readability

## Benefits of Following Standards

### For Adapter Developers

- Clear conversion rules
- Unified response format
- Easy to debug and test

### For Module Developers

- Consistent event interface
- Predictable API behavior
- Simplified cross-platform development

### For End Users

- Stable system behavior
- Unified message format
- Good compatibility

## Standard Compliance Checklist

### Event Transformation

- [ ] All standard fields have been correctly mapped
- [ ] Platform-specific fields have been prefixed
- [ ] Timestamps have been converted to 10-digit second-level
- [ ] Raw data has been saved in {platform}_raw
- [ ] Raw event type has been saved in {platform}_raw_type
- [ ] alt_message for message segments has been generated
- [ ] Request events include the request_id field

### API Response

- [ ] Contains status field
- [ ] Contains retcode field
- [ ] Contains data field
- [ ] Contains message_id field
- [ ] Contains message field
- [ ] Return codes follow the OneBot12 specification

### Send Method Naming

- [ ] Uses PascalCase naming convention
- [ ] Returns a Task object
- [ ] Modifier methods return self
- [ ] Parameter names follow the specification

### Request Operations

- [ ] HandleRequest class has implemented _do_accept / _do_reject
- [ ] Operation returns standard API response format
- [ ] Unsupported operations return retcode=10002

## Related Documentation

- [Platform Features Guide](../platform-guide/) - Learn about the feature differences across platforms
- [Developer Guide](../developer-guide/) - Develop custom modules and adapters