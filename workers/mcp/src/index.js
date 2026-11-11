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
const SERVER_VERSION = "1.0.4";

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
    `ErisPulse docs (lang: ${lang}, ${list.length} docs). Supported languages: ${SUPPORTED_LANGS.join(", ")}.\n\n` +
      JSON.stringify(list, null, 2),
  );
}

const TOOL_HANDLERS = {
  search_docs: toolSearchDocs,
  read_document: toolReadDocument,
  list_documents: toolListDocuments,
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
        instructions:
          `Retrieve ErisPulse docs with search_docs/read_document/list_documents. ` +
          `Supported languages: ${SUPPORTED_LANGS.join(", ")} (default zh-CN).`,
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
// 7. 人类访问的着陆页（GET /）—— 与 ErisPulse Dashboard 同一设计语言
// ============================================================

function pickRequestLang(request, url) {
  const q = (url && url.searchParams.get("lang")) || "";
  if (q === "zh") return "zh-CN";
  if (q === "en") return "en";
  const header = request.headers.get("Accept-Language") || "";
  if (/zh/i.test(header)) return "zh-CN";
  if (/en/i.test(header)) return "en";
  return "zh-CN";
}

const NPM_PACKAGE = "@erisdev/mcp-server";
const NPM_VERSION = "1.0.4";

const LANDING_I18N = {
  "zh-CN": {
    htmlLang: "zh-CN",
    title: "ErisPulse MCP Server",
    crumbs: "ErisPulse / MCP",
    lead: "两组 MCP 服务：官方文档检索（本站端点 / npm 本地包）与机器人运行时控制（ApiMCP 模块）。",
    chips: ["Streamable HTTP", "MCP 2025-03-26", "BM25 检索", "文档 5 语言"],
    docsTitle: "文档检索 MCP · erispulse-docs",
    docsDesc: "让 AI 编码助手直接检索、阅读 ErisPulse 官方文档。两种部署形态，工具集完全相同。",
    docsTabs: ["远程端点", "npm 本地包"],
    remoteDesc: "零依赖，客户端直连 Cloudflare Worker；文档缓存 4 小时，限流 60 次/分钟/IP。",
    remoteLabel: "客户端 mcpServers 配置",
    npmDesc: "本地 Node 进程（stdio 默认 / 可选 HTTP）。首次运行拉取文档缓存到 <code>~/.cache/erispulse-mcp</code>；设置 <code>ERISPULSE_DOCS_DIR</code> 可完全离线。",
    npmRunLabel: "运行（stdio）",
    npmHttpLabel: "HTTP 模式（自定义端口）",
    npmCfgLabel: "客户端 mcpServers 配置（stdio）",
    apiTitle: "机器人运行时 MCP · ApiMCP 模块",
    apiDesc: "把 <strong>框架运行时能力</strong>开放给 AI 客户端：收发消息、跨模块 RPC、模块热重载、适配器状态、事件流订阅、拓扑观测——AI 可以直接操作你的机器人，而不只是查文档。REST 桥挂框架内置 HTTP server（默认 <code>0.0.0.0:8000</code>），token 必须显式配置。",
    apiInstallLabel: "安装（机器人环境）",
    apiTokenLabel: "配置 token（config.toml [ApiMCP] 节）",
    apiCfgLabel: "Claude Desktop 配置",
    docsToolsTitle: "文档工具（3 个）",
    apiToolsTitle: "运行时工具（14 个）",
    apiToolsNote: "安全默认：限流 30 请求/分钟 · 模块重载默认允许 · 适配器重载默认禁用 · 模块调用白名单可配 · 私有方法拒绝",
    securityTitle: "访问控制",
    secItems: ["Bearer / X-MCP-Token 鉴权", "限流 60/min（远程）· 30/min（ApiMCP）", "事件环形缓冲 1000 条", "消息段摘要化（文本 500 字符）"],
    linksTitle: "相关链接",
    links: { repo: "框架仓库", npm: "npm 包", apimcp: "ApiMCP 模块", docs: "官方文档", site: "官方网站" },
    copyBtn: "复制",
    copiedBtn: "已复制!",
    foot: "ErisDev · MCP Server v" + NPM_VERSION,
  },
  en: {
    htmlLang: "en",
    title: "ErisPulse MCP Server",
    crumbs: "ErisPulse / MCP",
    lead: "Two MCP services: official docs retrieval (this endpoint / npm package) and bot runtime control (ApiMCP module).",
    chips: ["Streamable HTTP", "MCP 2025-03-26", "BM25 search", "Docs in 5 languages"],
    docsTitle: "Docs MCP · erispulse-docs",
    docsDesc: "Lets AI coding assistants search and read the official ErisPulse docs. Two deployment forms, identical toolset.",
    docsTabs: ["Remote endpoint", "npm local"],
    remoteDesc: "Zero-dependency: clients hit the Cloudflare Worker directly. Docs cached 4h, rate limit 60 req/min/IP.",
    remoteLabel: "Client mcpServers config",
    npmDesc: "Local Node process (stdio by default, HTTP optional). Docs are pulled on first run and cached under <code>~/.cache/erispulse-mcp</code>; set <code>ERISPULSE_DOCS_DIR</code> to stay fully offline.",
    npmRunLabel: "Run (stdio)",
    npmHttpLabel: "HTTP mode (custom port)",
    npmCfgLabel: "Client mcpServers config (stdio)",
    apiTitle: "Bot Runtime MCP · ApiMCP module",
    apiDesc: "Exposes the <strong>framework runtime</strong> to AI clients: send/receive messages, cross-module RPC, hot reload, adapter status, event streams, topology — AI can drive your bot, not just read docs. The REST bridge mounts on the framework HTTP server (default <code>0.0.0.0:8000</code>); a token must be configured explicitly.",
    apiInstallLabel: "Install (bot env)",
    apiTokenLabel: "Configure token (config.toml [ApiMCP])",
    apiCfgLabel: "Claude Desktop config",
    docsToolsTitle: "Docs tools (3)",
    apiToolsTitle: "Runtime tools (14)",
    apiToolsNote: "Secure defaults: 30 req/min rate limit · module reload allowed · adapter reload disabled by default · configurable call whitelist · private methods rejected",
    securityTitle: "Access control",
    secItems: ["Bearer / X-MCP-Token auth", "Rate limit 60/min (remote) · 30/min (ApiMCP)", "Ring buffer of 1000 events", "Message segments summarized (500 chars)"],
    linksTitle: "Resources",
    links: { repo: "Framework repo", npm: "npm package", apimcp: "ApiMCP module", docs: "Documentation", site: "Website" },
    copyBtn: "Copy",
    copiedBtn: "Copied!",
    foot: "ErisDev · MCP Server v" + NPM_VERSION,
  },
};

const LANDING_TOOLS_DOCS = [
  ["search_docs(query, top_k?, lang?)", "BM25 keyword search across official docs"],
  ["read_document(doc_path, lang?)", "read one full document (Markdown)"],
  ["list_documents(lang?)", "list all doc titles & paths"],
];

const LANDING_TOOLS_API = [
  ["list_modules", "list registered modules & status"],
  ["get_module_info(name)", "module registration + meta info"],
  ["call_module(name, method, args?, kwargs?)", "cross-module RPC (whitelist-guarded)"],
  ["reload_module(name)", "hot reload a module"],
  ["list_adapters", "list platform adapters & bots"],
  ["get_adapter_status(platform)", "per-platform runtime status"],
  ["reload_adapter(platform)", "adapter reload (off by default)"],
  ["send_message(platform, target_type, target_id, method, content)", "send Text/Image/Voice/Video/File"],
  ["recent_messages(platform?, session?, limit=50)", "recent messages via transcript"],
  ["subscribe_events(types)", "subscribe message/notice/request/meta/*"],
  ["unsubscribe(subscription_id)", "cancel a subscription"],
  ["poll_events(since_ts, since_seq, limit?, subscription_id?)", "incremental event polling"],
  ["get_topology", "runtime topology (sanitized)"],
  ["sdk_health", "SDK version / uptime / module & adapter summary"],
];

function landingPage(lang) {
  const t = LANDING_I18N[lang] || LANDING_I18N["zh-CN"];
  const isZh = lang === "zh-CN";
  const remoteJson = JSON.stringify(
    { mcpServers: { erispulse: { url: "https://mcp.erisdev.com/" } } },
    null,
    2,
  );
  const npmJson = JSON.stringify(
    { mcpServers: { erispulse: { command: "npx", args: ["-y", NPM_PACKAGE] } } },
    null,
    2,
  );
  const apiJson = JSON.stringify(
    {
      mcpServers: {
        erispulse: {
          command: "erispulse-apimcp",
          env: {
            ERISPULSE_APIMCP_URL: "http://127.0.0.1:8000",
            ERISPULSE_APIMCP_TOKEN: "your-token",
          },
        },
      },
    },
    null,
    2,
  );

  const docsToolsRows = LANDING_TOOLS_DOCS.map(
    (x) => '<div class="tool-row"><code>' + x[0] + "</code><span>" + x[1] + "</span></div>",
  ).join("");
  const apiToolsRows = LANDING_TOOLS_API.map(
    (x) => '<div class="tool-row"><code>' + x[0] + "</code><span>" + x[1] + "</span></div>",
  ).join("");
  const secChips = (t.secItems || [])
    .map((s) => '<span class="sec-chip">' + s + "</span>")
    .join("");

  const html = `<!DOCTYPE html>
<html lang="${t.htmlLang}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>${t.title}</title>
<style>
  :root {
    --bg-p: #f6f7f9; --bg-s: #eef0f3; --bg-t: #ffffff;
    --tx-p: #0a0a0a; --tx-s: #5f6b7a; --tx-t: #9aa4b1;
    --bd: #e5e8ec; --bd-h: #d0d6dd;
    --accent: #4aa3dd; --accent-fill: #3a94d0; --accent-soft: rgba(74,163,221,.14);
    --ok-c: #178a52; --ok-bg: #e9f8ef; --ok-bd: #bce8cd;
    --radius: 14px;
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    --font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  html[data-theme="dark"] {
    --bg-p: #0f1115; --bg-s: #161a20; --bg-t: #1c2027;
    --tx-p: #e6e9f0; --tx-s: #98a2b0; --tx-t: #5f6875;
    --bd: #272c35; --bd-h: #343b47;
    --accent: #6a9df0; --accent-fill: #4a85d8; --accent-soft: rgba(106,157,240,.16);
    --ok-c: #6fd6a1; --ok-bg: #12301f; --ok-bd: #1e5c3c;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: var(--font-sans); background: var(--bg-p); color: var(--tx-p); min-height: 100vh; line-height: 1.6; -webkit-font-smoothing: antialiased; }
  a { color: var(--accent-fill); text-decoration: none; }
  code { font-family: var(--font-mono); }
  .topbar { position: sticky; top: 10px; z-index: 10; width: min(1080px, calc(100% - 24px)); margin: 10px auto 0; background: var(--bg-t); border: 1px solid var(--bd); border-radius: var(--radius); padding: 0 18px; height: 54px; display: flex; align-items: center; gap: 12px; }
  .topbar .brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 15px; }
  .topbar .brand svg { width: 22px; height: 22px; color: var(--accent-fill); }
  .topbar .sp { flex: 1; }
  .round { width: 34px; height: 34px; border-radius: 8px; background: var(--bg-t); border: 1px solid var(--bd); display: flex; align-items: center; justify-content: center; color: var(--tx-s); cursor: pointer; transition: color .15s ease, border-color .15s ease; }
  .round:hover { border-color: var(--accent); color: var(--accent); }
  .round svg { width: 17px; height: 17px; }
  .container { max-width: 1080px; margin: 0 auto; padding: 28px 24px 64px; }
  .header { margin-bottom: 26px; }
  .crumbs { color: var(--tx-t); font-size: 13px; margin-bottom: 6px; }
  .header h1 { font-size: 30px; font-weight: 800; letter-spacing: -0.02em; }
  .header .sub { color: var(--tx-s); font-size: 15px; margin-top: 6px; max-width: 680px; }
  .badges { display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap; }
  .chip { padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: 600; background: var(--bg-s); color: var(--tx-s); border: 1px solid var(--bd); }
  .card { background: var(--bg-t); border: 1px solid var(--bd); border-radius: var(--radius); padding: 22px; transition: border-color .2s ease; }
  .card:hover { border-color: var(--bd-h); }
  .card + .card { margin-top: 16px; }
  .card-head { display: flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 700; margin-bottom: 16px; }
  .card-head svg { width: 19px; height: 19px; color: var(--accent-fill); flex: none; }
  .tabs { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 18px; }
  .tab-btn { padding: 7px 16px; border-radius: 8px; border: 1px solid var(--bd); background: var(--bg-s); color: var(--tx-s); font-size: 13px; font-weight: 600; cursor: pointer; font-family: inherit; }
  .tab-btn.active { background: var(--accent-fill); border-color: var(--accent-fill); color: #fff; }
  .tab-pane { display: none; }
  .tab-pane.active { display: block; }
  .pane-desc { color: var(--tx-s); font-size: 14px; margin-bottom: 14px; }
  .pane-desc code { color: var(--accent-fill); background: var(--accent-soft); padding: 2px 6px; border-radius: 5px; font-size: 12px; }
  .cmd-wrapper { border: 1px solid var(--bd); border-radius: 12px; overflow: hidden; margin-bottom: 12px; background: var(--bg-s); }
  .cmd-label { padding: 8px 16px; font-size: 12px; color: var(--tx-s); border-bottom: 1px solid var(--bd); }
  .cmd-content { padding: 14px 16px; font-size: 13px; display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
  .cmd-content pre { flex: 1; font-family: var(--font-mono); margin: 0; overflow-x: auto; scrollbar-width: thin; }
  .btn { background: var(--accent-fill); color: #fff; border: none; padding: 7px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; white-space: nowrap; font-family: inherit; }
  .btn:hover { filter: brightness(.94); }
  .btn.ok { background: var(--ok-c); }
  .tools-grid { display: grid; grid-template-columns: 1fr; gap: 0; }
  .tool-row { display: flex; flex-direction: column; gap: 2px; padding: 10px 4px; border-bottom: 1px solid var(--bd); }
  .tool-row:last-child { border-bottom: none; }
  .tool-row code { color: var(--tx-p); background: var(--bg-s); padding: 2px 8px; border-radius: 6px; font-size: 12.5px; width: fit-content; }
  .tool-row span { color: var(--tx-s); font-size: 13px; }
  .note { margin-top: 12px; font-size: 12.5px; color: var(--tx-t); }
  .sec-chips { display: flex; flex-wrap: wrap; gap: 8px; }
  .sec-chip { padding: 4px 12px; border-radius: 999px; font-size: 12px; background: var(--ok-bg); color: var(--ok-c); border: 1px solid var(--ok-bd); }
  .links-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
  .link-item { display: flex; align-items: center; justify-content: center; padding: 12px; background: var(--bg-s); border: 1px solid var(--bd); border-radius: 10px; color: var(--tx-s); text-decoration: none; font-size: 14px; font-weight: 600; transition: color .15s ease, border-color .15s ease; }
  .link-item:hover { background: var(--accent-soft); border-color: var(--accent); color: var(--accent-fill); }
  .foot { margin-top: 32px; text-align: center; color: var(--tx-t); font-size: 13px; }
  .lang-switch { display: inline-flex; background: var(--bg-s); border: 1px solid var(--bd); border-radius: 999px; overflow: hidden; margin-top: 12px; }
  .lang-btn { padding: 6px 16px; font-size: 12px; background: transparent; border: none; color: var(--tx-s); cursor: pointer; font-family: inherit; }
  .lang-btn.active { background: var(--accent-fill); color: #fff; }
  @media (max-width: 760px) { .container { padding: 20px 14px 40px; } .cmd-content { flex-direction: column; align-items: stretch; } .btn { width: 100%; } }
</style>
</head>
<body>
<div class="topbar">
  <div class="brand"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg><span>ErisPulse</span></div>
  <div class="sp"></div>
  <button class="round" id="themeBtn" onclick="toggleTheme()" title="Theme" aria-label="Toggle theme">
    <svg id="themeIcon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
  </button>
  <a class="round" href="https://github.com/ErisPulse/ErisPulse" target="_blank" rel="noopener noreferrer" title="GitHub" aria-label="GitHub">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55 0-.27-.01-1.17-.02-2.12-3.2.7-3.87-1.36-3.87-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.19 1.76 1.19 1.03 1.75 2.69 1.25 3.34.95.1-.74.4-1.25.72-1.53-2.55-.29-5.23-1.28-5.23-5.68 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.1 11.1 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.83 1.19 3.09 0 4.41-2.69 5.38-5.25 5.67.41.35.77 1.05.77 2.12 0 1.53-.01 2.76-.01 3.14 0 .3.2.67.8.55A11.51 11.51 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z"/></svg>
  </a>
</div>

<div class="container">
  <div class="header">
    <div class="crumbs">${t.crumbs}</div>
    <h1>${t.title}</h1>
    <div class="sub">${t.lead}</div>
    <div class="badges">${t.chips.map((c) => '<span class="chip">' + c + "</span>").join("")}</div>
  </div>

  <div class="card">
    <div class="card-head"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>${t.docsTitle}</div>
    <p class="pane-desc">${t.docsDesc}</p>
    <div class="tabs">
      ${t.docsTabs.map((n, i) => '<button class="tab-btn' + (i === 0 ? " active" : "") + '" onclick="switchTab(' + i + ')">' + n + "</button>").join("")}
    </div>

    <div class="tab-pane active" id="pane-0">
      <p class="pane-desc">${t.remoteDesc}</p>
      <div class="cmd-wrapper">
        <div class="cmd-label">${t.remoteLabel}</div>
        <div class="cmd-content"><pre>${remoteJson}</pre><button class="btn" data-copy>${t.copyBtn}</button></div>
      </div>
    </div>

    <div class="tab-pane" id="pane-1">
      <p class="pane-desc">${t.npmDesc}</p>
      <div class="cmd-wrapper">
        <div class="cmd-label">${t.npmRunLabel}</div>
        <div class="cmd-content"><pre>npx -y ${NPM_PACKAGE}</pre><button class="btn" data-copy>${t.copyBtn}</button></div>
      </div>
      <div class="cmd-wrapper">
        <div class="cmd-label">${t.npmHttpLabel}</div>
        <div class="cmd-content"><pre>epsdk-mcp --http --port 8765</pre><button class="btn" data-copy>${t.copyBtn}</button></div>
      </div>
      <div class="cmd-wrapper">
        <div class="cmd-label">${t.npmCfgLabel}</div>
        <div class="cmd-content"><pre>${npmJson}</pre><button class="btn" data-copy>${t.copyBtn}</button></div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-head"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>${t.apiTitle}</div>
    <p class="pane-desc">${t.apiDesc}</p>
    <div class="cmd-wrapper">
      <div class="cmd-label">${t.apiInstallLabel}</div>
      <div class="cmd-content"><pre>epsdk install ErisPulse-ApiMCP</pre><button class="btn" data-copy>${t.copyBtn}</button></div>
    </div>
    <div class="cmd-wrapper">
      <div class="cmd-label">${t.apiTokenLabel}</div>
      <div class="cmd-content"><pre>token = "your-long-random-string"</pre><button class="btn" data-copy>${t.copyBtn}</button></div>
    </div>
    <div class="cmd-wrapper">
      <div class="cmd-label">${t.apiCfgLabel}</div>
      <div class="cmd-content"><pre>${apiJson}</pre><button class="btn" data-copy>${t.copyBtn}</button></div>
    </div>
  </div>

  <div class="card">
    <div class="card-head"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h16M4 12h16M4 18h10"/></svg>${t.docsToolsTitle}</div>
    <div class="tools-grid">${docsToolsRows}</div>
  </div>

  <div class="card">
    <div class="card-head"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>${t.apiToolsTitle}</div>
    <div class="tools-grid">${apiToolsRows}</div>
    <p class="note">${t.apiToolsNote}</p>
  </div>

  <div class="card">
    <div class="card-head"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5.4L12 2.5 4 5.4V12c0 6 8 10 8 10z"/></svg>${t.securityTitle}</div>
    <div class="sec-chips">${secChips}</div>
  </div>

  <div class="card">
    <div class="card-head"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>${t.linksTitle}</div>
    <div class="links-grid">
      <a href="https://github.com/ErisPulse/ErisPulse" target="_blank" rel="noopener noreferrer" class="link-item">${t.links.repo}</a>
      <a href="https://www.npmjs.com/package/${NPM_PACKAGE}" target="_blank" rel="noopener noreferrer" class="link-item">${t.links.npm}</a>
      <a href="https://github.com/ErisPulse/ErisPulse-ApiMCP" target="_blank" rel="noopener noreferrer" class="link-item">${t.links.apimcp}</a>
      <a href="https://docs.erisdev.com" target="_blank" rel="noopener noreferrer" class="link-item">${t.links.docs}</a>
      <a href="https://www.erisdev.com" target="_blank" rel="noopener noreferrer" class="link-item">${t.links.site}</a>
    </div>
  </div>

  <div class="foot">
    ${t.foot}
    <div class="lang-switch">
      <button class="lang-btn ${isZh ? "" : "active"}" onclick="switchLang('en')">English</button>
      <button class="lang-btn ${isZh ? "active" : ""}" onclick="switchLang('zh')">中文</button>
    </div>
  </div>
</div>

<script>
(function () {
  var root = document.documentElement;
  var stored = null;
  try { stored = localStorage.getItem("ep_theme"); } catch (e) {}
  var theme = stored === "dark" || stored === "light" ? stored
    : (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  function applyTheme(v) {
    root.setAttribute("data-theme", v);
    theme = v;
    try { localStorage.setItem("ep_theme", v); } catch (e) {}
  }
  applyTheme(theme);
  window.toggleTheme = function () { applyTheme(theme === "dark" ? "light" : "dark"); };
  window.switchTab = function (i) {
    document.querySelectorAll(".tab-btn").forEach(function (b, idx) { b.classList.toggle("active", idx === i); });
    document.querySelectorAll(".tab-pane").forEach(function (p, idx) { p.classList.toggle("active", idx === i); });
  };
  var COPY_OK = ${JSON.stringify(t.copiedBtn)};
  var COPY_TXT = ${JSON.stringify(t.copyBtn)};
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var pre = btn.parentElement.querySelector("pre");
      if (!pre) return;
      var done = function () {
        btn.innerText = COPY_OK;
        btn.classList.add("ok");
        setTimeout(function () { btn.innerText = COPY_TXT; btn.classList.remove("ok"); }, 2000);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(pre.innerText).then(done, done);
      } else { done(); }
    });
  });
  window.switchLang = function (lang) {
    var url = new URL(window.location.href);
    url.searchParams.set("lang", lang);
    window.location.href = url.toString();
  };
})();
</script>
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
        return landingPage(pickRequestLang(request, url));
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
