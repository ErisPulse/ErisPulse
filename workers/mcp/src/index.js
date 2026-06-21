/**
 * ErisPulse MCP Server (Cloudflare Worker)
 *
 * 通过 MCP（Model Context Protocol）Streamable HTTP 传输，
 * 把 ErisPulse 官方文档暴露给 AI 编码助手（Claude Desktop / Cursor / 任意 MCP 客户端），
 * 让用户在 VIBE Coding 时可以让 AI 直接检索/查阅文档。
 *
 * 设计参考了前端 builder.js 的检索逻辑（BM25 + Markdown 分块），
 * 但运行在 Cloudflare Worker 上：
 *  - 文档源：https://raw.githubusercontent.com/ErisPulse/ErisPulse/Develop/v2/docs/
 *  - 缓存：Cloudflare Cache API（4 小时）+ 同 isolate 内存缓存
 *  - 协议：MCP 2025-03-26（Streamable HTTP），无状态实现（每次请求独立）
 *
 * 暴露的工具（tools）：
 *  - search_docs(query, top_k?, lang?)  —— BM25 关键词检索官方文档
 *  - read_document(doc_path, lang?)     —— 读取单篇文档完整内容
 *  - list_documents(lang?)              —— 列出所有文档标题与路径
 *  - list_languages()                   —— 列出文档支持的语言
 *
 * 暴露的资源（resources，可选）：
 *  - erispulse://docs/{lang}/{path}     —— 单篇文档作为 MCP resource
 *
 * 部署域名：mcp.erisdev.com
 */

// ============================================================
// 0. 常量与配置
// ============================================================

const DOCS_BASE =
  "https://raw.githubusercontent.com/ErisPulse/ErisPulse/Develop/v2/docs/";
const DOCS_PROXY_BASE =
  "https://cdn.gh-proxy.org/https://raw.githubusercontent.com/ErisPulse/ErisPulse/Develop/v2/docs/";
const MAPPING_INDEX_URL = DOCS_BASE + "_meta/docs-mapping.json"; // 顶层语言索引

const DEFAULT_LANG = "zh-CN";
const CACHE_TTL_SECONDS = 4 * 60 * 60; // 4 小时，与主站 Worker 一致
const SUPPORTED_LANGS = ["zh-CN", "en", "zh-TW", "ja", "ru"];

const PROTOCOL_VERSION = "2025-03-26"; // Streamable HTTP
const SERVER_NAME = "erispulse-docs";
const SERVER_VERSION = "1.0.0";

// 访问控制：
//  - 若环境变量配置了 MCP_TOKEN，则所有请求必须带 Authorization: Bearer <token>
//    或 X-MCP-Token: <token>。未配置则完全公开（建议配合 Cloudflare Rate Limiting）。
//  - 速率限制：每 IP 每分钟 60 次（命中 Cache API 计数），超过返回 429。
const RATE_LIMIT_PER_MIN = 60;
const RATE_LIMIT_WINDOW_SEC = 60;

// ============================================================
// 1. CORS / 通用响应助手
// ============================================================

// MCP 客户端多数不是浏览器，但仍允许浏览器客户端访问（如未来加入 Web 端）
function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers":
      "Content-Type, Accept, Authorization, Mcp-Session-Id, Last-Event-ID",
    "Access-Control-Expose-Headers": "Mcp-Session-Id",
    "Access-Control-Max-Age": "86400",
  };
}

function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...corsHeaders(),
      ...extraHeaders,
    },
  });
}

function jsonRpcResponse(id, result, extraHeaders = {}) {
  return json({ jsonrpc: "2.0", id, result }, 200, extraHeaders);
}

function jsonRpcError(id, code, message, data = undefined) {
  const err = { code, message };
  if (data !== undefined) err.data = data;
  return json({ jsonrpc: "2.0", id, error: err });
}

// ============================================================
// 2. BM25 检索（移植自前端 builder.js）
// ============================================================

const CJK_RE = /[\u4e00-\u9fff\u3400-\u4dbf]/g;
const WORD_RE = /[a-z0-9]+/g;

