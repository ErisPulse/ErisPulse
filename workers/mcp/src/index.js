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
// 7. 人类访问的着陆页（GET /）—— 拼贴艺术风（Collage Art）
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
    lead: "两组 MCP 服务：官方文档检索（npm 本地包 / 本站备用端点）与机器人运行时控制（ApiMCP 模块）。",
    chips: ["Streamable HTTP", "MCP 2025-03-26", "BM25 检索", "文档 5 语言"],
    docsTitle: "文档检索 MCP · erispulse-docs",
    docsDesc: "让 AI 编码助手直接检索、阅读 ErisPulse 官方文档。推荐 npm 本地包部署；远程端点是不能本地部署时的备用 API。工具集完全相同。",
    docsTabs: ["npm 本地包", "远程端点（备用）"],
    remoteDesc: "备用 API：零依赖，客户端直连 Cloudflare Worker，适合无法本地运行 Node 的环境；文档缓存 4 小时，限流 60 次/分钟/IP。",
    remoteLabel: "客户端 mcpServers 配置",
    npmDesc: "本地 Node 进程（≥ Node 18；stdio 默认，客户端以 command/args 拉起 / 可选 HTTP）。首次运行按框架版本拉取 zh-CN 文档缓存到 <code>~/.cache/erispulse-mcp</code>；设置 <code>ERISPULSE_DOCS_DIR</code> 可完全离线。",
    npmRunLabel: "运行（stdio）",
    npmHttpLabel: "HTTP 模式（自定义端口）",
    npmCfgLabel: "客户端 mcpServers 配置（stdio）",
    apiTitle: "机器人运行时 MCP · ApiMCP 模块",
    apiDesc: "把<strong>框架运行时能力</strong>开放给 AI 客户端：收发消息、跨模块 RPC、模块热重载、适配器状态、事件流订阅、拓扑观测，并内置框架文档检索（独立引擎，按框架版本缓存）——AI 可以直接操作你的机器人，而不只是查文档。REST 桥挂框架内置 HTTP server（默认 <code>0.0.0.0:8000</code>）；token 必须显式配置，未配置时除探活外全部返回 503。",
    apiInstallLabel: "安装（机器人环境）",
    apiTokenLabel: "配置 token（config.toml [ApiMCP] 节或环境变量）",
    apiCfgLabel: "Claude Desktop 配置",
    docsToolsTitle: "文档工具（3 个）",
    apiToolsTitle: "运行时工具（17 个）",
    apiToolsNote: "安全默认：限流 30 请求/分钟/IP · 未配置 token 除探活外 503 · 模块重载默认允许 · 适配器重载默认禁用 · module_call_whitelist / send_target_whitelist 白名单可配 · 输出键名级净化",
    securityTitle: "访问控制",
    secItems: ["token 显式配置，即完全控制权", "限流 30 请求/分钟/客户端 IP", "module_call_whitelist 收窄可调用面", "send_target_whitelist 收窄发送目标", "适配器重载默认禁用", "输出键名级净化（密钥/路径整键丢弃）"],
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
    lead: "Two MCP services: official docs retrieval (npm package / this endpoint as fallback) and bot runtime control (ApiMCP module).",
    chips: ["Streamable HTTP", "MCP 2025-03-26", "BM25 search", "Docs in 5 languages"],
    docsTitle: "Docs MCP · erispulse-docs",
    docsDesc: "Lets AI coding assistants search and read the official ErisPulse docs. The npm local package is recommended; the remote endpoint is a fallback API for environments that cannot deploy locally. Identical toolset.",
    docsTabs: ["npm local", "Remote (fallback)"],
    remoteDesc: "Fallback API: zero-dependency, clients hit the Cloudflare Worker directly — for environments that cannot run Node locally. Docs cached 4h, rate limit 60 req/min/IP.",
    remoteLabel: "Client mcpServers config",
    npmDesc: "Local Node process (Node ≥ 18; stdio by default — launched via command/args, HTTP optional). Docs for the current framework version are pulled on first run and cached under <code>~/.cache/erispulse-mcp</code>; set <code>ERISPULSE_DOCS_DIR</code> to stay fully offline.",
    npmRunLabel: "Run (stdio)",
    npmHttpLabel: "HTTP mode (custom port)",
    npmCfgLabel: "Client mcpServers config (stdio)",
    apiTitle: "Bot Runtime MCP · ApiMCP module",
    apiDesc: "Exposes the <strong>framework runtime</strong> to AI clients: send/receive messages, cross-module RPC, hot reload, adapter status, event streams, topology, plus built-in framework docs search (independent engine, cached per framework version) — AI can drive your bot, not just read docs. The REST bridge mounts on the framework HTTP server (default <code>0.0.0.0:8000</code>); a token must be configured explicitly — without one every endpoint but health returns 503.",
    apiInstallLabel: "Install (bot env)",
    apiTokenLabel: "Configure token (config.toml [ApiMCP] or env var)",
    apiCfgLabel: "Claude Desktop config",
    docsToolsTitle: "Docs tools (3)",
    apiToolsTitle: "Runtime tools (17)",
    apiToolsNote: "Secure defaults: 30 req/min/IP rate limit · 503 on all endpoints but health without a token · module reload allowed · adapter reload disabled by default · module_call_whitelist / send_target_whitelist supported · key-level output sanitization",
    securityTitle: "Access control",
    secItems: ["Explicit token = full control", "Rate limit 30 req/min per client IP", "module_call_whitelist narrows the callable surface", "send_target_whitelist narrows send targets", "Adapter reload disabled by default", "Key-level output sanitization"],
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
  ["call_module(name, method, args?, kwargs?, rpc_timeout?)", "cross-module RPC (whitelist-guarded)"],
  ["reload_module(name)", "hot reload a module (allowed by default)"],
  ["list_adapters", "list platform adapters & bots"],
  ["get_adapter_status(platform)", "per-platform runtime status"],
  ["reload_adapter(platform)", "adapter reload (disabled by default)"],
  ["send_message(platform, target_type, target_id, method, content, account?)", "send Text/Image/Voice/Video/File; account picks the bot"],
  ["recent_messages(platform?, session?, limit=50)", "recent messages via transcript"],
  ["subscribe_events(types)", "subscribe message/notice/request/meta/*"],
  ["unsubscribe(subscription_id)", "cancel a subscription"],
  ["poll_events(since_ts, since_seq, limit?, subscription_id?)", "incremental polling over the ring buffer"],
  ["search_erispulse_docs(query, top_k=5)", "search framework docs (built-in engine)"],
  ["read_erispulse_doc(file, limit=8000)", "read one framework document"],
  ["refresh_erispulse_docs()", "sync docs cache to the current framework version"],
  ["get_topology", "runtime topology (sanitized)"],
  ["sdk_health", "SDK version / uptime / module & adapter summary"],
];

