# AI-Assisted Development

ErisPulse provides two complementary AI-assisted development methods, enabling AI to generate code based on the latest framework specifications:

- **Material Documentation**: A large Markdown file, loaded into context at once, suitable for full-project development
- **MCP Server**: Allows AI to retrieve official documentation on demand, suitable for daily code completion and API lookup

| | Material Documentation | MCP Server |
|---|---|---|
| Format | A large Markdown file, **loaded at once** | AI **retrieves on demand** |
| Context Cost | High (consumes tokens) | Low (only retrieves relevant snippets) |
| Timeliness | Updated with version releases | Real-time (GitHub pull + cache) |
| Suitable For | Large context window, full-project development | Daily code completion, API lookup |
| Client | Any AI tool | Only clients supporting MCP |

The two methods are not mutually exclusive: when developing large projects, both can be used together—use material documentation as a foundation, and MCP as a backup for checking gaps.

## Material Documentation

The material documentation is located in the `prompts/` directory and is divided into three types based on development scenarios:

| Document | Scenario | Description |
|----------|----------|-------------|
| **ErisPulse-ModuleDev.md** | Module Development | Covers the entire module development workflow (event handling, routing, lifecycle, etc.) |
| **ErisPulse-AdapterDev.md** | Adapter Development | Builds upon module development, adding core adapter concepts, SendDSL, and platform adaptation guidelines |
| **ErisPulse-Full.md** | Full-stack Reference | All above content + complete user guide and API reference collection |

Acquisition method: Directly obtain from the `prompts/` directory (synchronized with the documentation), or download the corresponding version from [GitHub Releases](https://github.com/ErisPulse/ErisPulse/releases).

### Usage

1. Select the appropriate document based on your target scenario (module → `ModuleDev`, adapter → `AdapterDev`, complex needs → `Full`)
2. Provide the document content as context to the AI: place it in your IDE workspace, paste directly into chat-based interfaces, or inject as a system message in API calls
3. Describe your requirements using the template below; more specific descriptions yield higher quality results

### Requirement Description Template

**Module:**

```
Please generate complete code for a [module name] module based on the ErisPulse module development specifications.

Function description: [Core functionality]
Events to listen for: [Message / Command / Notification / Request], processing logic: [Operation]
Required configuration items: [Key name]: [Purpose] ([Required/Optional], default value: [Value])
Other requirements: [Additional constraints]
```

**Adapter:**

```
Please generate complete code for a [adapter name] adapter based on the ErisPulse adapter development specifications.

Platform information: [Name], communication protocol: [WebSocket / WebHook / HTTP polling], API documentation: [URL]
Event mapping: Platform event [type] → OneBot12 mapping [relationship]
Required send methods to implement: [Text / Image / Voice ...]
Configuration items: [Key name]: [Purpose] ([Required/Optional])
```

## MCP Server

ErisPulse provides a documentation retrieval MCP Server, allowing AI coding assistants (any that support MCP) to directly search and consult the official ErisPulse documentation while you code.

There are two ways to connect: **local process (recommended)** or **official online endpoint**. The toolset is identical in both cases:

| Tool | Parameters | Description |
|------|------------|-------------|
| **`search_docs`** | `query` (required), `top_k?=5`, `lang?=zh-CN` | BM25 keyword search, multiple keywords can be passed at once |
| **`read_document`** | `doc_path` (required), `lang?=zh-CN` | Read the full Markdown of a single document |
| **`list_documents`** | `lang?=zh-CN` | List all document titles, paths, and categories in the current language |
| **`list_languages`** | — | List all languages supported by the documentation and the number of documents for each |

Supported languages: `zh-CN` / `en` / `zh-TW` / `ja` / `ru`. Search tips: use **multiple keywords** instead of full sentences, for example `command registration event listening` is better than `how to register a command`.

### Method 1: Local Process (Recommended)

After installation, start it locally:

```bash
npm i -g @erisdev/mcp-server   # Install globally → creates the epsdk-mcp command
epsdk-mcp --server               # Start the MCP service; automatically downloads documentation to ~/.cache/erispulse-mcp/docs on first run
```

Alternatively, run it without global installation using `npx` (no installation required):

```bash
npx @erisdev/mcp-server --server
```

If you have a local documentation directory, specify it (no internet connection required):

```bash
ERISPULSE_DOCS_DIR=/path/to/erispulse/docs epsdk-mcp --server
```

In the MCP client, configure it using **stdio transport** with standard key-value pairs (`command` + `args` pointing to the above startup method; the specific location and format of the configuration depends on the client's own MCP integration documentation):

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

If you don't want to run a local process, connect to the official hosted [`mcp.erisdev.com`](https://mcp.erisdev.com/). In the MCP client, configure it using **HTTP transport**:

```json
{
  "url": "https://mcp.erisdev.com/"
}
```

The service is publicly accessible by default and does not require a token, but has IP rate limiting (60 requests per minute per IP). The official endpoint may be discontinued at any time, so **for production workflows, it is recommended to use Method 1 (local process) or self-hosting**.

## FAQ

**The generated code does not meet expectations?**  
Check whether a complete documentation is provided; add more details in the requirements (input/output examples, boundary conditions); let the AI generate step by step (first the skeleton, then add functionality); refer to the examples in the [examples/](../../examples/) directory as supplementary context.

**After connecting to MCP, the AI did not call `search_docs`?**  
Ensure the client has loaded the server (**restart the client to see that the tool is now active**); some clients require explicitly prompting in the prompt to "use the ErisPulse documentation tool to verify the API."

## Next Steps

- [Getting Started with Module Development](../developer-guide/modules/getting-started.md) -- A complete tutorial for manually developing modules
- [Getting Started with Adapter Development](../developer-guide/adapters/getting-started.md) -- A complete tutorial for manually developing adapters
- [Example Code](../../examples/) -- Reference existing module and adapter implementations
- [Module Builder](https://www.erisdev.com/builder.html) -- A browser-based visual AI module generator