/**
 * 分词：英文单词 + 中文单字 + 中文双字组合
 */
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
    this.avgdl =
      this.N === 0 ? 0 : this.docLen.reduce((s, n) => s + n, 0) / this.N;

    const df = {};
    this.tf = docs.map((d) => {
      const freq = {};
      for (const t of d.tokens) freq[t] = (freq[t] || 0) + 1;
      for (const t of Object.keys(freq)) df[t] = (df[t] || 0) + 1;
      return freq;
    });

    this.idf = {};
    for (const t of Object.keys(df)) {
      this.idf[t] = Math.log(1 + (this.N - df[t] + 0.5) / (df[t] + 0.5));
    }
  }

  search(query, topK = 5) {
    const qTokens = tokenize(query);
    if (qTokens.length === 0 || this.N === 0) return [];

    const scores = new Array(this.N).fill(0);
    const seenTerms = new Set(qTokens);

    for (const term of seenTerms) {
      const idf = this.idf[term];
      if (idf === undefined) continue;
      for (let i = 0; i < this.N; i++) {
        const f = this.tf[i][term];
        if (!f) continue;
        const dl = this.docLen[i] || 1;
        const denom =
          f + this.k1 * (1 - this.b + this.b * (dl / (this.avgdl || 1)));
        scores[i] += (idf * f * (this.k1 + 1)) / denom;
      }
    }

    const ranked = [];
    for (let i = 0; i < this.N; i++) {
      if (scores[i] > 0) ranked.push({ index: i, score: scores[i] });
    }
    ranked.sort((a, b) => b.score - a.score);
    return ranked.slice(0, topK);
  }
}

/**
 * Markdown 按标题分块，每块最大约 1000 字符
 */
function chunkDocument(docPath, title, content) {
  const chunks = [];
  const lines = String(content || "").split("\n");
  const MAX = 1000;

  let currentHeading = title || docPath;
  let buffer = [];

  const flush = () => {
    if (buffer.length === 0) return;
    let text = buffer.join("\n");
    while (text.length > MAX) {
      const slice = text.slice(0, MAX);
      chunks.push({
        docId: docPath,
        title: currentHeading,
        content: slice,
        tokens: tokenize(slice),
      });
      text = text.slice(MAX);
    }
    if (text.trim().length > 0) {
      chunks.push({
        docId: docPath,
        title: currentHeading,
        content: text,
        tokens: tokenize(text),
      });
    }
    buffer = [];
  };

  const headingRe = /^#{1,4}\s+/;
  for (const line of lines) {
    if (headingRe.test(line)) {
      flush();
      currentHeading = `${title || docPath} » ${line
        .replace(/^#+\s+/, "")
        .trim()}`;
    }
    buffer.push(line);
  }
  flush();
  return chunks;
}

// ============================================================
// 3. 文档加载（两级缓存：isolate 内存 + Cache API）
// ============================================================

// 内存缓存：每个 Worker isolate 复用同一个索引
const memCache = new Map(); // lang -> { chunks, docList, bm25, ts }

// ============================================================
// 访问控制：Token 校验 + IP 速率限制
// ============================================================

function getToken(env) {
  // 优先环境变量 MCP_TOKEN，其次 ALLOWED_TOKEN（兼容）
  return env?.MCP_TOKEN || env?.ALLOWED_TOKEN || "";
}

function checkToken(request, env) {
  const expected = getToken(env);
  if (!expected) return true; // 未配置 token = 公开访问

  const auth = request.headers.get("Authorization") || "";
  if (auth.startsWith("Bearer ") && auth.slice(7) === expected) return true;

  const xToken = request.headers.get("X-MCP-Token") || "";
  if (xToken === expected) return true;

  return false;
}

function clientIp(request) {
  // Cloudflare 把真实客户端 IP 放在 CF-Connecting-IP
  return (
    request.headers.get("CF-Connecting-IP") ||
    request.headers.get("X-Real-IP") ||
    "0.0.0.0"
  );
}

