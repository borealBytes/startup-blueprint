/**
 * Google OAuth Authentication Worker
 * Handles OAuth flow, session management, and user creation
 */

interface Env {
  SESSION_STORE: KVNamespace;
  DB: D1Database;
  GOOGLE_CLIENT_ID: string;
  GOOGLE_CLIENT_SECRET: string;
  GOOGLE_REDIRECT_URI: string;
}

interface GoogleUserInfo {
  id: string;
  email: string;
  name: string;
  picture: string;
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

    try {
      if (url.pathname === '/auth/google') {
        return handleGoogleAuthRedirect(env);
      }
      
      if (url.pathname === '/auth/callback') {
        return await handleGoogleCallback(request, env);
      }

      return new Response('Not Found', { status: 404 });
    } catch (error) {
      console.error('Auth error:', error);
      return new Response('Internal Server Error', { status: 500 });
    }
  },
};

function handleGoogleAuthRedirect(env: Env): Response {
  const state = crypto.randomUUID();
  const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
  
  authUrl.searchParams.set('client_id', env.GOOGLE_CLIENT_ID);
  authUrl.searchParams.set('redirect_uri', env.GOOGLE_REDIRECT_URI);
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('scope', 'openid email profile');
  authUrl.searchParams.set('state', state);

  return Response.redirect(authUrl.toString(), 302);
}

async function handleGoogleCallback(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');

  if (!code || !state) {
    return new Response('Missing code or state', { status: 400 });
  }

  // Exchange code for token
  const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      code,
      client_id: env.GOOGLE_CLIENT_ID,
      client_secret: env.GOOGLE_CLIENT_SECRET,
      redirect_uri: env.GOOGLE_REDIRECT_URI,
      grant_type: 'authorization_code',
    }),
  });

  const tokens = await tokenResponse.json() as { access_token: string };

  // Get user info
  const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  });

  const userInfo: GoogleUserInfo = await userInfoResponse.json();

  // Store/update user in D1
  await env.DB.prepare(`
    INSERT INTO users (id, email, name, picture_url, updated_at)
    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(id) DO UPDATE SET
      name = excluded.name,
      picture_url = excluded.picture_url,
      updated_at = CURRENT_TIMESTAMP
  `).bind(userInfo.id, userInfo.email, userInfo.name, userInfo.picture).run();

  // Create session token
  const sessionToken = crypto.randomUUID();
  await env.SESSION_STORE.put(`session:${sessionToken}`, userInfo.id, {
    expirationTtl: 86400, // 24 hours
  });

  // Set cookie and redirect
  const response = Response.redirect('/dashboard', 302);
  response.headers.set(
    'Set-Cookie',
    `session=${sessionToken}; HttpOnly; Secure; SameSite=Lax; Max-Age=86400; Path=/`
  );

  return response;
}
