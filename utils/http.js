// utils/http.js — عميل HTTP مع ترويسة السر المشترك ومهلة زمنية
import config from '../config.js';

/**
 * طلب JSON مع ترويسة x-api-secret ومهلة
 */
export async function httpJson(url, { method = 'POST', body = null, timeoutMs = 30000, secret = config.main.apiSecret } = {}) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method,
      signal: ctrl.signal,
      headers: {
        'content-type': 'application/json',
        'x-api-secret': secret
      },
      body: body ? JSON.stringify(body) : undefined
    });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    return { ok: false, status: 0, data: {}, error: err?.message || String(err) };
  }
}