async function checkRateLimit(ip) {
  // 用 Cache API 做简单计数窗口（无需 KV）
  // key 里带分钟桶，1 分钟自动过期
  const bucket = Math.floor(Date.now() / 1000 / RATE_LIMIT_WINDOW_SEC);
  const cache = caches.default;
  const cacheKey = new Request(
    `https://mcp.erispulse.internal/rl/${ip}/${bucket}`,
  );
  let count = 0;
  try {
    const hit = await cache.match(cacheKey);
    if (hit) count = parseInt(await hit.text(), 10) || 0;
  } catch (e) {}
  count += 1;
  if (count > RATE_LIMIT_PER_MIN) return { allowed: false, count };
  try {
    const resp = new Response(String(count), {
      headers: { "Cache-Ttl": String(RATE_LIMIT_WINDOW_SEC + 5) },
    });
    await cache.put(cacheKey, resp);
  } catch (e) {}
  return { allowed: true, count };
}

async function fetchTextWithFallback(url, proxyUrl) {
  // 直连 GitHub 失败时回退到 gh-proxy（国内可用性更好）
  const targets = [url];
  if (proxyUrl) targets.push(proxyUrl);
  let lastErr;
  for (const u of targets) {
    try {
      const res = await fetch(u, {
        cf: { cacheEverything: true, cacheTtl: CACHE_TTL_SECONDS },
      });
      if (res.ok) return await res.text();
      lastErr = new Error(`HTTP ${res.status} for ${u}`);
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr || new Error("fetch failed");
}

async function fetchJsonWithFallback(url, proxyUrl) {
  const text = await fetchTextWithFallback(url, proxyUrl);
  return JSON.parse(text);
}

/**
 * 加载某语言的文档映射（_meta/{lang}/docs-mapping.json）
 */
async function loadLangMapping(lang) {
  const url = DOCS_BASE + `_meta/${lang}/docs-mapping.json`;
  const proxyUrl = DOCS_PROXY_BASE + `_meta/${lang}/docs-mapping.json`;
  return fetchJsonWithFallback(url, proxyUrl);
}

/**
 * 从语言映射里平铺出所有 { path, title, category } 列表
 */
function flattenMapping(mapping) {
  const docs = [];
  if (!mapping || !mapping.categories) return docs;
  for (const [catName, category] of Object.entries(mapping.categories)) {
    if (Array.isArray(category.documents)) {
      for (const d of category.documents) {
        docs.push({
          path: d.path,
          title: d.title,
          category: catName,
          level: d.level,
        });
      }
    }
    if (category.subgroups) {
      for (const sg of Object.values(category.subgroups)) {
        if (!Array.isArray(sg.documents)) continue;
        for (const d of sg.documents) {
          docs.push({
            path: d.path,
            title: d.title,
            category: catName,
            level: d.level,
          });
        }
      }
    }
  }
  return docs;
}

/**
 * 构建（或从缓存读取）某语言的文档知识库：{ chunks, docList, bm25 }
 */
async function buildKnowledgeBase(lang) {
  lang = SUPPORTED_LANGS.includes(lang) ? lang : DEFAULT_LANG;

  // 1. 内存缓存：5 分钟内直接复用
  const now = Date.now();
  const memEntry = memCache.get(lang);
  if (memEntry && now - memEntry.ts < 5 * 60 * 1000) {
    return memEntry;
  }

  // 2. Cache API：跨 isolate 复用，避免重复抓取 + 分词
  const cache = caches.default;
  const cacheKey = new Request(`https://mcp.erispulse.internal/kb/${lang}`);
  try {
    const cached = await cache.match(cacheKey);
    if (cached) {
      const data = await cached.json();
      const bm25 = new BM25Index(data.chunks);
      const entry = {
        chunks: data.chunks,
        docList: data.docList,
        bm25,
        ts: now,
      };
      memCache.set(lang, entry);
      return entry;
    }
  } catch (e) {
    /* ignore */
  }

  // 3. 缓存未命中：抓取所有文档 → 分块
  const mapping = await loadLangMapping(lang);
  const docList = flattenMapping(mapping);

  const chunks = [];
  await Promise.all(
    docList.map(async (doc) => {
      try {
        const url = DOCS_BASE + `${lang}/${doc.path}`;
        const proxyUrl = DOCS_PROXY_BASE + `${lang}/${doc.path}`;
        const content = await fetchTextWithFallback(url, proxyUrl);
        for (const c of chunkDocument(doc.path, doc.title, content)) {
          chunks.push(c);
        }
      } catch (e) {
        /* 跳过单篇失败 */
      }
    }),
  );

  const bm25 = new BM25Index(chunks);
  const entry = { chunks, docList, bm25, ts: now };
  memCache.set(lang, entry);

  // 写入 Cache API（仅持久化纯数据，bm25 在读出后重建）
  try {
    const resp = new Response(JSON.stringify({ chunks, docList, ts: now }), {
      headers: {
        "Content-Type": "application/json",
        "Cache-Ttl": String(CACHE_TTL_SECONDS),
      },
    });
    await cache.put(cacheKey, resp);
  } catch (e) {
    /* ignore */
  }

  return entry;
}

// ============================================================
// 4. 工具定义（MCP tools/list 输出）
// ============================================================

const TOOL_DEFINITIONS = [
  {
    name: "search_docs",
    description:
      "使用 BM25 关键词检索 ErisPulse 官方文档。可一次传入多个关键词（空格分隔），" +
      "如 '命令注册 事件监听 配置 存储'。返回最相关的文档片段（doc_path / title / snippet / score）。" +
      "优先用它定位 SDK API，避免编造不存在的接口。",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "搜索关键词（支持中英文混排，可一次覆盖多个主题）",
        },
        top_k: {
          type: "integer",
          description: "返回结果数量上限，默认 5",
          default: 5,
          minimum: 1,
          maximum: 20,
        },
        lang: {
          type: "string",
          description:
            "文档语言代码，默认 zh-CN。可选：zh-CN / en / zh-TW / ja / ru",
          default: DEFAULT_LANG,
          enum: SUPPORTED_LANGS,
        },
      },
      required: ["query"],
    },
  },
  {
    name: "read_document",
    description:
      "读取 ErisPulse 某篇文档的完整 Markdown 内容。当 search_docs 已定位到具体文档、" +
      "或你知道文档 path（如 'quick-start.md'、'developer-guide/modules/getting-started.md'）时使用。",
    inputSchema: {
      type: "object",
      properties: {
        doc_path: {
          type: "string",
          description: "文档相对路径，如 'quick-start.md'",
        },
        lang: {
          type: "string",
          description: "文档语言代码，默认 zh-CN",
          default: DEFAULT_LANG,
          enum: SUPPORTED_LANGS,
        },
      },
      required: ["doc_path"],
    },
  },
  {
    name: "list_documents",
    description:
      "列出 ErisPulse 当前语言下所有可用文档的标题、路径与所属分类。" +
      "在不知道有哪些文档时先调用它。",
    inputSchema: {
      type: "object",
      properties: {
        lang: {
          type: "string",
          description: "文档语言代码，默认 zh-CN",
          default: DEFAULT_LANG,
          enum: SUPPORTED_LANGS,
        },
      },
      required: [],
    },
  },
  {
    name: "list_languages",
    description: "列出 ErisPulse 文档支持的所有语言及各语言的文档数量。",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
];

