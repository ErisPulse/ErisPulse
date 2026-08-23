#!/usr/bin/env node
/**
 * ErisPulse MCP Server — ErisPulse docs retrieval (stdio / HTTP)
 *
 * Tools:
 *   search_docs(query, top_k?, lang?)  - BM25 search (lang optional, default zh-CN)
 *   read_document(doc_path, lang?)     - read one doc (lang optional, default zh-CN)
 *   list_documents(lang?)              - list docs (lang optional, default zh-CN)
 *
 * Supported languages: zh-CN, en, zh-TW, ja, ru.
 * The zh-CN docs are pulled on first run; other languages are pulled on demand
 * when queried (cached to ~/.cache/erispulse-mcp/docs/<lang>). ERISPULSE_DOCS_DIR
 * points at a local docs/ directory to avoid network access.
 *
 * Usage:
 *   epsdk-mcp --server                  # stdio (default)
 *   epsdk-mcp --http --port 8765        # HTTP
 *   ERISPULSE_DOCS_DIR=/path/to/docs epsdk-mcp --server
 *
 * Protocol: MCP 2025-03-26 (Streamable HTTP) / JSON-RPC 2.0.
 */

const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");

const SUPPORTED_LANGS = ["zh-CN", "en", "zh-TW", "ja", "ru"];
const DEFAULT_LANG = "zh-CN";
const SERVER_NAME = "erispulse-docs";
const SERVER_VERSION = "1.0.4";
const PROTOCOL_VERSION = "2025-03-26";

const DOCS_RAW_BASE =
  "https://raw.githubusercontent.com/ErisPulse/ErisPulse/Develop/v2/docs/";
const DOCS_PROXY_BASE =
  "https://cdn.gh-proxy.org/https://raw.githubusercontent.com/ErisPulse/ErisPulse/Develop/v2/docs/";

function resolveLocalDocsRoot() {
  const env = process.env.ERISPULSE_DOCS_DIR;
  if (env) return env;
  for (const cand of [path.join(process.cwd(), "docs"), path.join(__dirname, "..", "..", "..", "docs")]) {
    if (fs.existsSync(cand)) return cand;
  }
  return null;
}

async function fetchTextWithFallback(url, proxyUrl) {
  let lastErr;
  for (const u of [url, proxyUrl].filter(Boolean)) {
    try {
      const res = await fetch(u);
      if (res.ok) return await res.text();
      lastErr = new Error(`HTTP ${res.status} for ${u}`);
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr || new Error("fetch failed");
}

async function pullLangToCache(lang, cacheLangDir) {
  const mappingUrl = `${DOCS_RAW_BASE}_meta/${lang}/docs-mapping.json`;
  const proxy = `${DOCS_PROXY_BASE}_meta/${lang}/docs-mapping.json`;
  let mapping;
  try {
    mapping = JSON.parse(await fetchTextWithFallback(mappingUrl, proxy));
  } catch (e) {
    return 0;
  }
  const docs = [];
  for (const category of Object.values(mapping.categories || {})) {
    for (const d of category.documents || []) docs.push(d);
    for (const sg of Object.values(category.subgroups || {})) {
      for (const d of sg.documents || []) docs.push(d);
    }
  }
  let count = 0;
  for (const d of docs) {
    const rel = String(d.path || "");
    if (!rel.endsWith(".md")) continue;
    try {
      const url = `${DOCS_RAW_BASE}${lang}/${rel}`;
      const proxy2 = `${DOCS_PROXY_BASE}${lang}/${rel}`;
      const text = await fetchTextWithFallback(url, proxy2);
      const dest = path.join(cacheLangDir, rel);
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      fs.writeFileSync(dest, text, "utf-8");
      count++;
    } catch (e) {}
  }
  return count;
}

// 返回 docs 基础目录：本地（ERISPULSE_DOCS_DIR 或仓库 docs/）优先；否则缓存根 ~/.cache/erispulse-mcp/docs
function resolveDocsBase() {
  const local = resolveLocalDocsRoot();
  if (local) return local;
  return path.join(os.homedir(), ".cache", "erispulse-mcp", "docs");
}

// 确保某语言目录就绪：本地有则用它；缓存没有则按需拉取。返回该语言目录
async function ensureLang(base, lang) {
  const dir = path.join(base, lang);
  if (fs.existsSync(path.join(dir))) return dir;
  // 本地 base 下没有该语言 → 若 base 是缓存则拉取；本地（如 ERISPULSE_DOCS_DIR）则视为无
  if (base === path.join(os.homedir(), ".cache", "erispulse-mcp", "docs")) {
    process.stderr.write(`ErisPulse MCP: pulling ${lang} docs...\n`);
    fs.mkdirSync(dir, { recursive: true });
    try {
      const n = await pullLangToCache(lang, dir);
      process.stderr.write(`  ${lang}: ${n} docs\n`);
    } catch (e) {
      process.stderr.write(`  ${lang}: pull failed (${e.message})\n`);
    }
  }
  return dir;
}

function listMarkdown(langDir) {
  if (!fs.existsSync(langDir)) return [];
  const out = [];
  (function walk(dir, rel) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === "ai-support" || entry.name === "api-reference") continue;
        walk(full, path.join(rel, entry.name));
      } else if (entry.name.endsWith(".md")) {
        out.push({ rel: path.join(rel, entry.name), full });
      }
    }
  })(langDir, "");
  return out;
}

