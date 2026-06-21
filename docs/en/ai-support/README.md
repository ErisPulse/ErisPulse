# AI-Assisted Development

ErisPulse provides two complementary AI-assisted development approaches, allowing AI to generate code based on the latest framework specifications:

- **Material Documentation**: A single large Markdown file, loaded once with context, suitable for full project development
- **MCP Server**: Allows AI to retrieve official documentation on demand, suitable for daily code completion and API lookup

| | Material Documentation | MCP Server |
|---|---|---|
| Format | A large Markdown file, **loaded once** | AI **retrieves on demand** |
| Context Cost | High (uses tokens) | Low (only fetches relevant fragments) |
| Timeliness | Updated with version releases | Real-time (GitHub pull + cache) |
| Suitable For | Large context window, full project development | Daily code completion, API lookup |
| Client | Any AI tool | Only clients supporting MCP |

The two approaches are not mutually exclusive: for large projects, both can be used simultaneously—Material Documentation as the foundation, and MCP as a safety net for missing information.

## Material Documentation

Material documentation is located in the `prompts/` directory and is divided into three types based on development scenarios:

| Document | Scenario | Description |
|------|------|------|
| **ErisPulse-ModuleDev.md** | Module Development | Covers the entire module development process (event handling, routing, lifecycle, etc.) |
| **ErisPulse-AdapterDev.md** | Adapter Development | Builds on module development, adding adapter core concepts, SendDSL, and platform adaptation guides |
| **ErisPulse-Full.md** | Full Stack Reference | All above content + complete user guide and API reference collection |

Access method: Directly obtain from the `prompts/` directory (synchronized with documentation updates), or download the corresponding version from [GitHub Releases](https://github.com/ErisPulse/ErisPulse/releases).

### Usage

1. Select the document based on your target (module → `ModuleDev`, adapter → `AdapterDev`, complex needs → `Full`)
2. Provide the document content as context to the AI: place it in the IDE workspace, paste directly in chat-based tools, or inject as a system message in API calls
3. Use the template below to describe your requirements; the more specific the description, the higher the quality of generated code

### Requirement Description Template

**Module:**

```
Please generate a complete code for a [Module Name] module based on the ErisPulse module development specification.

Function Description: [Core Function]
Events to listen to: [Message / Command / Notification / Request], Handling Logic: [Operation]
Required Configuration Items: [Key Name]: [Purpose] ([Required/Optional], Default Value: [Value])
Other Requirements: [Additional Constraints]
```

**Adapter:**

```
Please generate a complete code for a [Adapter Name] adapter based on the ErisPulse adapter development specification.

Platform Information: [Name], Communication Protocol: [WebSocket / WebHook / HTTP Polling], API Documentation: [Address]
Event Mapping: Platform Event [Type] → OneBot12 Mapping [Relationship]
Required Send Methods to Implement: [Text / Image / Voice ...]
Configuration Items: [Key Name]: [Purpose] ([Required/Optional])
```

## MCP Server

ErisPulse provides an official **MCP (Model Context Protocol) server** deployed at [`mcp.erisdev.com`](https://mcp.erisdev.com/). After integrating with an AI coding assistant that supports MCP (such as Claude Desktop, Cursor, etc.), the AI can directly **retrieve and consult the official ErisPulse documentation** while you write code, without manually pasting.

### Provided Tools

After integration, the AI will gain access to the following tools:

| Tool | Parameters | Description |
|------|------|------|
| **`search_docs`** | `query` (required), `top_k?=5`, `lang?=zh-CN` | BM25 keyword search, multiple keywords can be passed at once |
| **`read_document`** | `doc_path` (required), `lang?=zh-CN` | Reads the full Markdown of a single document |
| **`list_documents`** | `lang?=zh-CN` | Lists all document titles, paths, and categories in the current language |
| **`list_languages`** | — | Lists all supported languages and the number of documents |

Supported languages: `zh-CN` / `en` / `zh-TW` / `ja` / `ru`. Search tips: use **multiple keywords** instead of full sentences, for example `command registration event listening` is better than `how to register a command`.

### Integrating with Claude Desktop

Edit the configuration file (macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`; Windows: `%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "erispulse": {
      "url": "https://mcp.erisdev.com/"
    }
  }
}
```

> Requires Claude Desktop 0.85+. For older versions, use the `mcp-remote` bridge: `{ "command": "npx", "args": ["mcp-remote", "https://mcp.erisdev.com/"] }`.

### Integrating with Cursor

Edit `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` within the project:

```json
{
  "mcpServers": {
    "erispulse": {
      "url": "https://mcp.erisdev.com/"
    }
  }
}
```

The service is publicly accessible by default, no token required. To prevent abuse, there is an IP rate limit (60 requests per minute per IP). The worker source code is in the `workers` folder of this repository, supporting self-deployment.

## Frequently Asked Questions

**The generated code does not meet expectations?**  
Check if the complete documentation was provided; add more details in the requirements (input/output examples, boundary conditions); ask the AI to generate step-by-step (first skeleton, then functionality); refer to the [examples/](../../examples/) directory for supplementary context.

**After integrating MCP, the AI did not call `search_docs`?**  
Confirm that the client has loaded this server (after restarting Claude Desktop, an icon should appear in the bottom-right corner); some clients require explicit prompt instructions such as "use the ErisPulse documentation tool to verify the API."

## Next Steps

- [Getting Started with Module Development](../developer-guide/modules/getting-started.md) -- A complete tutorial for manual module development
- [Getting Started with Adapter Development](../developer-guide/adapters/getting-started.md) -- A complete tutorial for manual adapter development
- [Example Code](../../examples/) -- Reference existing module and adapter implementations
- [Module Builder](https://www.erisdev.com/builder.html) -- A browser-based visual AI module generator