// ============================================================
// 5. 工具实现
// ============================================================

async function toolSearchDocs(args) {
  const query = String(args?.query || "").trim();
  if (!query) {
    return textContent("错误：query 不能为空。");
  }
  const topK = clampInt(args?.top_k, 5, 1, 20);
  const lang = pickLang(args?.lang);

  const kb = await buildKnowledgeBase(lang);
  const results = kb.bm25.search(query, topK).map((r) => {
    const c = kb.chunks[r.index];
    const snippet =
      c.content.length > 500 ? c.content.slice(0, 500) + "..." : c.content;
    return {
      doc_path: c.docId,
      title: c.title,
      snippet,
      score: Number(r.score.toFixed(4)),
    };
  });

  if (results.length === 0) {
    return textContent(
      `未找到与 "${query}" 相关的文档（语言：${lang}）。` +
        `可尝试换关键词，或先调用 list_documents 查看可用文档。`,
    );
  }
  return textContent(JSON.stringify(results, null, 2));
}

async function toolReadDocument(args) {
  const docPath = String(args?.doc_path || "").trim();
  if (!docPath) return textContent("错误：doc_path 不能为空。");
  const lang = pickLang(args?.lang);

  const url = DOCS_BASE + `${lang}/${docPath}`;
  const proxyUrl = DOCS_PROXY_BASE + `${lang}/${docPath}`;
  try {
    const content = await fetchTextWithFallback(url, proxyUrl);
    return textContent(content);
  } catch (e) {
    return textContent(
      `读取文档失败：${docPath}（语言：${lang}）。请检查路径是否正确，` +
        `可用 list_documents 查看所有文档路径。错误：${e.message}`,
    );
  }
}

