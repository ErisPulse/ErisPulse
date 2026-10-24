# AI-Assisted Development

ErisPulse provides two complementary AI-assisted development methods, allowing AI to generate code based on the latest framework specifications:

- **Material Documentation**: A large Markdown file, loaded into context at once, suitable for full project development
- **MCP Server**: Allows AI to retrieve official documentation on demand, suitable for daily code completion and API lookup

| | Material Documentation | MCP Server |
|---|---|---|
| Format | A large Markdown file, **loaded at once** | AI **retrieves on demand** |
| Context Cost | High (consumes tokens) | Low (only retrieves relevant snippets) |
| Timeliness | Updated with version releases | Real-time (GitHub pull + cache) |
| Suitable For | Large context window, full project development | Daily code completion, API lookup |
| Client | Any AI tool | Only clients supporting MCP |

The two methods are not conflicting: when developing large projects, both can be used simultaneously—material documentation as the foundation, and MCP for on-demand lookup and error checking.

## Material Documentation

The material documentation is located in the `prompts/` directory and is divided into three types based on development scenarios:

| Document | Scenario | Description |
|----------|----------|-------------|
| **ErisPulse-ModuleDev.md** | Module Development | Covers the entire module development workflow (event handling, routing, lifecycle, etc.) |
| **ErisPulse-AdapterDev.md** | Adapter Development | Builds upon module development, adding core adapter concepts, SendDSL, and platform adaptation guidelines |
| **ErisPulse-Full.md** | Full-Stack Reference | All the above content plus a complete user guide and API reference collection |

Access method: Directly obtain from the `prompts/` directory (synchronized with the documentation), or download the corresponding version from [GitHub Releases](https://github.com/ErisPulse/ErisPulse/releases).

### Usage

1. Select the appropriate document based on your target (Module → `ModuleDev`, Adapter → `AdapterDev`, Complex needs → `Full`)
2. Provide the document content as context to the AI: place it in the workspace within your IDE, paste directly for chat-based interactions, or inject as a system message for API calls
3. Describe your requirements using the template below; the more specific the description, the higher the quality of the generated output

### Requirement Description Template

**Module:**

```
Please generate a complete code for a [Module Name] module based on the ErisPulse module development specification.

Function Description: [Core Functionality]
Events to be listened to: [Message / Command / Notification / Request], Processing Logic: [Operation]
Required Configuration Items: [Key Name]: [Purpose] ([Required/Optional], Default Value: [Value])
Other Requirements: [Additional Constraints]
```

**Adapter:**

```
Please generate a complete code for an [Adapter Name] adapter based on the ErisPulse adapter development specification.

Platform Information: [Name], Communication Protocol: [WebSocket / WebHook / HTTP Polling], API Documentation: [URL]
Event Mapping: Platform Event [Type] → OneBot12 Mapping [Relationship]
Send Methods to be Implemented: [Text / Image / Voice ...]
Configuration Items: [Key Name]: [Purpose] ([Required/Optional])
```

## MCP Server

ErisPulse provides a documentation retrieval MCP Server, allowing AI coding assistants (any that support MCP) to directly search and access the official ErisPulse documentation while you write code.

There are two ways to connect: **local process (recommended)** or **official online endpoint**. The toolset is consistent in both cases:

| Tool | Parameters | Description |
|------|------------|-------------|
| **`search_docs`** | `query` (required), `top_k?=5`, `lang?=zh-CN` | BM25 keyword search, multiple keywords can be passed at once |
| **`read_document`** | `doc_path` (required), `lang?=zh-CN` | Reads the complete Markdown of a single document |
| **`list_documents`** | `lang?=zh-CN` | Lists all document titles, paths, and categories in the current language |
| **`list_languages`** | — | Lists all supported languages and the number of documents for each |

Supported languages: `zh-CN` / `en` / `zh-TW` / `ja` / `ru`. Search tips: use **multiple keywords** instead of full sentences, for example `command registration event listening` is better than `how to register a command`.

### Method 1: Local Process (Recommended)

After installation, start it locally:

```bash
npm i -g @erisdev/mcp-server   # Install globally → `epsdk-mcp` command appears
epsdk-mcp --server               # Start the MCP service; first run automatically pulls documentation to ~/.cache/erispulse-mcp/docs
```

Alternatively, run it directly using `npx` without global installation:

```bash
npx @erisdev/mcp-server --server
```

If you have a local documentation directory, specify it (no internet connection required):

```bash
ERISPULSE_DOCS_DIR=/path/to/erispulse/docs epsdk-mcp --server
```

In the MCP client, configure it using **stdio transmission** with standard key-value pairs (`command` and `args` pointing to the above startup method; specific configuration locations and formats are detailed in each client's own MCP integration documentation):

```json
{
  "command": "epsdk-mcp",
  "args": ["--server"]
}
```

or

```json
{
  "command": "npx",
  "args": ["@erisdev/mcp-server", "--server"]
}
```

### Method 2: Official Online Endpoint

If you don't want to run a local process, connect to the officially hosted [`mcp.erisdev.com`](https://mcp.erisdev.com/). Configure the MCP client using **HTTP transmission**:

```json
{
  "url": "https://mcp.erisdev.com/"
}
```

The service is publicly accessible by default and does not require a Token, but there is an IP rate limit (60 requests per minute per IP). The official endpoint may be disabled at any time, so for production workflows, it is recommended to use Method 1 (local process) or self-hosting.

## FAQ

**The generated code doesn't meet expectations?**  
Check whether a complete documentation is provided; add more details in the requirements (input/output examples, edge cases); let the AI generate step by step (first the skeleton, then fill in functionality); refer to the [examples/](../../examples/) directory as supplementary context.

**After integrating MCP, the AI didn't call `search_docs`?**  
Make sure the client has loaded this server (the tool will take effect after **restarting the client**); some clients require explicitly prompting in the prompt to "use ErisPulse documentation tools to verify the API."

## Next Steps

- [Getting Started with Module Development](../developer-guide/modules/getting-started.md) -- A complete tutorial for manually developing modules
- [Getting Started with Adapter Development](../developer-guide/adapters/getting-started.md) -- A complete tutorial for manually developing adapters
- [Example Code](../../examples/) -- Reference existing module and adapter implementations
- [Module Builder](https://www.erisdev.com/builder.html) -- A browser-based visual AI module generator