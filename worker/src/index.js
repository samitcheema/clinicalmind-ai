export default {
  async fetch(request) {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'content-type, x-api-key, anthropic-version, anthropic-dangerous-allow-browser',
          'Access-Control-Max-Age': '86400',
        }
      });
    }

    if (request.method !== 'POST') {
      return new Response('Use POST', { status: 405 });
    }

    // Forward only specific headers — avoids passing Host and other problematic headers
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
    resHeaders.set('Access-Control-Allow-Origin', '*');

    return new Response(response.body, { status: response.status, headers: resHeaders });
  }
};
