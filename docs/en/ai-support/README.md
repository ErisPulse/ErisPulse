# AI-Assisted Development

ErisPulse provides two complementary AI-assisted development approaches, enabling AI to generate code based on the latest framework specifications:

- **Material Documents**: A single large Markdown file loaded into the context all at once, suitable for whole-project development
- **MCP Server**: Lets the AI retrieve the official documentation on demand, suitable for daily code completion and API lookups

| | Material Documents | MCP Server |
|---|---|---|
| Form | A single large Markdown file, **loaded all at once** | AI **retrieves on demand** |
| Context cost | High (consumes tokens) | Low (only fetches relevant snippets) |
| Freshness | Updated with version releases | Real-time (GitHub fetch + caching) |
| Best for | Large context windows, whole-project development | Daily code completion, API lookups |
| Clients | Any AI tool | MCP-capable clients only |

The two are not mutually exclusive: you can use both when developing large projects—material documents as the foundation, with the MCP server as a fallback to fill the gaps.

## Material Documents

Material documents are located in the `prompts/` directory, divided into three types by development scenario:

| Document | Scenario | Description |
|------|------|------|
| **ErisPulse-ModuleDev.md** | Module development | Covers the full module development workflow (event handling, routing, lifecycle, etc.) |
| **ErisPulse-AdapterDev.md** | Adapter development | Builds on module development, plus core adapter concepts, SendDSL, and platform adaptation guides |
| **ErisPulse-Full.md** | Full-stack reference | All of the above + a combined collection of the complete user guide and API reference |

How to obtain: get them directly from the `prompts/` directory (kept in sync with the documentation), or download the corresponding version from [GitHub Releases](https://github.com/ErisPulse/ErisPulse/releases).

### Usage

1. Choose a document based on your goal (modules → `ModuleDev`, adapters → `AdapterDev`, complex requirements → `Full`)
2. Provide the document content as context to the AI: place it in the workspace for IDEs, paste it directly for chat-based tools, or inject it as a system message for API calls
3. Describe your requirements using the templates below—the more specific, the higher the generation quality

### Requirement Description Templates

**Module:**

```
Based on the ErisPulse module development specifications, generate the complete code for a [module name] module.

Feature description: [core features]
Events to listen for: [messages / commands / notifications / requests], handling logic: [actions]
Required configuration items: [key name]: [purpose] ([required/optional], default: [value])
Other requirements: [additional constraints]
```

**Adapter:**

```
Based on the ErisPulse adapter development specifications, generate the complete code for an [adapter name] adapter.

Platform information: [name], communication protocol: [WebSocket / WebHook / HTTP polling], API documentation: [URL]
Event conversion: platform event [type] → OneBot12 mapping [relations]
Send methods to implement: [Text / Image / Voice ...]
Configuration items: [key name]: [purpose] ([required/optional])
```

## Agent Skills

Agent Skills are skill packages for AI coding agents (ZCode / Claude Code, etc.): each skill is a directory (`SKILL.md` + frontmatter), and agents automatically discover and load them on demand based on `description`—reading only the relevant sections when a task requires it, without loading the full text.

Skills are located in the `skills/` directory (generated in sync with the material documents), and each `SKILL.md` begins with a **line-numbered outline**: it marks the start and end line numbers of each section so the AI can read only the parts it needs.

### Deployment

1. Get the skills from the `skills/<language>/` directory (or download the corresponding version's artifact)
2. Copy the skill directories into the agent's skills directory (following your tool's convention, e.g. `.zcode/skills/`, `.claude/skills/`)
3. Afterwards, the agent will automatically trigger loading when it encounters relevant tasks—no manual referencing needed

### Outline Example

```markdown
## Content Outline
The AI reads on demand: just read the sections you need; no need to load the full text.

- Lazy loading and hibernation: lines 18-29
- Overview: lines 30-38
- Event-driven lazy activation (activate_on): lines 55-132
```

> Skills are built automatically by CI (`python -m scripts.tools gen skills`); do not modify them by hand.

## MCP Server

ErisPulse provides a documentation retrieval MCP Server, allowing AI coding assistants (any that support MCP) to search and consult the official ErisPulse documentation directly while you write code.

There are two ways to connect: **local process (recommended)** or **official online endpoint**. The tool set is identical:

| Tool | Parameters | Description |
|------|------|------|
| **`search_docs`** | `query` (required), `top_k?=5`, `lang?=zh-CN` | BM25 keyword search; multiple keywords can be passed in one call |
| **`read_document`** | `doc_path` (required), `lang?=zh-CN` | Read the full Markdown of a single document |
| **`list_documents`** | `lang?=zh-CN` | List the titles, paths, and categories of all documents in the current language |
| **`list_languages`** | — | List all languages supported by the documentation and their document counts |

Supported languages: `zh-CN` / `en` / `zh-TW` / `ja` / `ru`. Search tip: use **multiple keywords** instead of full sentences—for example, `command registration event listening` works better than `how do I register a command`.

### Method 1: Local Process (Recommended)

Once installed, start it locally directly:

```bash
npm i -g @erisdev/mcp-server   # Global install → the epsdk-mcp command becomes available
epsdk-mcp --server               # Starts the MCP service; the first run automatically pulls the docs to ~/.cache/erispulse-mcp/docs
```

You can also run it directly via `npx` without a global install (no installation required):

```bash
npx @erisdev/mcp-server --server
```

If you have a local documentation directory, specify it (offline):

```bash
ERISPULSE_DOCS_DIR=/path/to/erispulse/docs epsdk-mcp --server
```

Configure it in your MCP client using **stdio transport**, in the standard key-value format (`command` + `args` pointing to one of the startup methods above; see each client's own MCP integration documentation for the specific configuration location and format):

```json
{
  "command": "epsdk-mcp",
  "args": ["--server"]
}
```

Or:

```json
{
  "command": "npx",
  "args": ["@erisdev/mcp-server", "--server"]
}
```

### Method 2: Official Online Endpoint

If you don't want to run a local process, connect to the officially hosted [`mcp.erisdev.com`](https://mcp.erisdev.com/). Configure your MCP client with **HTTP transport**:

```json
{
  "url": "https://mcp.erisdev.com/"
}
```

The service is public by default and requires no token, with IP rate limiting (60 requests per IP per minute). The official endpoint may be discontinued at any time; **for production workflows, Method 1 (local process) or self-hosting is recommended**.

## FAQ

**Generated code doesn't meet expectations?**
Check whether the complete documentation was provided; add more details to your requirements (input/output examples, edge cases); have the AI generate step by step (skeleton first, then fill in features); refer to the examples in the [examples/](../../examples/) directory as supplementary context.

**The AI doesn't call `search_docs` after MCP integration?**
Confirm that the client has loaded the server (**the tools will take effect after restarting the client**); some clients require explicitly prompting in the prompt to "use ErisPulse documentation tools to verify APIs".

## Next Steps

- [Getting Started with Module Development](../developer-guide/modules/getting-started.md) -- Complete tutorial for manually developing modules
- [Getting Started with Adapter Development](../developer-guide/adapters/getting-started.md) -- Complete tutorial for manually developing adapters
- [Example Code](../../examples/) -- Reference existing module and adapter implementations
- [Module Builder](https://www.erisdev.com/builder.html) -- A visual AI module generator in the browser