const CJK_RE = /[\u4e00-\u9fff\u3400-\u4dbf]/g;
const WORD_RE = /[a-z0-9]+/g;

function tokenize(text) {
  if (!text) return [];
  const lower = String(text).toLowerCase();
  const tokens = [];
  let m;
  const wordRe = new RegExp(WORD_RE.source, "g");
  while ((m = wordRe.exec(lower)) !== null) tokens.push(m[0]);
  const cjkRe = new RegExp(CJK_RE.source, "g");
  let match;
  while ((match = cjkRe.exec(lower)) !== null) {
    const start = match.index;
    cjkRe.lastIndex = start + 1;
    let end = start;
    while (end < lower.length && CJK_RE.test(lower[end])) end++;
    const seg = lower.slice(start, end);
    for (const ch of seg) tokens.push(ch);
    for (let i = 0; i < seg.length - 1; i++) tokens.push(seg.slice(i, i + 2));
    cjkRe.lastIndex = end;
  }
  return tokens;
}

class BM25Index {
  constructor(docs, k1 = 1.5, b = 0.75) {
    this.k1 = k1;
    this.b = b;
    this.docs = docs;
    this.docLen = docs.map((d) => d.tokens.length);
    this.N = docs.length;
    this.avgdl = this.N === 0 ? 0 : this.docLen.reduce((s, n) => s + n, 0) / this.N;
    const df = {};
    this.tf = docs.map((d) => {
      const freq = {};
      for (const t of d.tokens) freq[t] = (freq[t] || 0) + 1;
      for (const t of Object.keys(freq)) df[t] = (df[t] || 0) + 1;
      return freq;
    });
    this.idf = {};
    for (const t of Object.keys(df)) this.idf[t] = Math.log(1 + (this.N - df[t] + 0.5) / (df[t] + 0.5));
  }

  search(query, topK = 5) {
    const qTokens = tokenize(query);
    if (qTokens.length === 0 || this.N === 0) return [];
    const scores = new Array(this.N).fill(0);
    const seen = new Set(qTokens);
    for (const term of seen) {
      const idf = this.idf[term];
      if (idf === undefined) continue;
      for (let i = 0; i < this.N; i++) {
        const f = this.tf[i][term];
        if (!f) continue;
        const dl = this.docLen[i] || 1;
        const denom = f + this.k1 * (1 - this.b + this.b * (dl / (this.avgdl || 1)));
        scores[i] += (idf * f * (this.k1 + 1)) / denom;
      }
    }
    const ranked = [];
    for (let i = 0; i < this.N; i++) if (scores[i] > 0) ranked.push({ index: i, score: scores[i] });
    ranked.sort((a, b) => b.score - a.score);
    return ranked.slice(0, topK);
  }
}

