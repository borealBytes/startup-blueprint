/**
 * API Worker
 * Handles API endpoints for D1, R2, and user management
 */

interface Env {
  SESSION_STORE: KVNamespace;
  DB: D1Database;
  STORAGE: R2Bucket;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    
    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*.SuperiorByteWorks.com',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Rate limiting (simplified)
    const userId = await getUserIdFromRequest(request, env);
    if (userId && !(await checkRateLimit(userId, env))) {
      return new Response('Rate limit exceeded', { status: 429 });
    }

    try {
      // Route handling
      if (url.pathname === '/api/contact' && request.method === 'POST') {
        return await handleContactSubmission(request, env);
      }
      
      if (url.pathname === '/api/user' && request.method === 'GET') {
        return await handleGetUser(request, env);
      }
      
      if (url.pathname === '/api/activity' && request.method === 'GET') {
        return await handleGetActivity(request, env);
      }
      
      if (url.pathname === '/api/upload' && request.method === 'POST') {
        return await handleUploadRequest(request, env);
      }
      
      if (url.pathname === '/api/files' && request.method === 'GET') {
        return await handleGetFiles(request, env);
      }
      
      if (url.pathname === '/api/logout' && request.method === 'POST') {
        return await handleLogout(request, env);
      }

      return new Response('Not Found', { status: 404 });
    } catch (error) {
      console.error('API error:', error);
      return new Response('Internal Server Error', { status: 500 });
    }
  },
};

async function getUserIdFromRequest(request: Request, env: Env): Promise<string | null> {
  const cookies = request.headers.get('Cookie') || '';
  const sessionMatch = cookies.match(/session=([^;]+)/);
  
  if (!sessionMatch) return null;
  
  return await env.SESSION_STORE.get(`session:${sessionMatch[1]}`);
}

async function checkRateLimit(userId: string, env: Env): Promise<boolean> {
  const key = `ratelimit:${userId}:${Math.floor(Date.now() / 60000)}`;
  const count = parseInt(await env.SESSION_STORE.get(key) || '0');
  
  if (count >= 10) return false; // 10 req/min
  
  await env.SESSION_STORE.put(key, String(count + 1), { expirationTtl: 60 });
  return true;
}

async function handleContactSubmission(request: Request, env: Env): Promise<Response> {
  const { email } = await request.json() as { email: string };
  
  // Validate email
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return new Response('Invalid email', { status: 400 });
  }

  // Store in D1
  await env.DB.prepare('INSERT INTO contacts (email) VALUES (?)').bind(email).run();

  return new Response(JSON.stringify({ success: true }), {
    headers: { 'Content-Type': 'application/json' },
  });
}

async function handleGetUser(request: Request, env: Env): Promise<Response> {
  const userId = await getUserIdFromRequest(request, env);
  if (!userId) return new Response('Unauthorized', { status: 401 });

  const result = await env.DB.prepare('SELECT * FROM users WHERE id = ?').bind(userId).first();
  
  return new Response(JSON.stringify(result), {
    headers: { 'Content-Type': 'application/json' },
  });
}

async function handleGetActivity(request: Request, env: Env): Promise<Response> {
  const userId = await getUserIdFromRequest(request, env);
  if (!userId) return new Response('Unauthorized', { status: 401 });

  const result = await env.DB.prepare(
    'SELECT * FROM activity WHERE user_id = ? ORDER BY created_at DESC LIMIT 10'
  ).bind(userId).all();

  return new Response(JSON.stringify(result.results || []), {
    headers: { 'Content-Type': 'application/json' },
  });
}

async function handleUploadRequest(request: Request, env: Env): Promise<Response> {
  const userId = await getUserIdFromRequest(request, env);
  if (!userId) return new Response('Unauthorized', { status: 401 });

  const { filename, contentType } = await request.json() as { filename: string; contentType: string };
  
  // Generate presigned URL (simplified - actual implementation needs R2 presigned URLs)
  const key = `${userId}/${Date.now()}-${filename}`;
  const uploadUrl = `/r2-upload/${key}`;

  return new Response(JSON.stringify({ uploadUrl }), {
    headers: { 'Content-Type': 'application/json' },
  });
}

async function handleGetFiles(request: Request, env: Env): Promise<Response> {
  const userId = await getUserIdFromRequest(request, env);
  if (!userId) return new Response('Unauthorized', { status: 401 });

  try {
    const objects = await env.STORAGE.list({ prefix: `${userId}/` });
    
    const files = objects.objects.map(obj => ({
      name: obj.key.split('/').pop(),
      url: `/r2-download/${obj.key}`,
    }));

    return new Response(JSON.stringify(files), {
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('Error listing files:', error);
    return new Response(JSON.stringify([]), {
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

async function handleLogout(request: Request, env: Env): Promise<Response> {
  const cookies = request.headers.get('Cookie') || '';
  const sessionMatch = cookies.match(/session=([^;]+)/);
  
  if (sessionMatch) {
    await env.SESSION_STORE.delete(`session:${sessionMatch[1]}`);
  }

  const response = new Response(JSON.stringify({ success: true }));
  response.headers.set(
    'Set-Cookie',
    'session=; HttpOnly; Secure; SameSite=Lax; Max-Age=0; Path=/'
  );

  return response;
}
