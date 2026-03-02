/**
 * Cloudflare Worker — Twitter API Proxy
 * Tries multiple approaches to bypass cloud IP blocking
 */

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': '*',
        },
      });
    }

    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Method not allowed' }), {
        status: 405,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const secret = request.headers.get('X-Proxy-Secret');
    if (secret !== (env.PROXY_SECRET || 'aiscientist-bot-2024')) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const authHeader = request.headers.get('Authorization') || '';
    const body = await request.text();

    // Try multiple Twitter API endpoints
    const endpoints = [
      'https://api.twitter.com/2/tweets',
      'https://api.x.com/2/tweets',
    ];

    const results = [];

    for (const endpoint of endpoints) {
      try {
        const resp = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Authorization': authHeader,
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (compatible; TwitterBot/1.0)',
            'Accept': '*/*',
          },
          body: body,
        });

        const respText = await resp.text();
        results.push({
          endpoint,
          status: resp.status,
          body: respText,
        });

        if (resp.status === 200 || resp.status === 201) {
          return new Response(respText, {
            status: resp.status,
            headers: { 'Content-Type': 'application/json' },
          });
        }
      } catch (e) {
        results.push({
          endpoint,
          status: 0,
          body: e.message,
        });
      }
    }

    // All failed — return debug info
    return new Response(JSON.stringify({
      error: 'All endpoints failed',
      attempts: results,
    }), {
      status: 502,
      headers: { 'Content-Type': 'application/json' },
    });
  },
};