function chunkDocument(docRel, title, content) {
  const chunks = [];
  const lines = String(content || "").split("\n");
  const MAX = 1000;
  let currentHeading = title || docRel;
  let buffer = [];
  const flush = () => {
    if (buffer.length === 0) return;
    let text = buffer.join("\n");
    while (text.length > MAX) {
      const slice = text.slice(0, MAX);
      chunks.push({ docId: docRel, title: currentHeading, content: slice, tokens: tokenize(slice) });
      text = text.slice(MAX);
    }
    if (text.trim().length > 0) {
      chunks.push({ docId: docRel, title: currentHeading, content: text, tokens: tokenize(text) });
    }
    buffer = [];
  };
  const headingRe = /^#{1,4}\s+/;
  for (const line of lines) {
    if (headingRe.test(line)) {
      flush();
      currentHeading = `${title || docRel} » ${line.replace(/^#+\s+/, "").trim()}`;
    }
    buffer.push(line);
  }
  flush();
  return chunks;
}

// 语言 -> 知识库缓存（按需构建）
const memCache = new Map();

async function buildKnowledgeBase(langDir, lang) {
  if (memCache.has(lang)) return memCache.get(lang);
  const docs = listMarkdown(langDir).map((f) => ({
    rel: f.rel.replace(/\\/g, "/"),
    title: path.basename(f.rel, ".md"),
    content: fs.readFileSync(f.full, "utf-8"),
  }));
  const chunks = [];
  for (const d of docs) chunks.push(...chunkDocument(d.rel, d.title, d.content));
  const bm25 = new BM25Index(chunks);
  const entry = { docs, chunks, bm25 };
  memCache.set(lang, entry);
  return entry;
}

function textContent(text) {
  return { content: [{ type: "text", text }] };
}

function pickLang(lang) {
  return SUPPORTED_LANGS.includes(lang) ? lang : DEFAULT_LANG;
}

async function toolSearchDocs(base, args) {
  const query = String(args?.query || "").trim();
  if (!query) return textContent("Error: query is required.");
  const topK = clampInt(args?.top_k, 5, 1, 20);
  const lang = pickLang(args?.lang);
  const langDir = await ensureLang(base, lang);
  const kb = await buildKnowledgeBase(langDir, lang);
  const results = kb.bm25.search(query, topK).map((r) => {
    const c = kb.chunks[r.index];
    const snippet = c.content.length > 500 ? c.content.slice(0, 500) + "..." : c.content;
    return { doc_path: c.docId, title: c.title, snippet, score: Number(r.score.toFixed(4)) };
  });
  if (results.length === 0) return textContent(`No docs found for "${query}" (lang: ${lang}).`);
  return textContent(JSON.stringify(results, null, 2));
}

async function toolReadDocument(base, args) {
  const docPath = String(args?.doc_path || "").trim();
  if (!docPath) return textContent("Error: doc_path is required.");
  const lang = pickLang(args?.lang);
  const langDir = await ensureLang(base, lang);
  const kb = await buildKnowledgeBase(langDir, lang);
  const doc = kb.docs.find((d) => d.rel === docPath);
  if (!doc) return textContent(`Doc not found: ${docPath} (lang: ${lang}). Use list_documents.`);
  return textContent(doc.content);
}

async function toolListDocuments(base, args) {
  const lang = pickLang(args?.lang);
  const langDir = await ensureLang(base, lang);
  const kb = await buildKnowledgeBase(langDir, lang);
  const list = kb.docs.map((d) => ({ path: d.rel, title: d.title }));
  return textContent(
    `ErisPulse docs (lang: ${lang}, ${list.length} docs). Supported languages: ${SUPPORTED_LANGS.join(", ")}.\n\n` +
      JSON.stringify(list, null, 2)
  );
}

