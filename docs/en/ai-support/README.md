# AI-Assisted Development

ErisPulse provides pre-built AI documentation assets that you can provide as context to AI models, enabling the generation of module and adapter code that complies with the framework specifications.

## Documentation Assets

The documentation assets are located in the `prompts/` subdirectory of this directory and are categorized by development scenarios:

| Document Name | Applicable Scenario | Content Size | Recommendation |
|---------------|---------------------|--------------|----------------|
| **ErisPulse-ModuleDev.md** | Module Development | Medium | Covers the entire module development workflow, suitable for most scenarios |
| **ErisPulse-AdapterDev.md** | Adapter Development | Medium | Covers the entire adapter development workflow, including platform adapter specifications |
| **ErisPulse-Full.md** | Full Reference | Large | Complete collection of development documentation, requires models with large context windows |

### Coverage of Each Document

**ModuleDev** includes: basic concepts, introduction to event handling, core concepts of module development, Event wrapper class, Conversation multi-turn dialog, MessageBuilder, routing system, lifecycle management, lazy loading system, session type standards, and module publishing process.

**AdapterDev** includes: the above basic content, plus core concepts of adapter development, SendDSL fluent interface, event converter design, three technical standards (event conversion, API response, send method), complete platform adapter guides, and documentation string conventions.

**Full** includes: all the above content, plus a complete user guide (installation, configuration, deployment), full API reference, and known issues tracking. Only recommended for models with context windows >= 128K tokens.

### Getting the Latest Version

The documentation assets are automatically updated with framework releases. You can obtain them via:

- Directly from the `prompts/` directory (synchronized with documentation updates)
- Download from [GitHub Releases](https://github.com/ErisPulse/ErisPulse/releases) for the corresponding version

## Usage Steps

### 1. Select the Documentation Asset

Choose the appropriate document based on your development goal:

- Developing functional modules → `ErisPulse-ModuleDev.md`
- Developing platform adapters → `ErisPulse-AdapterDev.md`
- Uncertain or complex requirements → `ErisPulse-Full.md` (ensure the model has sufficient context window)

### 2. Provide Context

Provide the selected documentation asset to the AI, depending on the tool you are using:

- **IDE-integrated AI (Copilot / Cursor)**: Place the document in the workspace, or paste it directly into the conversation
- **Conversational AI (ChatGPT / Claude)**: Paste the document content at the beginning of the conversation and inform the AI "Please answer questions based on the following document as a knowledge base"
- **API calls**: Inject the document as a system message or context

### 3. Write a Requirement Description

Use the templates below to describe your requirements. Fill in the details and send them to the AI. The more specific the description, the higher the quality of the generated code.

### 4. Verify the Generated Results

After the AI generates the code, it is recommended to:

1. Check if the code inherits the correct base class (`BaseModule` or `BaseAdapter`)
2. Confirm that event handlers use the correct decorators (`@message.on_message`, etc.)
3. Run `epsdk create module` or `epsdk create adapter` to create the project skeleton, and fill the generated code into the corresponding files
4. Execute tests to verify that the functionality works as expected

## Requirement Description Templates

### Module Requirement Template

```
Please generate the complete code for a [Module Name] module based on the ErisPulse module development specification.

Functional Description:
[Describe the core functionality of the module]

Events to Listen To:
- Event Type: [Message/Command/Notice/Request]
- Handling Logic: [Describe the operations executed when the event is triggered]

Required Configuration Items:
- [Configuration Key]: [Purpose Description] ([Required/Optional], Default Value: [Value])

Additional Requirements:
- [Additional features or constraints]
```

### Adapter Requirement Template

```
Please generate the complete code for an [Adapter Name] adapter based on the ErisPulse adapter development specification.

Platform Information:
- Platform Name: [Name]
- Communication Protocol: [WebSocket/WebHook/HTTP Polling]
- API Documentation URL: [If applicable]

Event Conversion:
- Platform Event Types: [List the main event types of the platform]
- OneBot12 Mapping: [Describe the mapping of platform events to the OB12 standard]

Implemented Send Methods:
- [Text/Image/Voice message types]: [Whether implementation is required]

Configuration Items:
- [Configuration Key]: [Purpose Description] ([Required/Optional])
```

## Frequently Asked Questions

**What AI tools are recommended?**

- **IDE-integrated tools**: Cursor, VS Code + Copilot —— Can directly manipulate the file system, suitable for project-level development
- **Conversational tools**: ChatGPT, Claude —— Suitable for rapid prototyping and single-file generation
- **API calls**: Suitable for batch generation or CI integration scenarios

**What should I do if the generated code does not meet expectations?**

1. Check if the complete and correct documentation asset was provided
2. Supplement more details in the requirement description (specific input/output examples, edge cases, etc.)
3. Ask the AI to generate step-by-step: first generate the skeleton code, confirm it is correct, then gradually add functionality
4. Refer to the example code in the [examples/](../../examples/) directory and provide the examples as supplementary context

**How can I improve the generation quality?**

- Clearly specify the module name and the base class to inherit in the requirement
- Provide specific message format examples (platform raw events → desired OB12 format)
- Request the AI to also generate test code
- For adapters, provide key interface information from the platform API documentation as supplementary context

## Next Steps

- [Module Development Guide](../developer-guide/modules/getting-started.md) -- Complete tutorial for manual module development
- [Adapter Development Guide](../developer-guide/adapters/getting-started.md) -- Complete tutorial for manual adapter development
- [Example Code](../../examples/) -- Reference existing module and adapter implementations