async function toolListDocuments(args) {
  const lang = pickLang(args?.lang);
  const kb = await buildKnowledgeBase(lang);
  const list = kb.docList.map((d) => ({
    path: d.path,
    title: d.title,
    category: d.category,
  }));
  return textContent(
    `ErisPulse 文档清单（语言：${lang}，共 ${list.length} 篇）：\n\n` +
      JSON.stringify(list, null, 2),
  );
}

async function toolListLanguages() {
  const url = MAPPING_INDEX_URL;
  const proxyUrl = DOCS_PROXY_BASE + "_meta/docs-mapping.json";
  try {
    const data = await fetchJsonWithFallback(url, proxyUrl);
    const langs = Object.entries(data.languages || {}).map(([code, info]) => ({
      code,
      docs_count: info.docs_count,
    }));
    return textContent(
      "ErisPulse 文档支持的语言：\n\n" + JSON.stringify(langs, null, 2),
    );
  } catch (e) {
    return textContent(
      JSON.stringify(
        SUPPORTED_LANGS.map((code) => ({ code, docs_count: "未知" })),
        null,
        2,
      ),
    );
  }
}

const TOOL_HANDLERS = {
  search_docs: toolSearchDocs,
  read_document: toolReadDocument,
  list_documents: toolListDocuments,
  list_languages: toolListLanguages,
};

// ============================================================
// 6. MCP 方法分发
// ============================================================

function textContent(text) {
  return { content: [{ type: "text", text }] };
}

function clampInt(v, def, min, max) {
  const n = Math.floor(Number(v));
  if (!Number.isFinite(n)) return def;
  return Math.max(min, Math.min(max, n));
}

function pickLang(lang) {
  return SUPPORTED_LANGS.includes(lang) ? lang : DEFAULT_LANG;
}

function newSessionId() {
  // 无状态实现，仅用于兼容要求 Mcp-Session-Id 的客户端
  return (
    "mcp-" +
    Date.now().toString(36) +
    "-" +
    Math.random().toString(36).slice(2, 10)
  );
}

