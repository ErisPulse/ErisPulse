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

Material documentation is located in the `prompts/` directory, divided into three scenarios:

| Document | Scenario | Description |
|----------|----------|-------------|
| **ErisPulse-ModuleDev.md** | Module Development | Covers the entire module development process (event handling, routing, lifecycle, etc.) |
| **ErisPulse-AdapterDev.md** | Adapter Development | Builds on module development, plus adapter core concepts, SendDSL, and platform adaptation guidelines |
| **ErisPulse-Full.md** | Full-stack Reference | All above content + complete user guide and API reference collection |

Acquisition: from the `prompts/` directory on the [docs-generated branch](https://github.com/ErisPulse/ErisPulse/tree/docs-generated) (synchronized with documentation updates), or via the download cards on the website.

### Usage

1. Choose the document based on your target (module → `ModuleDev`, adapter → `AdapterDev`, complex needs → `Full`)
2. Provide the document content as context to the AI: place it in the IDE workspace, paste directly for chat-based tools, or inject as a system message for API calls
3. Use the template below to describe your requirements; the more specific, the higher the quality of generated code

### Requirement Description Template

**Module:**

```
Please generate a complete code for a [Module Name] module based on the ErisPulse module development specification.

Function Description: [Core Function]
Events to Listen To: [Message / Command / Notification / Request], Handling Logic: [Operation]
Configuration Items Needed: [Key Name]: [Purpose] ([Required/Optional], Default Value: [Value])
Other Requirements: [Additional Constraints]
```

**Adapter:**

```
Please generate a complete code for an [Adapter Name] adapter based on the ErisPulse adapter development specification.

Platform Information: [Name], Communication Protocol: [WebSocket / WebHook / HTTP Polling], API Documentation: [Address]
Event Mapping: Platform Event [Type] → OneBot12 Mapping [Relationship]
Required Send Methods to Implement: [Text / Image / Voice ...]
Configuration Items: [Key Name]: [Purpose] ([Required/Optional])
```

## Docs Pack

`skills.zip` packages every document of this language as-is (no merging, no rewriting), plus a README index at the root: grouped by directory, each entry annotated with its "when to read this" note. The AI loads only the documents it needs.

### Docs pack vs. material documents

| | Material documents | Docs pack |
|---|---|---|
| Form | single merged `.md` | all raw documents + README index |
| Usage | inject whole into context | unzip into the workspace, AI picks documents on demand |
| Best for | large context windows, whole-project work | long-lived workspace, on-demand retrieval |

Both are generated from the same docs and updated in sync.

### Get it

Download from the "AI-assisted development" page on the website, or take `docs/en/ai-support/skills.zip` directly from the [docs-generated branch](https://github.com/ErisPulse/ErisPulse/tree/docs-generated).
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