function clampInt(v, def, min, max) {
  const n = Math.floor(Number(v));
  if (!Number.isFinite(n)) return def;
  return Math.max(min, Math.min(max, n));
}

const TOOL_DEFINITIONS = [
  {
    name: "search_docs",
    description:
      "BM25 keyword search over ErisPulse official docs. Pass multiple keywords separated by spaces. Returns doc_path / title / snippet / score. lang is optional (default zh-CN).",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "search keywords" },
        top_k: { type: "integer", description: "max results, default 5", default: 5, minimum: 1, maximum: 20 },
        lang: { type: "string", description: "docs language, default zh-CN", default: DEFAULT_LANG, enum: SUPPORTED_LANGS },
      },
      required: ["query"],
    },
  },
  {
    name: "read_document",
    description:
      "Read one ErisPulse doc's full Markdown. doc_path looks like 'developer-guide/getting-started.md'. lang is optional (default zh-CN).",
    inputSchema: {
      type: "object",
      properties: {
        doc_path: { type: "string", description: "doc relative path" },
        lang: { type: "string", description: "docs language, default zh-CN", default: DEFAULT_LANG, enum: SUPPORTED_LANGS },
      },
      required: ["doc_path"],
    },
  },
  {
    name: "list_documents",
    description: "List all docs' paths and titles. Also reports supported languages. lang is optional (default zh-CN).",
    inputSchema: {
      type: "object",
      properties: {
        lang: { type: "string", description: "docs language, default zh-CN", default: DEFAULT_LANG, enum: SUPPORTED_LANGS },
      },
      required: [],
    },
  },
];

const TOOL_HANDLERS = {
  search_docs: toolSearchDocs,
  read_document: toolReadDocument,
  list_documents: toolListDocuments,
};

function handleRequest(base, body) {
  const { jsonrpc, id, method, params } = body;
  if (jsonrpc !== "2.0") return error(id, -32600, "Invalid Request");

  switch (method) {
    case "initialize":
      return respond(id, {
        protocolVersion: PROTOCOL_VERSION,
        serverInfo: { name: SERVER_NAME, version: SERVER_VERSION },
        capabilities: { tools: { listChanged: false } },
        instructions:
          `Retrieve ErisPulse docs with search_docs/read_document/list_documents. ` +
          `Supported languages: ${SUPPORTED_LANGS.join(", ")} (default zh-CN).`,
      });
    case "ping":
      return respond(id, {});
    case "tools/list":
      return respond(id, { tools: TOOL_DEFINITIONS });
    case "tools/call": {
      const name = params?.name;
      const args = params?.arguments || {};
      const handler = TOOL_HANDLERS[name];
      if (!handler) return error(id, -32602, `Unknown tool: ${name}`);
      try {
        const result = handler(base, args);
        return Promise.resolve(result).then((r) => respond(id, r)).catch((e) => error(id, -32603, `Tool execution failed: ${e.message}`));
      } catch (e) {
        return error(id, -32603, `Tool execution failed: ${e.message}`);
      }
    }
    default:
      return error(id, -32601, `Method not found: ${method}`);
  }
}

function respond(id, result) {
  return JSON.stringify({ jsonrpc: "2.0", id, result });
}

function error(id, code, message) {
  return JSON.stringify({ jsonrpc: "2.0", id, error: { code, message } });
}

async function main(mode, port) {
  const base = resolveDocsBase();

  // 首启预拉默认语言（仅当 base 是缓存且 zh-CN 未就绪）
  if (base !== resolveLocalDocsRoot()) {
    await ensureLang(base, DEFAULT_LANG);
  }

  if (mode === "http") {
    return serveHttp(base, port || 8765);
  }

  process.stderr.write(
    `\nErisPulse MCP server is running (stdio).\n` +
      `  docs: ${base}\n` +
      `  languages: ${SUPPORTED_LANGS.join(", ")}\n` +
      `  waiting for MCP client...\n\n`
  );

  let buf = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => {
    buf += chunk;
    let idx;
    while ((idx = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, idx).trim();
      buf = buf.slice(idx + 1);
      if (!line) continue;
      let body;
      try {
        body = JSON.parse(line);
      } catch (e) {
        process.stdout.write(error(null, -32700, "Parse error") + "\n");
        continue;
      }
      if (Array.isArray(body)) {
        process.stdout.write(error(null, -32600, "Batch requests not supported") + "\n");
        continue;
      }
      const out = handleRequest(base, body);
      if (out && typeof out.then === "function") {
        out.then((s) => process.stdout.write(s + "\n"));
      } else {
        process.stdout.write(out + "\n");
      }
    }
  });
  process.stdin.on("end", () => {});
}