async function handleMcpRequest(body) {
  const { jsonrpc, id, method, params } = body;

  // JSON-RPC 基础校验
  if (jsonrpc !== "2.0") {
    return {
      response: jsonRpcError(id, -32600, "Invalid Request"),
      isNotification: false,
    };
  }

  // 通知（无 id）：无需返回 JSON-RPC 结果，但 HTTP 层返回 202
  const isNotification = id === undefined || id === null;

  switch (method) {
    case "initialize": {
      const result = {
        protocolVersion: PROTOCOL_VERSION,
        serverInfo: { name: SERVER_NAME, version: SERVER_VERSION },
        capabilities: {
          tools: { listChanged: false },
          resources: { listChanged: false },
        },
      };
      // 即便无状态，也下发一个 sessionId 以兼容严格客户端
      return {
        response: jsonRpcResponse(id, result, {
          "Mcp-Session-Id": newSessionId(),
        }),
        isNotification: false,
      };
    }

    case "notifications/initialized": {
      // 客户端初始化完成的握手通知
      return {
        response: new Response(null, { status: 202 }),
        isNotification: true,
      };
    }

    case "ping": {
      if (isNotification)
        return {
          response: new Response(null, { status: 202 }),
          isNotification: true,
        };
      return { response: jsonRpcResponse(id, {}), isNotification: false };
    }

    case "tools/list": {
      if (isNotification)
        return {
          response: new Response(null, { status: 202 }),
          isNotification: true,
        };
      return {
        response: jsonRpcResponse(id, { tools: TOOL_DEFINITIONS }),
        isNotification: false,
      };
    }

    case "tools/call": {
      if (isNotification)
        return {
          response: new Response(null, { status: 202 }),
          isNotification: true,
        };
      const name = params?.name;
      const args = params?.arguments || {};
      const handler = TOOL_HANDLERS[name];
      if (!handler) {
        return {
          response: jsonRpcError(id, -32602, `Unknown tool: ${name}`),
          isNotification: false,
        };
      }
      try {
        const result = await handler(args);
        return {
          response: jsonRpcResponse(id, result),
          isNotification: false,
        };
      } catch (e) {
        return {
          response: jsonRpcError(
            id,
            -32603,
            `Tool execution failed: ${e.message}`,
          ),
          isNotification: false,
        };
      }
    }

    case "resources/list": {
      if (isNotification)
        return {
          response: new Response(null, { status: 202 }),
          isNotification: true,
        };
      const lang = pickLang(params?.uri?.split("/")?.[3] || params?.lang);
      const kb = await buildKnowledgeBase(lang);
      const resources = kb.docList.map((d) => ({
        uri: `erispulse://docs/${lang}/${d.path}`,
        name: d.title,
        description: `ErisPulse 文档 · ${d.category}`,
        mimeType: "text/markdown",
      }));
      return {
        response: jsonRpcResponse(id, { resources }),
        isNotification: false,
      };
    }

    case "resources/read": {
      if (isNotification)
        return {
          response: new Response(null, { status: 202 }),
          isNotification: true,
        };
      const uri = String(params?.uri || "");
      // 形如：erispulse://docs/{lang}/{path}
      const m = uri.match(/^erispulse:\/\/docs\/([^/]+)\/(.+)$/);
      if (!m) {
        return {
          response: jsonRpcError(id, -32602, `Invalid resource URI: ${uri}`),
          isNotification: false,
        };
      }
      const [, lang, path] = m;
      try {
        const url = DOCS_BASE + `${lang}/${path}`;
        const proxyUrl = DOCS_PROXY_BASE + `${lang}/${path}`;
        const text = await fetchTextWithFallback(url, proxyUrl);
        return {
          response: jsonRpcResponse(id, {
            contents: [{ uri, mimeType: "text/markdown", text }],
          }),
          isNotification: false,
        };
      } catch (e) {
        return {
          response: jsonRpcError(
            id,
            -32603,
            `Failed to read resource ${uri}: ${e.message}`,
          ),
          isNotification: false,
        };
      }
    }

    default:
      return {
        response: jsonRpcError(id, -32601, `Method not found: ${method}`),
        isNotification: false,
      };
  }
}

// ============================================================
// 7. 人类访问的着陆页（GET /）
// ============================================================

