interface Env {
  GITHUB_REPO: string;
  GITHUB_BRANCH: string;
  CACHE_TTL: number;
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

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const pathname = url.pathname;

    const script = SCRIPT_MAP[pathname];
    if (!script) {
      return new Response("Not Found", { status: 404 });
    }

    const repo = env.GITHUB_REPO || "ErisPulse/ErisPulse";
    const branch = env.GITHUB_BRANCH || "Develop/v2";
    const rawUrl = `${GITHUB_RAW_BASE}/${repo}/${branch}/${script.path}`;

    const cache = caches.default;
    const cacheKey = new Request(request.url, request);
    const cached = await cache.match(cacheKey);
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
        cf: { cacheTtl: env.CACHE_TTL || 300 },
      });
    } catch {
      return new Response("Failed to fetch script from upstream", {
        status: 502,
      });
    }

    if (!upstream.ok) {
      return new Response(`Upstream returned ${upstream.status}`, {
        status: 502,
      });
    }

    const body = await upstream.text();

    const response = new Response(body, {
      status: 200,
      headers: {
        "Content-Type": script.contentType,
        "Content-Disposition": `attachment; filename="${pathname.slice(1)}"`,
        "Cache-Control": `public, max-age=${env.CACHE_TTL || 300}`,
        "Access-Control-Allow-Origin": "*",
      },
    });

    await cache.put(cacheKey, response.clone());

    return response;
  },
};