// —— 官方 Logo（词标 SVG，剥离动画样式后的静态版，经 /logo.svg 提供） ——

const LOGO_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="190 740 1720 600" role="img" aria-labelledby="title desc"><title id="title">ErisPulse</title><desc id="desc">ErisPulse logo traced from the supplied reference image as editable SVG paths.</desc><defs><!--
      ==============================================================
      ErisPulse Logo — Editable SVG
      ==============================================================

      这版以提供的「无白色描边」Logo 图片作为轮廓参考。

      设计原则：

      1. 不使用字体
      2. 不使用白色外描边
      3. 每个字母都是独立 Group
      4. i 的点单独存在
      5. P 的下方弧线属于 P
      6. 高光独立
      7. 纹理独立
      8. 所有主体轮廓都是 SVG Path

      可以直接使用 CSS / JavaScript / SMIL
      对每一个字母进行动画。

      可用动画 ID：

        #letter-E
        #letter-r
        #letter-i-dot
        #letter-i
        #letter-s
        #letter-P
        #letter-u
        #letter-l
        #letter-s2
        #letter-e

      ==============================================================
    --><!-- ============================================================
         蓝色部分
         E r i s
         ============================================================ --><linearGradient
      id="eris-blue"
      gradientUnits="userSpaceOnUse"
      x1="0"
      y1="770"
      x2="0"
      y2="1165"
    ><stop
        offset="0"
        stop-color="#80C8F8"
      /><stop
        offset=".50"
        stop-color="#9CC8F2"
      /><stop
        offset="1"
        stop-color="#B99BEF"
      /></linearGradient><!-- ============================================================
         粉色部分
         Pulse
         ============================================================ --><linearGradient
      id="pulse-pink"
      gradientUnits="userSpaceOnUse"
      x1="0"
      y1="790"
      x2="0"
      y2="1300"
    ><stop
        offset="0"
        stop-color="#F08CBD"
      /><stop
        offset=".48"
        stop-color="#F19FD0"
      /><stop
        offset="1"
        stop-color="#C99BEF"
      /></linearGradient><!-- ============================================================
         Logo 内部的轻微颗粒纹理

         这不是必须的。

         如果以后需要纯色版本：

           .texture {
             display: none;
           }

         即可。
         ============================================================ --><pattern
      id="speckles"
      width="12"
      height="12"
      patternUnits="userSpaceOnUse"
    ><circle
        cx="2"
        cy="3"
        r=".55"
        fill="#7569A7"
        opacity=".10"
      /><circle
        cx="8"
        cy="9"
        r=".45"
        fill="#7569A7"
        opacity=".07"
      /></pattern><!-- ============================================================
         公共 CSS
         ============================================================ --></defs><!-- ==============================================================
       E
       ============================================================== --><g
    id="letter-E"
    class="letter"
    data-letter="E"
  ><!--
      E 主体轮廓
    --><path
      id="shape-E"
      fill="url(#eris-blue)"
      fill-rule="evenodd"
      d="
        M 483.00 771.00
        L 473.00 768.00
        L 449.00 768.00
        L 361.00 775.00
        L 305.00 777.00
        L 289.00 781.00
        L 281.00 786.00
        L 273.00 795.00
        L 266.00 813.00
        L 257.00 876.00
        L 242.00 956.00
        L 233.00 1019.00
        L 217.00 1110.00
        L 217.00 1131.00
        L 220.00 1141.00
        L 225.00 1150.00
        L 237.00 1161.00
        L 261.00 1170.00
        L 284.00 1170.00
        L 291.00 1168.00
        L 425.00 1159.00
        L 443.00 1154.00
        L 450.00 1148.00
        L 458.00 1136.00
        L 464.00 1114.00
        L 464.00 1093.00
        L 460.00 1084.00
        L 449.00 1076.00
        L 435.00 1074.00
        L 356.00 1080.00
        L 315.00 1081.00
        L 309.00 1074.00
        L 309.00 1064.00
        L 316.00 1014.00
        L 320.00 1004.00
        L 374.00 999.00
        L 406.00 998.00
        L 415.00 996.00
        L 433.00 996.00
        L 442.00 994.00
        L 450.00 988.00
        L 454.00 982.00
        L 460.00 963.00
        L 461.00 938.00
        L 458.00 929.00
        L 452.00 923.00
        L 443.00 920.00
        L 429.00 920.00
        L 337.00 928.00
        L 333.00 924.00
        L 334.00 908.00
        L 338.00 892.00
        L 342.00 861.00
        L 344.00 857.00
        L 349.00 854.00
        L 376.00 851.00
        L 416.00 850.00
        L 425.00 848.00
        L 466.00 847.00
        L 480.00 842.00
        L 488.00 834.00
        L 495.00 811.00
        L 494.00 785.00
        L 491.00 778.00
        Z
      "
    /><!-- E 纹理 --><use
      href="#shape-E"
      class="texture"
      fill="url(#speckles)"
    /><!-- E 高光 --><path
      class="highlight"
      d="
        M 286.00 802.00
        L 293.00 799.00
        L 300.00 801.00
        L 308.00 807.00
        L 312.00 813.00
        L 309.00 818.00
        L 303.00 821.00
        L 296.00 825.00
        L 289.00 826.00
        L 285.00 821.00
        L 284.00 813.00
        Z
      "
    /></g><!-- ==============================================================
       r
       ============================================================== --><g
    id="letter-r"
    class="letter"
    data-letter="r"
  ><path
      id="shape-r"
      fill="url(#eris-blue)"
      fill-rule="evenodd"
      d="
        M 660.00 915.00
        L 642.00 908.00
        L 627.00 909.00
        L 610.00 915.00
        L 589.00 931.00
        L 578.00 947.00
        L 575.00 942.00
        L 574.00 932.00
        L 570.00 921.00
        L 562.00 915.00
        L 556.00 913.00
        L 543.00 912.00
        L 530.00 915.00
        L 514.00 927.00
        L 509.00 937.00
        L 507.00 946.00
        L 486.00 1123.00
        L 486.00 1133.00
        L 490.00 1146.00
        L 499.00 1155.00
        L 511.00 1159.00
        L 532.00 1158.00
        L 543.00 1154.00
        L 552.00 1146.00
        L 558.00 1131.00
        L 568.00 1045.00
        L 574.00 1021.00
        L 586.00 1001.00
        L 597.00 991.00
        L 610.00 984.00
        L 618.00 982.00
        L 627.00 983.00
        L 644.00 989.00
        L 650.00 988.00
        L 658.00 982.00
        L 666.00 965.00
        L 670.00 948.00
        L 670.00 934.00
        L 666.00 921.00
        Z
      "
    /><use
      href="#shape-r"
      class="texture"
      fill="url(#speckles)"
    /><path
      class="highlight"
      d="
        M 524.00 935.00
        L 530.00 932.00
        L 537.00 933.00
        L 541.00 937.00
        L 539.00 943.00
        L 533.00 948.00
        L 527.00 950.00
        L 523.00 946.00
        L 522.00 940.00
        Z
      "
    /></g><!-- ==============================================================
       i 点
       ============================================================== --><g
    id="letter-i-dot"
    class="letter"
    data-letter="i-dot"
  ><path
      id="shape-i-dot"
      fill="url(#eris-blue)"
      d="
        M 765.00 803.00
        L 750.00 799.00
        L 731.00 801.00
        L 716.00 809.00
        L 706.00 819.00
        L 699.00 835.00
        L 697.00 851.00
        L 698.00 860.00
        L 703.00 874.00
        L 714.00 886.00
        L 728.00 892.00
        L 745.00 892.00
        L 762.00 886.00
        L 777.00 872.00
        L 784.00 856.00
        L 786.00 837.00
        L 778.00 815.00
        Z
      "
    /><use
      href="#shape-i-dot"
      class="texture"
      fill="url(#speckles)"
    /><path
      class="highlight"
      d="
        M 717.00 824.00
        L 722.00 819.00
        L 728.00 818.00
        L 734.00 821.00
        L 734.00 826.00
        L 729.00 831.00
        L 723.00 835.00
        L 718.00 833.00
        L 716.00 829.00
        Z
      "
    /></g><!-- ==============================================================
       i
       ============================================================== --><g
    id="letter-i"
    class="letter"
    data-letter="i"
  ><path
      id="shape-i"
      fill="url(#eris-blue)"
      fill-rule="evenodd"
      d="
        M 741.00 915.00
        L 723.00 916.00
        L 707.00 923.00
        L 699.00 932.00
        L 695.00 945.00
        L 675.00 1103.00
        L 673.00 1138.00
        L 675.00 1144.00
        L 683.00 1154.00
        L 700.00 1160.00
        L 715.00 1160.00
        L 731.00 1155.00
        L 739.00 1148.00
        L 746.00 1128.00
        L 750.00 1099.00
        L 752.00 1064.00
        L 766.00 956.00
        L 766.00 936.00
        L 760.00 923.00
        L 749.00 917.00
        Z
      "
    /><use
      href="#shape-i"
      class="texture"
      fill="url(#speckles)"
    /><path
      class="highlight"
      d="
        M 711.00 937.00
        L 716.00 933.00
        L 722.00 933.00
        L 727.00 936.00
        L 726.00 941.00
        L 720.00 947.00
        L 714.00 950.00
        L 710.00 947.00
        L 709.00 942.00
        Z
      "
    /></g><!-- ==============================================================
       s
       ============================================================== --><g
    id="letter-s"
    class="letter"
    data-letter="s"
  ><path
      id="shape-s"
      fill="url(#eris-blue)"
      fill-rule="evenodd"
      d="
        M 904.00 907.00
        L 886.00 904.00
        L 872.00 904.00
        L 854.00 907.00
        L 831.00 917.00
        L 813.00 931.00
        L 803.00 944.00
        L 795.00 959.00
        L 790.00 979.00
        L 790.00 996.00
        L 795.00 1014.00
        L 802.00 1026.00
        L 819.00 1042.00
        L 837.00 1050.00
        L 847.00 1052.00
        L 865.00 1062.00
        L 875.00 1075.00
        L 875.00 1082.00
        L 870.00 1091.00
        L 856.00 1099.00
        L 845.00 1099.00
        L 830.00 1091.00
        L 820.00 1076.00
        L 810.00 1068.00
        L 796.00 1068.00
        L 787.00 1073.00
        L 779.00 1082.00
        L 774.00 1092.00
        L 771.00 1102.00
        L 771.00 1112.00
        L 773.00 1120.00
        L 779.00 1131.00
        L 786.00 1138.00
        L 800.00 1146.00
        L 827.00 1155.00
        L 867.00 1156.00
        L 878.00 1154.00
        L 900.00 1145.00
        L 915.00 1134.00
        L 926.00 1122.00
        L 936.00 1104.00
        L 942.00 1086.00
        L 943.00 1062.00
        L 938.00 1044.00
        L 932.00 1034.00
        L 922.00 1023.00
        L 910.00 1015.00
        L 861.00 993.00
        L 856.00 988.00
        L 853.00 981.00
        L 856.00 970.00
        L 862.00 964.00
        L 875.00 959.00
        L 883.00 960.00
        L 894.00 965.00
        L 908.00 980.00
        L 913.00 982.00
        L 926.00 981.00
        L 932.00 978.00
        L 939.00 971.00
        L 944.00 962.00
        L 947.00 950.00
        L 944.00 935.00
        L 928.00 918.00
        Z
      "
    /><use
      href="#shape-s"
      class="texture"
      fill="url(#speckles)"
    /></g><!-- ==============================================================
       P
       ============================================================== --><g
    id="letter-P"
    class="letter"
    data-letter="P"
  ><!--
      P 的完整轮廓。

      注意：

      下方的大弧线已经包含在同一个 shape-P 中。

      因此：

        #letter-P

      才是完整的 P 动画对象。
    --><path
      id="shape-P"
      fill="url(#pulse-pink)"
      fill-rule="evenodd"
      d="
        M 1162.00 825.00
        L 1146.00 817.00
        L 1121.00 810.00
        L 1079.00 808.00
        L 1041.00 813.00
        L 1023.00 818.00
        L 1009.00 827.00
        L 1001.00 839.00
        L 996.00 861.00
        L 987.00 927.00
        L 981.00 963.00
        L 976.00 1005.00
        L 971.00 1043.00
        L 966.00 1085.00
        L 962.00 1111.00
        L 956.00 1154.00
        L 947.00 1180.00
        L 939.00 1192.00
        L 927.00 1204.00
        L 911.00 1212.00
        L 893.00 1216.00
        L 870.00 1214.00
        L 843.00 1204.00
        L 829.00 1195.00
        L 812.00 1175.00
        L 801.00 1174.00
        L 767.00 1203.00
        L 750.00 1212.00
        L 733.00 1217.00
        L 712.00 1217.00
        L 696.00 1212.00
        L 687.00 1206.00
        L 676.00 1195.00
        L 666.00 1181.00
        L 655.00 1173.00
        L 640.00 1168.00
        L 625.00 1169.00
        L 614.00 1173.00
        L 604.00 1180.00
        L 595.00 1189.00
        L 587.00 1205.00
        L 586.00 1233.00
        L 589.00 1245.00
        L 595.00 1258.00
        L 602.00 1266.00
        L 619.00 1282.00
        L 640.00 1292.00
        L 665.00 1296.00
        L 683.00 1296.00
        L 704.00 1293.00
        L 730.00 1284.00
        L 748.00 1275.00
        L 768.00 1262.00
        L 796.00 1236.00
        L 802.00 1234.00
        L 821.00 1254.00
        L 838.00 1266.00
        L 859.00 1276.00
        L 881.00 1282.00
        L 923.00 1282.00
        L 944.00 1276.00
        L 972.00 1260.00
        L 1001.00 1230.00
        L 1016.00 1205.00
        L 1025.00 1184.00
        L 1034.00 1148.00
        L 1042.00 1082.00
        L 1048.00 1079.00
        L 1076.00 1079.00
        L 1102.00 1075.00
        L 1122.00 1068.00
        L 1140.00 1059.00
        L 1160.00 1044.00
        L 1170.00 1034.00
        L 1188.00 1008.00
        L 1204.00 969.00
        L 1209.00 947.00
        L 1211.00 927.00
        L 1210.00 899.00
        L 1204.00 875.00
        L 1190.00 849.00
        L 1178.00 835.00
        Z

        M 1111.00 887.00
        L 1123.00 895.00
        L 1130.00 904.00
        L 1135.00 915.00
        L 1137.00 940.00
        L 1131.00 962.00
        L 1119.00 982.00
        L 1108.00 993.00
        L 1097.00 1000.00
        L 1078.00 1007.00
        L 1065.00 1009.00
        L 1049.00 1008.00
        L 1058.00 938.00
        L 1062.00 892.00
        L 1070.00 885.00
        L 1083.00 883.00
        L 1095.00 883.00
        Z
      "
    /><use
      href="#shape-P"
      class="texture"
      fill="url(#speckles)"
    /><!-- P 主体高光 --><path
      class="highlight"
      d="
        M 1014.00 841.00
        L 1020.00 837.00
        L 1027.00 838.00
        L 1033.00 842.00
        L 1033.00 847.00
        L 1028.00 852.00
        L 1022.00 857.00
        L 1016.00 857.00
        L 1013.00 852.00
        L 1012.00 846.00
        Z
      "
    /><!-- P 下方弧线高光 --><path
      class="highlight"
      d="
        M 606.00 1192.00
        L 612.00 1189.00
        L 618.00 1190.00
        L 624.00 1194.00
        L 625.00 1199.00
        L 620.00 1204.00
        L 614.00 1210.00
        L 608.00 1210.00
        L 605.00 1206.00
        L 604.00 1200.00
        Z
      "
    /></g><!-- ==============================================================
       u
       ============================================================== --><g
    id="letter-u"
    class="letter"
    data-letter="u"
  ><path
      id="shape-u"
      fill="url(#pulse-pink)"
      fill-rule="evenodd"
      d="
        M 1395.00 924.00
        L 1383.00 920.00
        L 1371.00 920.00
        L 1356.00 924.00
        L 1345.00 933.00
        L 1341.00 940.00
        L 1327.00 1057.00
        L 1321.00 1070.00
        L 1315.00 1078.00
        L 1305.00 1086.00
        L 1294.00 1090.00
        L 1284.00 1087.00
        L 1278.00 1081.00
        L 1274.00 1068.00
        L 1276.00 1042.00
        L 1290.00 949.00
        L 1288.00 941.00
        L 1280.00 929.00
        L 1266.00 923.00
        L 1245.00 926.00
        L 1235.00 931.00
        L 1229.00 937.00
        L 1224.00 948.00
        L 1221.00 965.00
        L 1219.00 993.00
        L 1212.00 1037.00
        L 1209.00 1082.00
        L 1213.00 1110.00
        L 1223.00 1131.00
        L 1236.00 1144.00
        L 1258.00 1154.00
        L 1282.00 1154.00
        L 1298.00 1148.00
        L 1314.00 1138.00
        L 1325.00 1125.00
        L 1332.00 1142.00
        L 1337.00 1147.00
        L 1348.00 1151.00
        L 1359.00 1151.00
        L 1373.00 1146.00
        L 1380.00 1138.00
        L 1384.00 1126.00
        L 1392.00 1055.00
        L 1396.00 1034.00
        L 1400.00 985.00
        L 1404.00 962.00
        L 1404.00 937.00
        L 1402.00 932.00
        Z
      "
    /><use
      href="#shape-u"
      class="texture"
      fill="url(#speckles)"
    /><path
      class="highlight"
      d="
        M 1240.00 947.00
        L 1245.00 943.00
        L 1251.00 943.00
        L 1256.00 947.00
        L 1255.00 952.00
        L 1250.00 957.00
        L 1244.00 961.00
        L 1239.00 959.00
        L 1237.00 954.00
        Z
      "
    /><path
      class="highlight"
      d="
        M 1355.00 944.00
        L 1360.00 940.00
        L 1366.00 940.00
        L 1371.00 944.00
        L 1370.00 949.00
        L 1365.00 954.00
        L 1359.00 958.00
        L 1354.00 956.00
        L 1352.00 951.00
        Z
      "
    /></g><!-- ==============================================================
       l
       ============================================================== --><g
    id="letter-l"
    class="letter"
    data-letter="l"
  ><path
      id="shape-l"
      fill="url(#pulse-pink)"
      fill-rule="evenodd"
      d="
        M 1494.00 791.00
        L 1479.00 791.00
        L 1467.00 795.00
        L 1456.00 805.00
        L 1451.00 816.00
        L 1445.00 853.00
        L 1443.00 882.00
        L 1437.00 914.00
        L 1433.00 962.00
        L 1421.00 1054.00
        L 1418.00 1093.00
        L 1421.00 1124.00
        L 1428.00 1134.00
        L 1435.00 1140.00
        L 1447.00 1146.00
        L 1456.00 1148.00
        L 1474.00 1148.00
        L 1493.00 1140.00
        L 1501.00 1132.00
        L 1505.00 1124.00
        L 1509.00 1106.00
        L 1508.00 1092.00
        L 1504.00 1085.00
        L 1490.00 1081.00
        L 1484.00 1075.00
        L 1495.00 981.00
        L 1500.00 954.00
        L 1516.00 829.00
        L 1516.00 811.00
        L 1512.00 803.00
        L 1506.00 796.00
        Z
      "
    /><use
      href="#shape-l"
      class="texture"
      fill="url(#speckles)"
    /><path
      class="highlight"
      d="
        M 1466.00 817.00
        L 1471.00 812.00
        L 1477.00 812.00
        L 1481.00 816.00
        L 1480.00 821.00
        L 1475.00 826.00
        L 1469.00 831.00
        L 1465.00 829.00
        L 1464.00 824.00
        Z
      "
    /></g><!-- ==============================================================
       第二个 s
       ============================================================== --><g
    id="letter-s2"
    class="letter"
    data-letter="s2"
  ><path
      id="shape-s2"
      fill="url(#pulse-pink)"
      fill-rule="evenodd"
      d="
        M 1645.00 901.00
        L 1628.00 898.00
        L 1605.00 899.00
        L 1579.00 907.00
        L 1562.00 917.00
        L 1549.00 929.00
        L 1542.00 939.00
        L 1534.00 956.00
        L 1531.00 970.00
        L 1531.00 994.00
        L 1533.00 1004.00
        L 1541.00 1020.00
        L 1555.00 1034.00
        L 1569.00 1042.00
        L 1603.00 1052.00
        L 1614.00 1061.00
        L 1617.00 1067.00
        L 1617.00 1073.00
        L 1613.00 1082.00
        L 1600.00 1091.00
        L 1592.00 1092.00
        L 1583.00 1091.00
        L 1574.00 1087.00
        L 1566.00 1081.00
        L 1556.00 1068.00
        L 1550.00 1066.00
        L 1536.00 1068.00
        L 1525.00 1077.00
        L 1519.00 1093.00
        L 1519.00 1101.00
        L 1523.00 1114.00
        L 1535.00 1128.00
        L 1555.00 1140.00
        L 1581.00 1147.00
        L 1604.00 1147.00
        L 1630.00 1140.00
        L 1646.00 1131.00
        L 1660.00 1118.00
        L 1667.00 1109.00
        L 1676.00 1090.00
        L 1680.00 1069.00
        L 1676.00 1043.00
        L 1668.00 1027.00
        L 1662.00 1019.00
        L 1652.00 1011.00
        L 1635.00 1002.00
        L 1604.00 990.00
        L 1594.00 981.00
        L 1592.00 977.00
        L 1592.00 969.00
        L 1596.00 963.00
        L 1605.00 956.00
        L 1610.00 955.00
        L 1627.00 956.00
        L 1645.00 972.00
        L 1651.00 974.00
        L 1661.00 974.00
        L 1668.00 971.00
        L 1677.00 962.00
        L 1683.00 946.00
        L 1683.00 933.00
        L 1680.00 925.00
        L 1666.00 911.00
        Z
      "
    /><use
      href="#shape-s2"
      class="texture"
      fill="url(#speckles)"
    /><path
      class="highlight"
      d="
        M 1557.00 934.00
        L 1561.00 930.00
        L 1566.00 930.00
        L 1570.00 934.00
        L 1569.00 938.00
        L 1565.00 942.00
        L 1560.00 945.00
        L 1556.00 943.00
        L 1555.00 939.00
        Z
      "
    /></g><!-- ==============================================================
       e
       ============================================================== --><g
    id="letter-e"
    class="letter"
    data-letter="e"
  ><path
      id="shape-e"
      fill="url(#pulse-pink)"
      fill-rule="evenodd"
      d="
        M 1844.00 899.00
        L 1822.00 895.00
        L 1806.00 896.00
        L 1786.00 901.00
        L 1768.00 909.00
        L 1743.00 926.00
        L 1726.00 943.00
        L 1717.00 957.00
        L 1707.00 979.00
        L 1701.00 999.00
        L 1697.00 1029.00
        L 1697.00 1049.00
        L 1702.00 1074.00
        L 1708.00 1090.00
        L 1718.00 1107.00
        L 1734.00 1122.00
        L 1755.00 1133.00
        L 1778.00 1139.00
        L 1808.00 1139.00
        L 1837.00 1131.00
        L 1853.00 1122.00
        L 1869.00 1108.00
        L 1875.00 1100.00
        L 1882.00 1085.00
        L 1882.00 1076.00
        L 1878.00 1067.00
        L 1873.00 1061.00
        L 1863.00 1056.00
        L 1852.00 1055.00
        L 1845.00 1057.00
        L 1827.00 1075.00
        L 1814.00 1083.00
        L 1792.00 1085.00
        L 1776.00 1077.00
        L 1768.00 1069.00
        L 1760.00 1053.00
        L 1760.00 1045.00
        L 1764.00 1042.00
        L 1781.00 1042.00
        L 1826.00 1035.00
        L 1846.00 1028.00
        L 1862.00 1018.00
        L 1876.00 1003.00
        L 1884.00 985.00
        L 1887.00 972.00
        L 1887.00 955.00
        L 1884.00 942.00
        L 1876.00 924.00
        L 1862.00 909.00
        Z

        M 1827.00 957.00
        L 1829.00 961.00
        L 1830.00 973.00
        L 1829.00 979.00
        L 1823.00 986.00
        L 1797.00 995.00
        L 1764.00 1000.00
        L 1760.00 997.00
        L 1766.00 978.00
        L 1774.00 967.00
        L 1786.00 956.00
        L 1801.00 949.00
        L 1815.00 948.00
        Z
      "
    /><use
      href="#shape-e"
      class="texture"
      fill="url(#speckles)"
    /></g><!-- ==============================================================
       Animation Notes
       ==============================================================

       每个字母都可以单独控制。

       例如：

         #letter-P {
           animation: bounce .8s ease-in-out;
         }

         @keyframes bounce {
           50% {
             transform:
               translateY(-10px)
               rotate(-1deg);
           }
         }


       逐字出现：

         .letter {
           opacity: 0;
           animation:
             logo-in .5s ease forwards;
         }

         @keyframes logo-in {
           from {
             opacity: 0;
             transform: translateY(15px);
           }

           to {
             opacity: 1;
             transform: translateY(0);
           }
         }


       P 的下方弧线属于 #letter-P，
       所以 P 做旋转、弹跳、缩放时会保持整体关系。


       高光也是独立元素：

         .highlight {
           animation: shine 2s infinite;
         }


       纹理也是独立元素：

         .texture {
           animation: grain 1.5s infinite;
         }

       ==============================================================
  --></svg>`;

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
  const secStickers = (t.secItems || [])
    .map((s) => '<span class="sticker">' + s + "</span>")
    .join("");
  const chips = (t.chips || [])
    .map((c) => '<span class="tag">' + c + "</span>")
    .join("");

  const html = `<!DOCTYPE html>
