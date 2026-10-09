// utils/channel.js — ★ v3.14: الانضمام التلقائي لقناة الواتساب الرسمية بعد نجاح الربط
// ─────────────────────────────────────────────────────────────────────────────
// ★ تصحيح مهم بعد الفحص الفعلي لنسخة Baileys المثبّتة (7.0.0-rc14):
//   هذه النسخة **لا تُصدِّر** `newsletterMetadata` كتصدير مُسمّى على مستوى الحزمة
//   (تم التحقّق: `typeof B.newsletterMetadata === 'undefined'`)، لكنها توفّر دوال
//   القنوات **على كائن الـ socket نفسه** (تم التحقّق من
//   `lib/Socket/index.d.ts`: `newsletterFollow: (jid) => Promise<unknown>`).
//   لذلك لم يُعد الملف يستورد شيئاً من Baileys، بل يستدعي الدوال عبر الـ socket
//   بفحص وجودها أولاً (`typeof sock.x === 'function'`) — فإن غابت في نسخة أخرى
//   لا ينكسر المشروع ولا يُسقط الجلسة، بل يُرسل الرابط كبديل.
//
// كيف يعمل:
//   1) يُستخرج رمز الدعوة من الرابط الرسمي:
//      https://whatsapp.com/channel/0029Vb8AkYM2v1IuuBl6cy0W → 0029Vb8AkYM2v1IuuBl6cy0W
//   2) يُحوَّل الرمز إلى معرّف القناة عبر sock.newsletterMetadata('invite', code)
//      إن كانت متاحة في هذه النسخة.
//   3) sock.newsletterFollow(jid) ⇒ يصبح الرقم متابعاً للقناة.
//   4) أي فشل في أي خطوة ⇒ يُرسل الرابط نفسه في محادثة الرقم المربوط كي يفتحه
//      المستخدم بضغطة واحدة — فلا يبقى بلا مسار للانضمام.
//
// ⚠️ شفافية: واتساب لا يوفّر «إضافة مستخدم للقناة قسراً»؛ المتاح هو «متابعة»
//    (follow) ينفّذها الرقم نفسه — وهذا ما يُنفَّذ هنا.
// ─────────────────────────────────────────────────────────────────────────────
import logger from './logger.js';
import config from '../config.js';

export const OFFICIAL_CHANNEL_INVITE = String(
  config.channel?.invite || '0029Vb8AkYM2v1IuuBl6cy0W'
).trim();

export const OFFICIAL_CHANNEL_URL = String(
  config.channel?.url || `https://whatsapp.com/channel/${OFFICIAL_CHANNEL_INVITE}`
).trim();

/** استخراج رمز الدعوة من رابط قناة أو من الرمز نفسه */
export function extractInviteCode(input) {
  const raw = String(input || '').trim();
  if (!raw) return '';
  const m = raw.match(/whatsapp\.com\/channel\/([A-Za-z0-9_-]+)/i);
  if (m) return m[1];
  if (/^[A-Za-z0-9_-]{15,40}$/.test(raw)) return raw;
  return '';
}

/** هل تدعم هذه النسخة من Baileys دوال القنوات على الـ socket؟ */
export function channelApiSupport(sock) {
  return {
    metadata: typeof sock?.newsletterMetadata === 'function',
    follow: typeof sock?.newsletterFollow === 'function',
    unfollow: typeof sock?.newsletterUnfollow === 'function',
    any: typeof sock?.newsletterFollow === 'function'
  };
}

/**
 * تحويل رمز الدعوة إلى معرّف القناة (jid) عبر واجهة الـ socket.
 * @returns {Promise<{ok:boolean, jid?:string, name?:string, code?:string, error?:string}>}
 */
export async function resolveChannelJid(sock, inviteOrUrl) {
  const code = extractInviteCode(inviteOrUrl);
  if (!code) return { ok: false, error: 'رمز دعوة القناة غير صالح.' };
  if (typeof sock?.newsletterMetadata !== 'function') {
    return {
      ok: false,
      code,
      error: 'نسخة Baileys المثبّتة لا توفّر newsletterMetadata على المقبس — سيُرسل الرابط للانضمام اليدوي.'
    };
  }
  try {
    const meta = await sock.newsletterMetadata('invite', code);
    const jid = meta?.id ? String(meta.id) : '';
    if (!jid) return { ok: false, code, error: 'لم تُرجِع واتساب معرّفاً لهذه القناة.' };
    return { ok: true, jid, name: meta?.name || '', code };
  } catch (err) {
    logger.warn({ err: err?.message || err, code }, 'تعذّر قراءة بيانات قناة الواتساب');
    return { ok: false, code, error: err?.message || String(err) };
  }
}

