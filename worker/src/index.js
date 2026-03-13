const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'content-type, x-api-key, anthropic-version, anthropic-dangerous-allow-browser, x-worker-token',
  'Access-Control-Max-Age': '86400',
};

function addCors(headers) {
  for (const [k, v] of Object.entries(CORS_HEADERS)) headers.set(k, v);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    // Supabase REST proxy: GET /supabase/<table>?<postgrest-params>
    if (url.pathname.startsWith('/supabase/')) {
      // Auth: require X-Worker-Token header
      const token = request.headers.get('x-worker-token') || '';
      if (!env.WORKER_TOKEN || token !== env.WORKER_TOKEN) {
        return new Response(JSON.stringify({ error: 'Unauthorized' }), {
          status: 401,
          headers: { ...CORS_HEADERS, 'content-type': 'application/json' },
        });
      }

      const table = url.pathname.slice('/supabase/'.length);
      const supaUrl = `${env.SUPABASE_URL}/rest/v1/${table}${url.search}`;
      const upstream = await fetch(supaUrl, {
        headers: {
          'apikey': env.SUPABASE_SERVICE_KEY,
          'Authorization': `Bearer ${env.SUPABASE_SERVICE_KEY}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      });
      const resHeaders = new Headers(upstream.headers);
      addCors(resHeaders);
      return new Response(upstream.body, { status: upstream.status, headers: resHeaders });
    }

    // Claude API proxy
    if (request.method !== 'POST') {
      return new Response('Use POST', { status: 405 });
    }

    const headers = new Headers();
    headers.set('content-type', 'application/json');
    headers.set('x-api-key', request.headers.get('x-api-key') || '');
    headers.set('anthropic-version', request.headers.get('anthropic-version') || '2023-06-01');
    headers.set('anthropic-dangerous-allow-browser', 'true');

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers,
      body: request.body,
    });

    const resHeaders = new Headers(response.headers);
    addCors(resHeaders);

    return new Response(response.body, { status: response.status, headers: resHeaders });
  }
};