<html lang="${t.htmlLang}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>${t.title}</title>
<link rel="icon" type="image/svg+xml" href="/logo.svg" />
<style>
  :root {
    --ink: #2d2d2d;
    --paper: #f5f0e8;
    --card: #fbf7ef;
    --white: #ffffff;
    --red: #e74c3c;
    --blue: #3498db;
    --orange: #f39c12;
    --violet: #9b59b6;
    --sh-sm: 3px 3px 0 rgba(45,45,45,.22);
    --dash: 2px dashed rgba(45,45,45,.4);
    --serif: Georgia, "Songti SC", "STSong", "SimSun", serif;
    --sans: system-ui, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    --mono: ui-monospace, "Cascadia Mono", "Courier New", monospace;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { overflow-x: clip; }
  body { font-family: var(--sans); font-size: 15px; line-height: 1.6; color: var(--ink); background: var(--paper); min-height: 100vh; -webkit-font-smoothing: antialiased; }
  a { color: inherit; }
  code { font-family: var(--mono); }
  :focus-visible { outline: 3px solid var(--blue); outline-offset: 2px; }

  /* —— 旋转与纸片阴影：旋转一律用类，避免与 hover 冲突 —— */
  .tilt { transform: rotate(var(--rot, 0deg)); transition: transform .2s ease, filter .2s ease; }
  .tilt:hover { transform: rotate(0deg) translateY(-2px); }
  .r-1 { --rot: -1.6deg; } .r-2 { --rot: -.7deg; } .r-3 { --rot: 1.1deg; }
  .r-4 { --rot: .8deg; } .r-5 { --rot: 2deg; } .r-6 { --rot: -2.1deg; }
  .lift { filter: drop-shadow(6px 6px 0 rgba(45,45,45,.28)); }
  .lift:hover { filter: drop-shadow(8px 8px 0 rgba(45,45,45,.28)); }
  .torn { clip-path: polygon(0 2%,8% 0,20% 3%,35% 0,50% 2%,65% 0,80% 3%,92% 0,100% 2%,100% 98%,90% 100%,75% 97%,60% 100%,45% 98%,30% 100%,15% 97%,0 100%); }

  /* —— 剪下来的标签条 —— */
  .tag { display: inline-block; height: 28px; line-height: 28px; padding: 0 14px; font-family: var(--mono); font-size: 13px; letter-spacing: .08em; text-transform: uppercase; background: var(--blue); color: #fff; clip-path: polygon(8px 0,calc(100% - 8px) 0,100% 50%,calc(100% - 8px) 100%,8px 100%,0 50%); }
  .badges { display: flex; gap: 12px; margin-top: 22px; flex-wrap: wrap; }
  .badges .tag:nth-child(4n+2) { background: var(--red); }
  .badges .tag:nth-child(4n+3) { background: var(--orange); color: var(--ink); }
  .badges .tag:nth-child(4n) { background: var(--violet); }
  .badges .tag:nth-child(odd) { transform: rotate(-1.6deg); }
  .badges .tag:nth-child(even) { transform: rotate(1.4deg); }

  /* —— 胶带 —— */
  .tape { position: absolute; width: 130px; height: 22px; pointer-events: none; clip-path: polygon(3% 0,97% 0,100% 28%,96% 52%,100% 78%,97% 100%,3% 100%,0 72%,4% 46%,0 24%); }
  .tape-red { background: rgba(231,76,49,.5); }
  .tape-blue { background: rgba(52,152,219,.45); }
  .tape-white { background: rgba(255,255,255,.6); }
  .tape-orange { background: rgba(243,156,18,.5); }

  /* —— 顶栏 —— */
  .topbar { width: min(1120px, calc(100% - 32px)); margin: 24px auto 0; display: flex; align-items: center; gap: 14px; }
  .brand-logo { height: 30px; width: auto; display: block; }
  .top-tag { background: var(--orange); color: var(--ink); transform: rotate(-1.5deg); }
  .sp { flex: 1; }
  .round { width: 36px; height: 36px; border: 2px solid var(--ink); border-radius: 2px; background: var(--white); display: flex; align-items: center; justify-content: center; color: var(--ink); cursor: pointer; transition: transform .15s ease, box-shadow .15s ease; }
  .round:hover { transform: translate(-2px,-2px); box-shadow: var(--sh-sm); }
  .round svg { width: 17px; height: 17px; }

  main { width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 34px 0 70px; }

  /* —— 头部：混合字体堆叠 —— */
  .hero { margin-bottom: 46px; }
  .hero > .tag { margin-bottom: 20px; transform: rotate(-1.2deg); }
  .hero-title { position: relative; font-family: var(--serif); font-weight: 900; font-size: clamp(40px, 6vw, 62px); line-height: 1.05; letter-spacing: -.02em; max-width: 840px; }
  .hero-title .tape { top: -12px; right: 4%; width: 150px; transform: rotate(5deg); }
  .hero-sub { margin-top: 16px; font-size: 18px; line-height: 1.55; max-width: 660px; color: rgba(45,45,45,.85); transform: rotate(-.5deg); }
  .hero-sub strong { color: var(--ink); }

  /* —— 纸片网格 —— */
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 40px 32px; align-items: start; }
  .card { position: relative; }
  .card.full { grid-column: 1 / -1; }
  .torn-body { background: var(--card); padding: 26px 26px 24px; }
  .card-head { display: flex; flex-direction: column; gap: 10px; margin-bottom: 18px; }
  .num { display: inline-block; padding: 3px 12px; font-family: var(--mono); font-size: 11px; letter-spacing: .14em; color: #fff; background: var(--ink); clip-path: polygon(6px 0,calc(100% - 6px) 0,100% 50%,calc(100% - 6px) 100%,6px 100%,0 50%); align-self: flex-start; }
  .num.alt { background: var(--red); }
  .card-head h2 { font-family: var(--serif); font-weight: 700; font-size: 27px; line-height: 1.15; }
  .desc { font-size: 14px; color: rgba(45,45,45,.8); margin-bottom: 16px; }
  .desc code { background: var(--white); border: 1px solid rgba(45,45,45,.2); padding: 1px 6px; font-size: 12px; }
  .desc strong { color: var(--ink); }

  /* —— 切换标签 —— */
  .tabs { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }
  .tab-btn { height: 30px; padding: 0 16px; border: none; cursor: pointer; font-family: var(--mono); font-size: 13px; letter-spacing: .06em; background: var(--white); color: var(--ink); box-shadow: inset 0 0 0 2px rgba(45,45,45,.35); clip-path: polygon(9px 0,calc(100% - 9px) 0,100% 50%,calc(100% - 9px) 100%,9px 100%,0 50%); }
  .tab-btn:nth-child(odd) { transform: rotate(-1.4deg); }
  .tab-btn:nth-child(even) { transform: rotate(1.2deg); }
  .tab-btn.active { background: var(--red); color: #fff; box-shadow: none; }
  .tab-pane { display: none; }
  .tab-pane.active { display: block; }

  /* —— 剪切痕迹代码块 —— */
  .cmd-wrapper { border: var(--dash); border-radius: 2px; background: var(--white); margin-bottom: 14px; }
  .cmd-label { display: flex; align-items: center; gap: 8px; padding: 8px 14px; font-family: var(--mono); font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: rgba(45,45,45,.7); border-bottom: 2px dashed rgba(45,45,45,.25); }
  .cmd-label svg { width: 14px; height: 14px; flex: none; }
  .cmd-content { padding: 12px 14px; display: flex; align-items: flex-start; gap: 12px; }
  .cmd-content pre { flex: 1; min-width: 0; font-family: var(--mono); font-size: 13px; line-height: 1.5; margin: 0; white-space: pre-wrap; word-break: break-all; }
  .btn { font-family: var(--mono); font-size: 12px; letter-spacing: .05em; background: var(--ink); color: #fff; border: none; padding: 7px 14px; border-radius: 2px; cursor: pointer; white-space: nowrap; transform: rotate(-1deg); transition: transform .15s ease, box-shadow .15s ease, background-color .15s ease; }
  .btn:hover { transform: translate(-2px,-2px) rotate(0); box-shadow: var(--sh-sm); }
  .btn.ok { background: var(--blue); }

  /* —— 工具清单 —— */
  .tools-grid { column-count: 2; column-gap: 36px; }
  .tools-grid.one { column-count: 1; }
  .tool-row { break-inside: avoid; display: flex; flex-direction: column; gap: 4px; padding: 10px 2px; border-bottom: 2px dashed rgba(45,45,45,.18); }
  .tool-row code { align-self: flex-start; background: var(--white); border: 1px solid rgba(45,45,45,.25); padding: 2px 8px; font-size: 12.5px; }
  .tool-row span { font-size: 13px; color: rgba(45,45,45,.75); }
  .note { margin-top: 14px; font-family: var(--mono); font-size: 12px; color: rgba(45,45,45,.65); border-top: var(--dash); padding-top: 12px; }

  /* —— 贴纸（安全） —— */
  .stickers { display: flex; flex-wrap: wrap; gap: 12px; }
  .sticker { display: inline-block; padding: 7px 16px; border-radius: 999px; font-family: var(--mono); font-size: 12px; font-weight: 700; color: #fff; background: var(--red); transform: rotate(-1.6deg); transition: transform .15s ease; }
  .sticker:nth-child(4n+2) { background: var(--blue); transform: rotate(1.4deg); }
  .sticker:nth-child(4n+3) { background: var(--orange); color: var(--ink); transform: rotate(-.8deg); }
  .sticker:nth-child(4n) { background: var(--violet); transform: rotate(2deg); }
  .sticker:hover { transform: rotate(0); }

  /* —— 链接纸条 —— */
  .links-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px; }
  .link-item { display: flex; align-items: center; justify-content: center; padding: 13px 10px; background: var(--white); border: var(--dash); border-radius: 2px; text-decoration: none; font-family: var(--mono); font-size: 13px; letter-spacing: .04em; transition: background-color .15s ease; }
  .link-item:nth-child(3n+1) { transform: rotate(-1.2deg); }
  .link-item:nth-child(3n+2) { transform: rotate(.9deg); }
  .link-item:nth-child(3n) { transform: rotate(-.4deg); }
  .link-item:hover { background: var(--orange); }

  /* —— 页脚 —— */
  .foot { margin-top: 48px; display: flex; flex-direction: column; align-items: center; gap: 14px; }
  .foot-text { font-family: var(--mono); font-size: 12px; letter-spacing: .08em; color: rgba(45,45,45,.6); }
  .lang-switch { display: inline-flex; gap: 8px; }
  .lang-btn { height: 28px; padding: 0 14px; border: none; cursor: pointer; font-family: var(--mono); font-size: 12px; letter-spacing: .08em; background: var(--white); color: var(--ink); clip-path: polygon(7px 0,calc(100% - 7px) 0,100% 50%,calc(100% - 7px) 100%,7px 100%,0 50%); }
  .lang-btn.active { background: var(--ink); color: #fff; }

  @media (max-width: 1024px) {
    .grid { grid-template-columns: 1fr; gap: 30px; }
    .tools-grid { column-count: 1; }
    .hero-title .tape { width: 110px; }
    .cmd-content { flex-direction: column; }
    .btn { width: 100%; }
    .lift { filter: drop-shadow(4px 4px 0 rgba(45,45,45,.28)); }
  }
  @media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
</head>
<body>
<div class="topbar">
  <img class="brand-logo" src="/logo.svg" alt="ErisPulse" />
  <span class="tag top-tag">MCP</span>
  <div class="sp"></div>
  <a class="round" href="https://github.com/ErisPulse/ErisPulse" target="_blank" rel="noopener noreferrer" title="GitHub" aria-label="GitHub">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55 0-.27-.01-1.17-.02-2.12-3.2.7-3.87-1.36-3.87-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.19 1.76 1.19 1.03 1.75 2.69 1.25 3.34.95.1-.74.4-1.25.72-1.53-2.55-.29-5.23-1.28-5.23-5.68 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.1 11.1 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.83 1.19 3.09 0 4.41-2.69 5.38-5.25 5.67.41.35.77 1.05.77 2.12 0 1.53-.01 2.76-.01 3.14 0 .3.2.67.8.55A11.51 11.51 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z"/></svg>
  </a>
</div>

<main>
  <header class="hero">
    <span class="tag">${t.crumbs}</span>
    <h1 class="hero-title">${t.title}<span class="tape tape-red"></span></h1>
    <p class="hero-sub">${t.lead}</p>
    <div class="badges">${chips}</div>
  </header>

  <div class="grid">
    <div class="card full lift tilt r-1">
      <div class="torn torn-body">
        <span class="tape tape-blue" style="top:-10px;left:22px;transform:rotate(-5deg)"></span>
        <div class="card-head"><span class="num">01</span><h2>${t.docsTitle}</h2></div>
        <p class="desc">${t.docsDesc}</p>
        <div class="tabs">
          ${t.docsTabs.map((n, i) => '<button class="tab-btn' + (i === 0 ? " active" : "") + '" onclick="switchTab(' + i + ')">' + n + "</button>").join("")}
        </div>
        <div class="tab-pane active" id="pane-0">
          <p class="desc">${t.npmDesc}</p>
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
        <div class="tab-pane" id="pane-1">
          <p class="desc">${t.remoteDesc}</p>
          <div class="cmd-wrapper">
            <div class="cmd-label">${t.remoteLabel}</div>
            <div class="cmd-content"><pre>${remoteJson}</pre><button class="btn" data-copy>${t.copyBtn}</button></div>
          </div>
        </div>
      </div>
    </div>

    <div class="card lift tilt r-4">
      <div class="torn torn-body">
        <div class="card-head"><span class="num">02</span><h2>${t.docsToolsTitle}</h2></div>
        <div class="tools-grid one">${docsToolsRows}</div>
      </div>
    </div>

    <div class="card lift tilt r-6">
      <div class="torn torn-body">
        <div class="card-head"><span class="num alt">03</span><h2>${t.securityTitle}</h2></div>
        <div class="stickers">${secStickers}</div>
      </div>
    </div>

    <div class="card full lift tilt r-3">
      <div class="torn torn-body">
        <span class="tape tape-orange" style="top:-10px;right:22px;transform:rotate(4deg)"></span>
        <div class="card-head"><span class="num alt">04</span><h2>${t.apiTitle}</h2></div>
        <p class="desc">${t.apiDesc}</p>
        <div class="cmd-wrapper">
          <div class="cmd-label"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/><line x1="8.12" y1="8.12" x2="12" y2="12"/></svg>${t.apiInstallLabel}</div>
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
    </div>

    <div class="card full lift tilt r-2">
      <div class="torn torn-body">
        <div class="card-head"><span class="num">05</span><h2>${t.apiToolsTitle}</h2></div>
        <div class="tools-grid">${apiToolsRows}</div>
        <p class="note">${t.apiToolsNote}</p>
      </div>
    </div>

    <div class="card full lift tilt r-5">
      <div class="torn torn-body">
        <span class="tape tape-white" style="top:-10px;left:38%;transform:rotate(3deg)"></span>
        <div class="card-head"><span class="num">06</span><h2>${t.linksTitle}</h2></div>
        <div class="links-grid">
          <a href="https://github.com/ErisPulse/ErisPulse" target="_blank" rel="noopener noreferrer" class="link-item">${t.links.repo}</a>
          <a href="https://www.npmjs.com/package/${NPM_PACKAGE}" target="_blank" rel="noopener noreferrer" class="link-item">${t.links.npm}</a>
          <a href="https://github.com/wsu2059q/ErisPulse-ApiMCP" target="_blank" rel="noopener noreferrer" class="link-item">${t.links.apimcp}</a>
          <a href="https://docs.erisdev.com" target="_blank" rel="noopener noreferrer" class="link-item">${t.links.docs}</a>
          <a href="https://www.erisdev.com" target="_blank" rel="noopener noreferrer" class="link-item">${t.links.site}</a>
        </div>
      </div>
    </div>
  </div>

  <div class="foot">
    <div class="foot-text">${t.foot}</div>
    <div class="lang-switch">
      <button class="lang-btn ${isZh ? "" : "active"}" onclick="switchLang('en')">English</button>
      <button class="lang-btn ${isZh ? "active" : ""}" onclick="switchLang('zh')">中文</button>
    </div>
  </div>
</main>

<script>
(function () {
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
      if (url.pathname === "/logo.svg") {
        return new Response(LOGO_SVG, {
          headers: {
            "Content-Type": "image/svg+xml; charset=utf-8",
            "Cache-Control": "public, max-age=86400",
            ...corsHeaders(),
          },
        });
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