function serveHttp(base, port) {
  const server = http.createServer((req, res) => {
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.setHeader(
      "Access-Control-Allow-Headers",
      "Content-Type, Accept, Authorization, Mcp-Session-Id"
    );
    if (req.method === "OPTIONS") {
      res.writeHead(204);
      res.end();
      return;
    }

    if (req.method === "GET") {
      const url = new URL(req.url, `http://localhost:${port}`);
      const qLang = url.searchParams.get("lang");
      const acceptLang = (req.headers["accept-language"] || "").split(",")[0] || "";
      const lang = qLang === "en" || qLang === "zh" ? (qLang === "en" ? "en" : "zh-CN")
        : /zh/i.test(acceptLang) || !acceptLang
          ? "zh-CN"
          : "en";
      const t =
        lang === "zh-CN"
          ? {
              title: "ErisPulse MCP Server",
              lead: "本端点为 AI 编码助手提供 ErisPulse 官方文档检索能力（MCP Streamable HTTP）。",
              tools: "支持的 MCP 工具",
              search: "BM25 关键词检索",
              read: "读取单篇文档",
              list: "列出所有文档",
              client: "在客户端中接入",
              endpoint: "在客户端配置中填入上面的 url：",
              docs: "开源仓库",
              source: "github.com/ErisPulse/ErisPulse",
            }
          : {
              title: "ErisPulse MCP Server",
              lead: "This endpoint gives AI coding assistants MCP Streamable HTTP access to ErisPulse docs.",
              tools: "MCP tools",
              search: "BM25 keyword search",
              read: "read a single doc",
              list: "list all docs",
              client: "Client configuration",
              endpoint: "Set the url above in your client:",
              docs: "Source",
              source: "github.com/ErisPulse/ErisPulse",
            };
      const html = `<!DOCTYPE html>
<html lang="${lang}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>${t.title}</title>
<style>
  :root {
    --bg: #f4f6fb; --bg-deep: #eceff6; --card: #ffffff;
    --ink: #1f2937; --ink-soft: #64748b; --ink-faint: #9aa6b8; --line: #e8edf5;
    --accent: #64748b; --accent-glow: rgba(100,116,139,0.10); --danger: #ef4444;
    --radius: 14px; --shadow: 0 1px 2px rgba(16,24,40,0.03), 0 4px 20px rgba(16,24,40,0.04);
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: var(--font-sans); background: var(--bg); color: var(--ink); min-height: 100vh; line-height: 1.6; -webkit-font-smoothing: antialiased; }
  .container { max-width: 860px; margin: 0 auto; padding: 32px 24px 64px; }
  .crumbs { color: var(--ink-faint); font-size: 13px; margin-bottom: 6px; }
  h1 { font-size: 30px; font-weight: 800; letter-spacing: -0.02em; }
  .sub { color: var(--ink-soft); font-size: 15px; margin-top: 6px; }
  .badges { display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap; }
  .chip { padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: 600; background: var(--bg-deep); color: var(--ink-soft); border: 1px solid var(--line); }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 28px; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow); padding: 22px; transition: box-shadow 0.2s, transform 0.2s; }
  .card:hover { box-shadow: 0 6px 28px rgba(16,24,40,0.06); transform: translateY(-2px); }
  .card.wide { grid-column: 1 / -1; }
  .card-head { display: flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 700; margin-bottom: 18px; }
  .card-head svg { width: 19px; height: 19px; }
  .cmd-wrapper { position: relative; background: var(--bg-deep); border-radius: 12px; overflow: hidden; }
  .cmd-label { padding: 8px 16px; font-size: 12px; color: var(--ink-soft); border-bottom: 1px solid var(--line); background: rgba(0,0,0,0.02); }
  .cmd-content { padding: 14px 16px; font-family: var(--font-mono); font-size: 13px; color: var(--ink); display: flex; align-items: center; justify-content: space-between; gap: 12px; overflow-x: auto; }
  .cmd-text { flex: 1; word-break: break-all; }
  .btn { background: var(--accent); color: #fff; border: none; padding: 7px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; white-space: nowrap; }
  .btn:hover { opacity: 0.9; }
  .steps { list-style: none; counter-reset: s; }
  .steps li { position: relative; padding-left: 32px; margin-bottom: 12px; color: var(--ink-soft); font-size: 14px; }
  .steps li:last-child { margin-bottom: 0; }
  .steps li::before { counter-increment: s; content: counter(s); position: absolute; left: 0; top: 0; width: 22px; height: 22px; background: var(--bg-deep); border: 1px solid var(--line); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: var(--accent); }
  .steps code { font-family: var(--font-mono); color: var(--ink); background: var(--bg-deep); padding: 1px 5px; border-radius: 4px; }
  .links-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
  .link-item { display: flex; align-items: center; justify-content: center; padding: 12px; background: var(--bg-deep); border: 1px solid var(--line); border-radius: 10px; color: var(--ink-soft); text-decoration: none; font-size: 14px; font-weight: 600; transition: all 0.2s; }
  .link-item:hover { background: var(--accent-glow); border-color: var(--accent); color: var(--accent); transform: translateY(-2px); }
  .foot { margin-top: 36px; text-align: center; color: var(--ink-faint); font-size: 13px; }
  .lang-switch { display: inline-flex; background: var(--bg-deep); border: 1px solid var(--line); border-radius: 999px; overflow: hidden; margin-bottom: 12px; }
  .lang-btn { padding: 6px 16px; font-size: 12px; background: transparent; border: none; color: var(--ink-soft); cursor: pointer; }
  .lang-btn.active { background: var(--accent); color: #fff; }
  a { color: var(--accent); text-decoration: none; }
  @media (max-width: 640px) { .container { padding: 20px 14px 40px; } .grid { grid-template-columns: 1fr; } .cmd-content { flex-direction: column; align-items: stretch; gap: 10px; } .btn { width: 100%; } }
</style>
</head>
<body>
<div class="container">
  <div class="crumbs">ErisPulse / MCP</div>
  <h1>${t.title}</h1>
  <div class="sub">${t.lead}</div>
  <div class="badges">
    <span class="chip">MCP</span><span class="chip">Streamable HTTP</span><span class="chip">localhost:${port}</span>
  </div>

  <div class="grid">
    <div class="card wide">
      <div class="card-head"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>${t.client}</div>
      <div class="cmd-wrapper">
        <div class="cmd-label">mcpServers</div>
        <div class="cmd-content">
          <span class="cmd-text">{ "mcpServers": { "erispulse": { "url": "http://localhost:${port}/" } } }</span>
          <button class="btn" onclick="copyCmd(this)">复制</button>
        </div>
      </div>
      <p class="hint" style="margin-top:12px;font-size:13px;color:var(--ink-soft)">${t.endpoint}</p>
    </div>

    <div class="card">
      <div class="card-head"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h10"/></svg>${t.tools}</div>
      <ol class="steps">
        <li><code>search_docs(query, top_k?, lang?)</code> — ${t.search}</li>
        <li><code>read_document(doc_path, lang?)</code> — ${t.read}</li>
        <li><code>list_documents(lang?)</code> — ${t.list}</li>
      </ol>
    </div>

    <div class="card">
      <div class="card-head"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>${t.docs}</div>
      <div class="links-grid">
        <a href="https://github.com/ErisPulse/ErisPulse" target="_blank" class="link-item">GitHub</a>
        <a href="https://www.erisdev.com" target="_blank" class="link-item">官网</a>
        <a href="https://github.com/ErisPulse/ErisPulse/tree/Develop/v2/workers/mcp" target="_blank" class="link-item">源码</a>
      </div>
    </div>
  </div>

  <div class="foot">
    <div class="lang-switch">
      <button class="lang-btn ${lang === "en" ? "active" : ""}" onclick="switchLang('en')">English</button>
      <button class="lang-btn ${lang !== "en" ? "active" : ""}" onclick="switchLang('zh')">中文</button>
    </div>
      </div>
</div>
<script>
function copyCmd(btn) {
  const t = btn.closest('.cmd-wrapper').querySelector('.cmd-text').innerText.trim();
  navigator.clipboard.writeText(t).then(() => {
    const zh = document.documentElement.lang !== 'en';
    const orig = btn.innerText;
    btn.innerText = zh ? '已复制!' : 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.innerText = orig; btn.classList.remove('copied'); }, 2000);
  }).catch(() => {});
}
function switchLang(lang) {
  const url = new URL(window.location.href);
  url.searchParams.set('lang', lang);
  window.location.href = url.toString();
}
</script>
</body>
</html>`;
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(html);
      return;
    }

    if (req.method !== "POST") {
      res.writeHead(405, { Allow: "GET, POST, OPTIONS" });
      res.end("Method Not Allowed");
      return;
    }

    let raw = "";
    req.on("data", (c) => (raw += c));
    req.on("end", () => {
      let body;
      try {
        body = JSON.parse(raw);
      } catch (e) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(error(null, -32700, "Parse error"));
        return;
      }
      if (Array.isArray(body)) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(error(null, -32600, "Batch requests not supported"));
        return;
      }
      const out = handleRequest(base, body);
      const done = (s) => {
        res.writeHead(200, {
          "Content-Type": "application/json",
          "Mcp-Session-Id": "static",
        });
        res.end(s);
      };
      if (out && typeof out.then === "function") {
        out.then(done).catch((e) => {
          res.writeHead(500, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ jsonrpc: "2.0", id: body.id, error: { code: -32603, message: e.message } }));
        });
      } else {
        done(out);
      }
    });
  });

  server.listen(port, "0.0.0.0", () => {
    process.stderr.write(
      `\nErisPulse MCP server is running (http).\n` +
        `  docs: ${base}\n` +
        `  endpoint: http://localhost:${port}/\n` +
        `  use in MCP client as url: http://localhost:${port}/\n\n`
    );
  });
  server.on("error", (err) => {
    process.stderr.write(`ErisPulse MCP HTTP server error: ${err.message}\n`);
    process.exit(1);
  });
}

let mode = "stdio";
let port = 8765;
{
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--http" || a === "--serve") {
      mode = "http";
      continue;
    }
    if (a === "--server" || a === "-s") {
      mode = "stdio";
      continue;
    }
    if (a === "--port" || a === "-p") {
      const next = argv[++i];
      const n = parseInt(next, 10);
      if (!next || !Number.isFinite(n) || n <= 0 || n > 65535) {
        process.stderr.write("usage: --port <1-65535>\n");
        process.exit(2);
      }
      port = n;
      continue;
    }
    process.stderr.write(
      "usage: epsdk-mcp [--server|--http] [--port N]\n" +
        "  --server    启动 MCP 服务（stdio，默认）。\n" +
        "  --http      启动 MCP 服务（HTTP，MCP 客户端 url 接入或浏览器/curl 访问）。\n" +
        "  --port      --http 模式监听端口（默认 8765）。\n" +
        "  ERISPULSE_DOCS_DIR 指向本地文档目录时不联网。\n"
    );
    process.exit(2);
  }
}

main(mode, port).catch((e) => {
  process.stderr.write(`ErisPulse MCP startup failed: ${e.message}\n`);
  process.exit(1);
});