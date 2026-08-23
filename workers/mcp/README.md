# @erisdev/mcp-server

MCP server that lets AI coding assistants search and read ErisPulse documentation on demand.

## Installation

```bash
npm install -g @erisdev/mcp-server
```

## Usage

Start in stdio mode (for MCP clients that launch a local process):

```bash
epsdk-mcp --server
```

Or run it on the fly without installing:

```bash
npx @erisdev/mcp-server --server
```

Start in HTTP mode (connect via a client's `url` field, or open in browser / curl):

```bash
epsdk-mcp --http --port 8765
```

Point it at a local docs directory to skip network access:

```bash
ERISPULSE_DOCS_DIR=/path/to/erispulse/docs epsdk-mcp --server
```

By default the server pulls the **zh-CN** docs into `~/.cache/erispulse-mcp/docs/zh-CN` on first run. Other languages are pulled on demand when queried. All tools accept an optional `lang` (default `zh-CN`). Supported languages: `zh-CN`, `en`, `zh-TW`, `ja`, `ru`.

### Client configuration

stdio transport — `command` / `args` point at the launch command above:

```json
{ "command": "epsdk-mcp", "args": ["--server"] }
```

Or via `npx` without global install:

```json
{ "command": "npx", "args": ["@erisdev/mcp-server", "--server"] }
```

HTTP transport — use the `url`:

```json
{ "url": "http://localhost:8765/" }
```

### Tools

| Tool | Description |
|------|-------------|
| `search_docs(query, top_k?, lang?)` | BM25 keyword search over the docs; pass multiple keywords separated by spaces |
| `read_document(doc_path, lang?)` | Read a single doc's full Markdown (path like `developer-guide/getting-started.md`) |
| `list_documents(lang?)` | List all available docs with paths and titles |

Source: [github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)

## License

MIT