/**
 * متابعة القناة من الرقم المربوط.
 * @returns {Promise<{ok:boolean, jid?:string, name?:string, error?:string, stage?:string}>}
 */
export async function followChannel(sock, inviteOrUrl) {
  if (!sock) return { ok: false, error: 'مقبس واتساب غير متوفر.', stage: 'socket' };
  const sup = channelApiSupport(sock);
  if (!sup.follow) {
    return { ok: false, error: 'نسخة Baileys الحالية لا تدعم متابعة القنوات على المقبس.', stage: 'api' };
  }
  const resolved = await resolveChannelJid(sock, inviteOrUrl);
  if (!resolved.ok) return { ...resolved, stage: 'resolve' };
  try {
    await sock.newsletterFollow(resolved.jid);
    return { ok: true, jid: resolved.jid, name: resolved.name };
  } catch (err) {
    return { ok: false, jid: resolved.jid, error: err?.message || String(err), stage: 'follow' };
  }
}

/** نصّ جاهز يُرسل في محادثة الرقم المربوط */
export function channelInviteMessage({ done = false, reason = '' } = {}) {
  if (done) {
    return (
      '📢 *قناة الواتساب الرسمية*\n\n' +
      '✅ تمّت متابعة رقمك للقناة الرسمية تلقائياً.\n' +
      `🔗 ${OFFICIAL_CHANNEL_URL}\n\n` +
      'تابع القناة للاطّلاع على التحديثات والأوامر الجديدة أولاً بأول.'
    );
  }
  return (
    '📢 *قناة الواتساب الرسمية*\n\n' +
    'اضغط الرابط التالي للانضمام ومتابعة التحديثات:\n' +
    `🔗 ${OFFICIAL_CHANNEL_URL}\n` +
    (reason ? `\nℹ️ ${reason}` : '')
  );
}

/**
 * ★ الدالة المستدعاة من whatsapp/session.js لحظة نجاح الاتصال:
 *   متابعة القناة تلقائياً، وعند أي فشل يُرسل الرابط في محادثة الرقم نفسه.
 * لا ترمي أي استثناء إطلاقاً (كل المسارات محمية).
 * @returns {Promise<{ok:boolean, jid?:string, fallbackSent?:boolean, error?:string}>}
 */
export async function followChannelForSession(session) {
  try {
    if (!session?.sock) return { ok: false, error: 'لا مقبس.' };
    const enabled = config.channel?.autoFollow !== false;
    if (!enabled) return { ok: false, error: 'الانضمام التلقائي معطّل من الإعدادات.' };

    const res = await followChannel(session.sock, OFFICIAL_CHANNEL_INVITE);
    const chat = (() => {
      try { return session.selfJid(); } catch { return ''; }
    })();

    if (res.ok) {
      logger.info({ phone: session.phone, jid: res.jid, name: res.name }, '✅ تمت متابعة قناة الواتساب الرسمية');
      if (chat) await session.sendText(chat, channelInviteMessage({ done: true })).catch(() => {});
      return { ok: true, jid: res.jid };
    }

    logger.warn(
      { phone: session.phone, stage: res.stage, err: res.error },
      'تعذّر الانضمام التلقائي للقناة — يُرسل الرابط بدلاً منه'
    );
    let fallbackSent = false;
    if (chat) {
      fallbackSent = await session
        .sendText(
          chat,
          channelInviteMessage({
            done: false,
            reason: 'إن لم يُفتح الرابط تلقائياً فانسخه والصقه في المتصفح، أو افتحه من زر «📢 قناة الواتساب» في بوت تيليجرام.'
          })
        )
        .then(() => true)
        .catch(() => false);
    }
    return { ok: false, jid: res.jid, fallbackSent, error: res.error };
  } catch (err) {
    logger.debug({ err: err?.message || err }, 'فشل مسار الانضمام التلقائي للقناة');
    return { ok: false, error: err?.message || String(err) };
  }
}

/** حالة القناة لهذه الجلسة — للعرض في بوت تيليجرام */
export function channelStatusForSession(session) {
  const sup = channelApiSupport(session?.sock);
  return {
    url: OFFICIAL_CHANNEL_URL,
    invite: OFFICIAL_CHANNEL_INVITE,
    followed: !!session?._channelFollowed,
    supported: sup.any,
    metadataSupported: sup.metadata
  };
}

export default followChannelForSession;