function landingPage() {
  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>ErisPulse MCP Server</title>
<style>
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;max-width:760px;margin:40px auto;padding:0 20px;color:#222;line-height:1.6}
  code,pre{background:#f5f5f7;padding:2px 6px;border-radius:4px;font-family:"SF Mono",Menlo,Consolas,monospace;font-size:0.9em}
  pre{padding:16px;overflow-x:auto}
  h1{margin-bottom:8px}
  .tag{display:inline-block;background:#6366f1;color:#fff;padding:2px 10px;border-radius:12px;font-size:12px;margin-left:8px;vertical-align:middle}
  a{color:#6366f1}
</style>
</head>
<body>
<h1>ErisPulse MCP Server <span class="tag">mcp.erisdev.com</span></h1>
<p>本端点为 AI 编码助手提供 ErisPulse 官方文档检索能力（MCP Streamable HTTP）。</p>

<h2>支持的 MCP 工具</h2>
<ul>
  <li><code>search_docs(query, top_k?, lang?)</code> — BM25 关键词检索</li>
  <li><code>read_document(doc_path, lang?)</code> — 读取单篇文档</li>
  <li><code>list_documents(lang?)</code> — 列出所有文档</li>
  <li><code>list_languages()</code> — 列出支持的语言</li>
</ul>

<h2>在客户端中接入</h2>
<p>Claude Desktop（<code>claude_desktop_config.json</code>）：</p>
<pre>{
  "mcpServers": {
    "erispulse": {
      "url": "https://mcp.erisdev.com/"
    }
  }
}</pre>

<p>Cursor / 通用 MCP 客户端：</p>
<pre>{
  "mcpServers": {
    "erispulse": {
      "url": "https://mcp.erisdev.com/"
    }
  }
}</pre>

<p>直接发送 JSON-RPC 请求测试：</p>
<pre>curl -X POST https://mcp.erisdev.com/ \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'</pre>

<h2>文档源</h2>
<p><a href="https://github.com/ErisPulse/ErisPulse/tree/Develop/v2/docs">github.com/ErisPulse/ErisPulse · Develop/v2/docs</a></p>
</body>
</html>`;
  return new Response(html, {
    headers: { "Content-Type": "text/html; charset=utf-8", ...corsHeaders() },
  });
}

// ============================================================
// 8. 主入口
// ============================================================

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const method = request.method;

    // CORS 预检（不受鉴权/限流约束）
    if (method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }

    // GET 着陆页 / 健康检查：不受鉴权/限流约束
    if (method === "GET") {
      if (url.pathname === "/" || url.pathname === "/health") {
        return landingPage();
      }
      return new Response("Not Found", { status: 404 });
    }

    // DELETE：客户端关闭会话（无状态，直接 200 即可）
    if (method === "DELETE") {
      return new Response(null, { status: 200, headers: corsHeaders() });
    }

    // MCP 主路径：POST /
    if (method !== "POST") {
      return new Response("Method Not Allowed", {
        status: 405,
        headers: { Allow: "POST, GET, OPTIONS", ...corsHeaders() },
      });
    }

    // —— 访问控制（仅对 POST 生效）——
    // 1) Token（可选）
    if (!checkToken(request, env)) {
      return json(
        {
          jsonrpc: "2.0",
          id: null,
          error: {
            code: -32001,
            message:
              "Unauthorized: missing or invalid token. Set Authorization: Bearer <token> or X-MCP-Token.",
          },
        },
        401,
      );
    }

    // 2) 速率限制（按 IP，每分钟 60 次）
    const ip = clientIp(request);
    const rl = await checkRateLimit(ip);
    if (!rl.allowed) {
      return json(
        {
          jsonrpc: "2.0",
          id: null,
          error: {
            code: -32000,
            message: `Rate limit exceeded: ${rl.count} requests/min from this IP. Try again in a minute.`,
          },
        },
        429,
        { "Retry-After": String(RATE_LIMIT_WINDOW_SEC) },
      );
    }

    let body;
    try {
      body = await request.json();
    } catch (e) {
      return json(
        {
          jsonrpc: "2.0",
          id: null,
          error: { code: -32700, message: "Parse error" },
        },
        400,
      );
    }

    // 暂不支持批量请求（MCP 客户端一般一次一发）
    if (Array.isArray(body)) {
      return json(
        {
          jsonrpc: "2.0",
          id: null,
          error: { code: -32600, message: "Batch requests not supported" },
        },
        400,
      );
    }

    try {
      const { response } = await handleMcpRequest(body);
      return response;
    } catch (e) {
      return jsonRpcError(body.id, -32603, `Internal error: ${e.message}`);
    }
  },
};
