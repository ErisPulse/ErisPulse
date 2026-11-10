# Technical Standards

> [!TIP]
> **When to read this**: When you are developing or modifying an adapter and need to confirm whether event transformations, API responses, send methods, etc. comply with ErisPulse's cross-platform standards, refer to the corresponding specifications in this section. If you're unsure where to start, read the overview below first.

> **Overview**: [Adapter Standardization Guide](standardization-guide.md) —— Standardization principles, standard map, naming conventions, difference handling patterns, and developer Checklist. Please read it first for new adapters or new capabilities.

This document contains the technical standards of ErisPulse to ensure consistency and compatibility among components.

## Standard Documentation List


1. [Session Type Standard](session-types.md) - ErisPulse session type definitions and mapping specifications
2. [Event Conversion Standard](event-conversion.md) - Platform event conversion specifications, extension naming conventions, and message segment standards
3. [API Response Standard](api-response.md) - Adapter API response format standards and extension requirements
4. [Send Method Specification](send-method-spec.md) - Send class method naming, parameter specifications, and reverse conversion requirements
5. [Request Action Specification](request-action-spec.md) - Request event field requirements, Request DSL (approve/reject), request type context retention for heterogeneous endpoints, and adapter implementation requirements
6. [API Action Standard](api-action-spec.md) - Unified interface for OneBot12 standard API actions (user/group/channel/message management/file including chunking/meta actions)
7. [Adapter Standardization Guide (Overview)](standardization-guide.md) - Standardization principles/workflows/naming rules + interactive component standards (button keyboards/interaction callback events) and their mappings across platforms

## Standard Overview

ErisPulse adopts OneBot12 as its core event standard, and extends and refines it based on this foundation.

### Core Principles

1. **Compatibility**: All standards must remain compatible with the OneBot12 standard.
2. **Extensibility**: Platform-specific features are extended using prefixes to avoid conflicts.
3. **Consistency**: Key fields such as timestamps and ID formats must be uniformly handled.
4. **Traceability**: Original data is retained for debugging and issue troubleshooting.

## Why is a Standard Needed?

### 1. Ensure Cross-Platform Compatibility

Event formats vary across different platforms. Standardized conversion ensures:
- Module code needs to be written only once and can run on all platforms
- Event handling logic remains consistent
- Development and maintenance costs are reduced

### 2. Standardize API Interfaces

A unified API response format ensures:
- Modules can consistently handle API errors
- Error messages are uniform and easy to understand
- Return data structures are consistent

### 3. Improve Code Quality

Standardized specifications help:
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
- Uniform message format
- Good compatibility

## Standards Compliance Checklist


### Event Conversion


- [ ] All standard fields are correctly mapped
- [ ] Platform-specific fields are prefixed
- [ ] Timestamps are converted to 10-digit second-level values
- [ ] Raw data is saved in {platform}_raw
- [ ] Raw event types are saved in {platform}_raw_type
- [ ] alt_message has been generated for message segments
- [ ] Request events include the request_id field

### API Response


- [ ] Contains the status field
- [ ] Contains the retcode field
- [ ] Contains the data field
- [ ] Contains the message_id field
- [ ] Contains the message field
- [ ] Return codes follow the OneBot 12 specification

### Send Method Naming


- [ ] Uses PascalCase naming convention
- [ ] Returns a Task object
- [ ] Modifier methods return self
- [ ] Parameter naming follows the specification

### Media Sending (Image / Voice / Video / File)


- [ ] The `file` parameter must support all forms: HTTP(S) URL / local path / `bytes`
- [ ] The `file` parameter should support as many forms as possible: `file://` URI / Base64 / Data URI (when a form cannot be supported, return `retcode=10002` following the fallback ladder)
- [ ] The form detection order follows the specification (bytes → URL → `file://` → path)
- [ ] The `File` filename is generated following the derivation order (explicit `filename` > URL basename > path basename > platform default)
- [ ] Platform media limitations are declared in the adapter documentation
- [ ] Unsupported media types are handled per the fallback ladder (fall back to a closely-related type or return `retcode=10002`; no exceptions thrown, no silent drops)

> For the detailed protocol, see [Send Method Specification §2.1](send-method-spec.md#21-media-message-send-protocol-image--voice--video--file)

### Request Operations


- [ ] The Request inner class has overridden _do_accept / _do_reject (do not override the public entry points accept()/reject())
- [ ] Operations return the standard API response format
- [ ] Unsupported operations return retcode=10002

## Related Documentation

- [Platform Features Guide](../platform-guide/) - Learn about the feature differences between platforms
- [Developer Guide](../developer-guide/) - Develop custom modules and adapters