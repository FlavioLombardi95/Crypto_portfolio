// Cloudflare Workers Proxy per Binance API
// Deploy su https://workers.cloudflare.com/ (gratuito)

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)
  const binanceUrl = url.searchParams.get('url') || 'https://api.binance.com'
  
  // Crea nuova richiesta per Binance
  const binanceRequest = new Request(binanceUrl + url.pathname + url.search, {
    method: request.method,
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; Binance-Proxy/1.0)',
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: request.method !== 'GET' ? await request.text() : undefined
  })
  
  try {
    const response = await fetch(binanceRequest)
    return new Response(response.body, {
      status: response.status,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, X-MBX-APIKEY',
        'Content-Type': 'application/json'
      }
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      }
    })
  }
} 