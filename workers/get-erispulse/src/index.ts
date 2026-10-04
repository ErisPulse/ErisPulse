interface Env {
  GITHUB_REPO: string;
  GITHUB_BRANCH: string;
  CACHE_TTL: number | string;
}

interface Ctx {
  waitUntil(promise: Promise<unknown>): void;
}

const SCRIPT_MAP: Record<string, { path: string; contentType: string }> = {
  "/install.ps1": {
    path: "scripts/install/install.ps1",
    contentType: "text/plain; charset=utf-8",
  },
  "/install.sh": {
    path: "scripts/install/install.sh",
    contentType: "text/plain; charset=utf-8",
  },
};

const GITHUB_RAW_BASE = "https://raw.githubusercontent.com";
const UPSTREAM_TIMEOUT_MS = 10_000;
// 兜底缓存：上游故障时返回最近一次成功内容（边缘缓存尽力保留，远超常规 TTL）
const FALLBACK_TTL = 60 * 60 * 24 * 30;

function respond(request: Request, status: number, headers: Record<string, string>, body?: string): Response {
  const response = new Response(body ?? null, { status, headers });
  // HEAD 请求不得携带响应体
  if (request.method === "HEAD") {
    return new Response(null, { status, headers: response.headers });
  }
  return response;
}

export default {
  async fetch(request: Request, env: Env, ctx: Ctx): Promise<Response> {
    const url = new URL(request.url);
    const script = SCRIPT_MAP[url.pathname];
    if (!script) {
      return respond(request, 404, { "Content-Type": "text/plain; charset=utf-8" }, "Not Found");
    }

    const ttl = Number(env.CACHE_TTL ?? 300) || 300;
    const repo = env.GITHUB_REPO || "ErisPulse/ErisPulse";
    const branch = env.GITHUB_BRANCH || "Develop/v2";
    const rawUrl = `${GITHUB_RAW_BASE}/${repo}/${branch}/${script.path}`;

    const cache = caches.default;
    // Cache API 仅接受 GET：以剥掉 query 的 GET 请求规范化缓存键，避免任意 query 绕过边缘缓存
    const cacheKey = new Request(url.origin + url.pathname, { method: "GET" });
    const fallbackKey = new Request(url.origin + url.pathname + "?fallback", { method: "GET" });
    const cached = await cache.match(cacheKey, { ignoreMethod: true });
    if (cached) {
      return cached;
    }

    let upstream: Response;
    try {
      upstream = await fetch(rawUrl, {
        headers: {
          "User-Agent": "ErisPulse-Installer-Worker/1.0",
          Accept: "text/plain",
        },
        signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
        cf: { cacheTtl: ttl },
      });
    } catch (err) {
      console.error(`[get-erispulse] upstream unreachable: ${rawUrl}`, err);
      return serveFallback(request, cache, fallbackKey, script);
    }

    if (!upstream.ok) {
      console.error(`[get-erispulse] upstream ${upstream.status} for ${rawUrl}`);
      // 404 透传：脚本路径 / 分支配置错误应显式暴露，而不是混入网关错误
      if (upstream.status === 404) {
        return respond(
          request,
          404,
          { "Content-Type": "text/plain; charset=utf-8" },
          "Script not found upstream",
        );
      }
      return serveFallback(request, cache, fallbackKey, script);
    }

    const body = await upstream.text();
    const headers: Record<string, string> = {
      "Content-Type": script.contentType,
      "Content-Disposition": `attachment; filename="${url.pathname.slice(1)}"`,
      "Cache-Control": `public, max-age=${ttl}`,
      "X-Content-Type-Options": "nosniff",
      "Access-Control-Allow-Origin": "*",
    };

    ctx.waitUntil(cache.put(cacheKey, new Response(body, { headers })));
    ctx.waitUntil(
      cache.put(
        fallbackKey,
        new Response(body, {
          headers: { ...headers, "Cache-Control": `public, max-age=${FALLBACK_TTL}` },
        }),
      ),
    );

    return respond(request, 200, headers, body);
  },
};

async function serveFallback(
  request: Request,
  cache: Cache,
  fallbackKey: Request,
  script: { contentType: string },
): Promise<Response> {
  const stale = await cache.match(fallbackKey, { ignoreMethod: true });
  if (stale) {
    const headers: Record<string, string> = {};
    stale.headers.forEach((v, k) => {
      headers[k] = v;
    });
    headers["X-Cache"] = "fallback";
    return respond(request, 200, headers, await stale.text());
  }
  return respond(
    request,
    502,
    { "Content-Type": "text/plain; charset=utf-8" },
    "Upstream temporarily unavailable, please retry later",
  );
}
