addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

const PURGE_PASSWORD = 'your_secure_password_here';

async function handleRequest(request) {
  const url = new URL(request.url)
  const path = url.pathname

  // 标准化路径
  const normalizedPath = path.replace(/^\/+/, '/');

  if (normalizedPath === '/') {
    return Response.redirect('https://www.erisdev.com', 301)
  }

  let response

  if ( normalizedPath === '/packages.json' || 
       normalizedPath === '/packages' || 
       normalizedPath === '/packages.json/') {
    response = await fetch('https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/packages.json', {
      cf: {
        cacheEverything: true,
        cacheTtl: 14400 // 缓存 4 小时
      }
    })
  } else if ( normalizedPath === '/map.json' ||
              normalizedPath === '/map' ||
              normalizedPath === '/map.json/') {
    response = await fetch('https://raw.githubusercontent.com/ErisPulse/ErisPulse-ModuleRepo/main/map.json', {
      cf: {
        cacheEverything: true,
        cacheTtl: 14400
      }
    })
  } else if (normalizedPath.startsWith('/archived/modules/')) {
    const modulePath = normalizedPath.replace('/archived/modules', '');
    response = await fetch(`https://raw.githubusercontent.com/ErisPulse/ErisPulse-ModuleRepo/main/archived/modules${modulePath}`, {
      cf: {
        cacheEverything: true,
        cacheTtl: 14400
      }
    });
  } else if (normalizedPath.startsWith('/purge-cache/')) {
    // 检查密码
    const password = normalizedPath.split('/')[2];
    if (password === PURGE_PASSWORD) {
      response = await purgeCache()
    } else {
      response = new Response(JSON.stringify({ 
        error: 'Unauthorized', 
        message: 'Invalid password'
      }), {
        status: 401,
        headers: {
          'Content-Type': 'application/json'
        }
      })
    }
  } else {
    response = new Response(JSON.stringify({ error: 'Not Found' }), {
      status: 404,
      headers: {
        'Content-Type': 'application/json'
      }
    })
  }

  if (normalizedPath.endsWith('.json') || 
      normalizedPath === '/packages' || 
      normalizedPath === '/map' ||
      normalizedPath.startsWith('/purge-cache/')) {
    const newHeaders = new Headers(response.headers)
    newHeaders.set('Content-Type', 'application/json')
    response = new Response(response.body, {
      status: response.status,
      headers: newHeaders
    })
  }

  return response
}

async function purgeCache() {
  try {
    const cache = caches.default;
    
    const packagesUrl = 'https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/packages.json';
    await cache.delete(new Request(packagesUrl));
    const mapUrl = 'https://raw.githubusercontent.com/ErisPulse/ErisPulse-ModuleRepo/main/map.json';
    await cache.delete(new Request(mapUrl));
    
    // 注意：这里无法精确清除所有 archived/modules 下的缓存项
    // 因为 Cloudflare Workers 不支持通配符删除缓存
    
    return new Response(JSON.stringify({ 
      success: true, 
      message: 'Cache purged successfully' 
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ 
      success: false, 
      error: error.message 
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
}
