# AI-Assisted Development

ErisPulse provides two complementary ways for AI-assisted development, enabling AI to generate code based on the latest framework specifications:

- **Material Documentation**: A large Markdown file, loaded as context in one go, suitable for full project development.
- **MCP Server**: Allows AI to retrieve official documentation on-demand, suitable for daily code completion and API lookup.

| | Material Documentation | MCP Server |
|---|---|---|
| Format | A large Markdown file, **loaded in one go** | AI **retrieves on-demand** |
| Context Cost | High (consumes tokens) | Low (only fetches relevant snippets) |
| Timeliness | Updated with version releases | Real-time (GitHub pull + cache) |
| Suitable For | Large context window, full project development | Daily code completion, API lookup |
| Client | Any AI tool | Only clients supporting MCP |

The two approaches are not mutually exclusive: for large projects, both can be used together—material documentation for the base, and MCP as a safety net for missing information.

## Material Documentation

The material documentation is located in the `prompts/` directory and is divided into three types based on development scenarios:

| Document | Scenario | Description |
|----------|----------|-------------|
| **ErisPulse-ModuleDev.md** | Module Development | Covers the entire module development workflow (event handling, routing, lifecycle, etc.) |
| **ErisPulse-AdapterDev.md** | Adapter Development | Builds on module development and adds core adapter concepts, SendDSL, and platform adaptation guidelines |
| **ErisPulse-Full.md** | Full Stack Reference | All the above content plus a complete user guide and API reference collection |

Access method: Retrieve from the `prompts/` directory in the [docs-generated branch](https://github.com/ErisPulse/ErisPulse/tree/docs-generated) (updated synchronously with the documentation), or download via the "AI-Assisted Development" page on the official website.

### Usage

1. Choose the appropriate document based on your target (module → `ModuleDev`, adapter → `AdapterDev`, complex needs → `Full`)
2. Provide the document content as context to the AI: place it in your IDE workspace, paste directly into chat-style interfaces, or inject as a system message in API calls
3. Describe your requirements using the template below; the more specific your description, the higher the quality of the generated output

### Requirement Description Template

**Module:**

```
Please generate a complete code for a [Module Name] module based on the ErisPulse module development specification.

Function Description: [Core Functionality]
Events to listen for: [Message / Command / Notification / Request], Processing Logic: [Operation]
Required Configuration Items: [Key Name]: [Purpose] ([Required/Optional], Default Value: [Value])
Other Requirements: [Additional Constraints]
```

**Adapter:**

```
Please generate a complete code for an [Adapter Name] adapter based on the ErisPulse adapter development specification.

Platform Information: [Name], Communication Protocol: [WebSocket / WebHook / HTTP Polling], API Documentation: [URL]
Event Mapping: Platform Event [Type] → OneBot12 Mapping [Relationship]
Send Methods to Implement: [Text / Image / Voice ...]
Configuration Items: [Key Name]: [Purpose] ([Required/Optional])
```

## Complete Documentation Package

The `skills.zip` file packages all the original documentation in this language (unmerged and unmodified), with a README index at the root directory: documents grouped by directory, each entry marked with "When to read this document." An AI can load only the required documents according to the index.

### Difference from Material Documentation

| | Material Documentation | Complete Documentation Package |
|---|---|---|
| Format | Single `.md` merged document | All original documents + index README |
| Usage | Entire document inserted into context | Unzip and place into workspace; AI reads documents as needed |
| Applicable | When context window is sufficient, for whole project development | Long-term workspace residency, document retrieval on demand |

Both are generated from the same batch of documents and are updated synchronously.

### Download

Download from the "AI-assisted Development" page on the official website, or directly access the `docs/en/ai-support/skills.zip` file from the [docs-generated branch](https://github.com/ErisPulse/ErisPulse/tree/docs-generated).

## MCP Server

ErisPulse provides a documentation retrieval MCP Server, allowing AI coding assistants (any that support MCP) to directly search and access ErisPulse's official documentation while writing code.

There are two ways to connect: **local process (recommended)** or **official online endpoint**. The toolset is identical:

| Tool | Parameters | Description |
|------|------------|-------------|
| **`search_docs`** | `query` (required), `top_k?=5`, `lang?=zh-CN` | BM25 keyword search, multiple keywords can be passed at once |
| **`read_document`** | `doc_path` (required), `lang?=zh-CN` | Reads the full Markdown of a single document |
| **`list_documents`** | `lang?=zh-CN` | Lists all document titles, paths, and categories in the current language |
| **`list_languages`** | — | Lists all languages supported by the documentation and their document counts |

Supported languages: `zh-CN` / `en` / `zh-TW` / `ja` / `ru`. Search tips: use **multiple keywords** rather than full sentences, for example, `command registration event listening` is better than `how to register a command`.

### Method 1: Local Process (Recommended)

Install and start locally:

```bash
npm i -g @erisdev/mcp-server   # Global installation → `epsdk-mcp` command appears
epsdk-mcp --server               # Start the MCP service; first run automatically pulls documentation to ~/.cache/erispulse-mcp/docs
```

Alternatively, run without global installation using `npx`:

```bash
npx @erisdev/mcp-server --server
```

Specify a local documentation directory (offline mode):

```bash
ERISPULSE_DOCS_DIR=/path/to/erispulse/docs epsdk-mcp --server
```

Configure in the MCP client using **stdio transmission** with standard key-value pairs (`command` + `args` pointing to the above startup method; specific configuration locations and formats are detailed in each client's MCP integration documentation):

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

If you don't want to start a local process, connect to the official hosted [`mcp.erisdev.com`](https://mcp.erisdev.com/). Configure the MCP client using **HTTP transmission**:

```json
{
  "url": "https://mcp.erisdev.com/"
}
```

The service is publicly accessible by default, without a token, with IP rate limiting (60 requests per minute per IP). The official endpoint can be disabled at any time; **for production workflows, it is recommended to use Method 1 (local process) or self-hosting**.

## Frequently Asked Questions

**The generated code does not meet expectations?**
Check if the full documentation is provided; add more details in the requirements (input/output examples, boundary conditions); have the AI generate step-by-step (first skeleton, then features); refer to the [examples/](../../examples/) directory for example contexts.

**After MCP integration, the AI did not call `search_docs`?**
Confirm that the client has loaded the server (the tools will be effective after **restarting the client**); some clients require explicit prompts in the prompt, such as "use the ErisPulse documentation tool to verify the API."

## Next Steps

- [Module Development Guide](../developer-guide/modules/getting-started.md) -- Complete tutorial for manual module development
- [Adapter Development Guide](../developer-guide/adapters/getting-started.md) -- Complete tutorial for manual adapter development
- [Example Code](../../examples/) -- Reference existing module and adapter implementations
- [Module Builder](https://www.erisdev.com/builder.html) -- A browser-based visual AI module generator