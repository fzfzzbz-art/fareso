// utils/sync.js — ★ v3.9: المزامنة الثنائية الفورية (Two-Way Real-time Sync)
// ─────────────────────────────────────────────────────────────────────────────
// من البوت إلى الموقع: كل تغيير (إيموجي/تفاعل/حالة/خيار) يُبثّ فوراً للواجهة عبر
//   SSE (/dashboard/api/events) فيتحدّث الموقع لحظياً بلا أي استفسار يدوي.
// من الموقع إلى البوت: أي تعديل من الموقع (لوحة/إعدادات/خيارات) يُطبَّق فوراً
//   على الجلسة الحيّة (s.applyPrefs/s.setEmoji/s.toggleReact) ويُحفظ على القرص
//   ويُبثّ للواجهات الأخرى — دون إعادة تشغيل إطلاقاً.
// ─────────────────────────────────────────────────────────────────────────────
import logger from './logger.js';

// عملاء SSE الحاليون: { id: { res, userId } }
const sseClients = new Map();
let sseSeq = 0;

/** تسجيل عميل SSE (من dashboard/api.js) */
export function addSseClient(res, { userId = null } = {}) {
  const id = `sse_${++sseSeq}`;
  sseClients.set(id, { res, userId });
  return id;
}

export function removeSseClient(id) {
  sseClients.delete(id);
}

/** بث حدث مزامنة لكل واجهات الويب المتصلة (فوري) */
export function broadcastToDashboards(event, data = {}) {
  const payload = JSON.stringify({ event, data, at: Date.now() });
  let delivered = 0;
  for (const [id, client] of [...sseClients]) {
    try {
      client.res.write(`data: ${payload}\n\n`);
      delivered += 1;
    } catch {
      sseClients.delete(id);
    }
  }
  if (delivered) logger.debug({ event, delivered }, 'بث مزامنة للواجهات');
  return delivered;
}

/**
 * إشعار واجهة الويب بتغيير جاء من البوت (تيليجرام/واتساب).
 * يُستدعى بعد كل تعديل من البوت: إيموجي، تفاعل، حالة، خيار، ربط/فك ربط…
 */
export function notifyDashboardChanged(kind, detail = {}) {
  broadcastToDashboards('session-changed', { kind, ...detail });
}

/**
 * تطبيق فوري لتغيير من الموقع على جلسة حيّة — الواجهة الأخرى للسهم.
 * يعيد true إن وُجدت جلسة حيّة وطُبِّق عليها التغيير مباشرة.
 * (التوابع getSession/listServers/applySessionPrefs تُمرَّر لتفادي الاستيراد الدائري)
 */
export async function pushPrefsToSession(getSessionFn, userId, phone, patch = {}) {
  const s = getSessionFn(String(userId), phone);
  if (!s) return { live: false };
  try {
    if (patch.emoji || patch.emojis) s.setEmoji(patch.emojis || patch.emoji);
    if (typeof patch.reactEnabled === 'boolean') s.toggleReact(patch.reactEnabled);
    if (typeof patch.autoView === 'boolean') s.toggleView(patch.autoView);
    if (typeof patch.autoLike === 'boolean') s.toggleLike(patch.autoLike);
    // أي حقول إضافية تُطبَّق عبر applyPrefs مباشرة
    s.applyPrefs(patch);
    broadcastToDashboards('prefs-applied', { userId: String(userId), phone, patch });
    return { live: true };
  } catch (err) {
    logger.warn({ err: err?.message || err, phone }, 'فشل تطبيق فوري لإعدادات الموقع على الجلسة');
    return { live: false, error: err?.message || String(err) };
  }
}
