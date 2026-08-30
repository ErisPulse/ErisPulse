# AI-Assisted Development

ErisPulse provides two complementary AI-assisted development approaches, enabling AI to generate code based on the latest framework specifications:

- **Material Documentation**: A large Markdown file, loaded into context at once, suitable for full project development.
- **MCP Server**: Enables AI to retrieve official documentation on-demand, suitable for daily code completion and API lookup.

| | Material Documentation | MCP Server |
|---|---|---|
| Format | A large Markdown file, **loaded once** | AI **retrieves on-demand** |
| Context Cost | High (consumes tokens) | Low (only retrieves relevant fragments) |
| Timeliness | Updated with version releases | Real-time (GitHub pull + cache) |
| Suitable For | Large context window, full project development | Daily code completion, API lookup |
| Client | Any AI tool | Only clients supporting MCP |

The two approaches are not conflicting: for large-scale projects, both can be used simultaneously — use material documentation as the foundation, and MCP to fill in gaps.



## Material Documentation

The material documentation is located in the `prompts/` directory and is divided into three types based on development scenarios:

| Document | Scenario | Description |
|------|------|------|
| **ErisPulse-ModuleDev.md** | Module Development | Covers the full module development process (event handling, routing, lifecycle, etc.) |
| **ErisPulse-AdapterDev.md** | Adapter Development | Builds upon module development, adding core adapter concepts, SendDSL, and platform adaptation guidelines |
| **ErisPulse-Full.md** | Full-stack Reference | All the above content + a complete user guide and API reference collection |

How to Obtain: Directly from the `prompts/` directory (synchronized with the documentation), or download the corresponding version from [GitHub Releases](https://github.com/ErisPulse/ErisPulse/releases).

### Usage

1. Select the document according to your target (module → `ModuleDev`, adapter → `AdapterDev`, complex needs → `Full`)
2. Provide the document content as context to the AI: place it in the workspace within the IDE, paste directly into a chat, or inject it as a system message in API calls
3. Describe your requirements using the template below; the more specific the description, the higher the generation quality

### Requirement Description Template

**Module:**

```
Please generate the complete code for a [Module Name] module based on the ErisPulse module development specification.

Function Description: [Core Function]
Events to Listen For: [Message / Command / Notification / Request], Handling Logic: [Operation]
Required Configuration Items: [Key Name]: [Purpose] ([Required/Optional], Default Value: [Value])
Additional Requirements: [Extra Constraints]
```

**Adapter:**

```
Please generate the complete code for a [Adapter Name] adapter based on the ErisPulse adapter development specification.

Platform Information: [Name], Communication Protocol: [WebSocket / WebHook / HTTP Polling], API Documentation: [Address]
Event Mapping: Platform Event [Type] → OneBot12 Mapping [Relationship]
Implemented Send Methods Required: [Text / Image / Voice ...]
Configuration Items: [Key Name]: [Purpose] ([Required/Optional])

## MCP Server

ErisPulse provides a documentation retrieval MCP Server, allowing AI coding assistants (any that support MCP) to directly search and consult ErisPulse's official documentation while you write code.

There are two ways to connect: **Local Process (Recommended)** or **Official Online Endpoint**. The toolset is consistent in both cases:

| Tool | Parameters | Description |
|------|------------|-------------|
| **`search_docs`** | `query` (required), `top_k?=5`, `lang?=zh-CN` | BM25 keyword search, multiple keywords can be passed at once |
| **`read_document`** | `doc_path` (required), `lang?=zh-CN` | Read the full Markdown of a single document |
| **`list_documents`** | `lang?=zh-CN` | List titles, paths, and categories of all documents in the current language |
| **`list_languages`** | — | List all languages supported by the documentation and the number of documents in each |

Supported languages: `zh-CN` / `en` / `zh-TW` / `ja` / `ru`. Search tips: Use **multiple keywords** instead of full sentences. For example, `command registration event listening` is better than `how to register a command`.

### Method 1: Local Process (Recommended)

After installation, start it locally:

```bash
npm i -g @erisdev/mcp-server   # Global installation → creates the epsdk-mcp command
epsdk-mcp --server               # Start the MCP service; first run automatically pulls documentation to ~/.cache/erispulse-mcp/docs
```

Alternatively, you can run it via `npx` without global installation (no need to install):

```bash
npx @erisdev/mcp-server --server
```

If you have a local documentation directory, specify it (no internet connection required):

```bash
ERISPULSE_DOCS_DIR=/path/to/erispulse/docs epsdk-mcp --server
```

In the MCP client, configure it using **stdio transmission** with standard key-value pairs (`command` + `args` pointing to the above startup method; specific configuration locations and formats are detailed in each client's own MCP integration documentation):

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

If you don't want to start a local process, connect to the official hosted endpoint [`mcp.erisdev.com`](https://mcp.erisdev.com/). Configure the MCP client using **HTTP transmission**:

```json
{
  "url": "https://mcp.erisdev.com/"
}
```

The service is publicly accessible by default and does not require a token, but there is an IP rate limit (60 requests per minute per IP). The official endpoint may be deactivated at any time, so for production workflows, it is recommended to use Method 1 (local process) or self-hosting.


## FAQ

**Generated code does not meet expectations?**  
Check if a complete documentation is provided; add more details in requirements (input/output examples, boundary conditions); ask the AI to generate step by step (first the skeleton, then fill in functionality); refer to the [examples/](../../examples/) directory for example code as supplementary context.

**After integrating MCP, the AI did not call `search_docs`?**  
Ensure the client has loaded the server (the tool will be effective after **restarting the client**); some clients require explicitly prompting in the prompt to "use the ErisPulse documentation tool to verify the API."


## Next Steps

- [Getting Started with Module Development](../developer-guide/modules/getting-started.md) -- Complete tutorial for manually developing modules
- [Getting Started with Adapter Development](../developer-guide/adapters/getting-started.md) -- Complete tutorial for manually developing adapters
- [Example Code](../../examples/) -- Reference existing module and adapter implementations
- [Module Builder](https://www.erisdev.com/builder.html) -- Visual AI module generator in the browser

Please directly return the translated complete Markdown content, without including any other text.
