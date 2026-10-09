// utils/performance.js — ★ v3.12: طبقة الأداء والثبات (فلود + ذاكرة + أدوات ذكية)
// ─────────────────────────────────────────────────────────────────────────────
// • sessionMsgLimit  : طابور رسائل كل جلسة (تزامن 3) — يمنع تكدّس المعالجة تحت الفلود.
// • cmdLimit         : أوامر الواتساب تُنفَّذ بتسلسل لكل جلسة (منع سباق الردود).
// • smartQueue       : حماية من ضغط تيليجرام (تُجاري retry_after عند 429 تلقائياً).
// • packageMedia     : قراءة وسائط من Buffer/Stream/URL/مسار — تسريع إرسال الوسائط
//   وإصلاح «فشل إرسال الصورة/الفيديو» الناتج عن تمرير stream بعد إغلاقه.
// • periodic memoryGC: تفريغ خفيف لمنع تضخم الذاكرة في الإقامات الطويلة (24/7).
// ─────────────────────────────────────────────────────────────────────────────
import config from '../config.js';
import logger from './logger.js';
import { pLimit, delay } from './queue.js';

/** طابور رسائل لكل جلسة واتساب (يُنشأ عند أول استخدام ويُعاد استخدامه) */
export function sessionMsgLimit(session) {
  if (!session._msgLimit) session._msgLimit = pLimit(3);
  return session._msgLimit;
}

/** طابور أوامر متسلسل لكل جلسة — أمر واحد في كل لحظة، فلا تتداخل الردود */
export function sessionCmdQueue(session) {
  if (!session._cmdQueue) session._cmdQueue = pLimit(1);
  return session._cmdQueue;
}

// ─────────── حماية بوت تيليجرام من 429 (Too Many Requests) ───────────
const tgQueues = new Map(); // chatKey -> serial limit
const TG_LAST_ERR = new Map(); // chatKey -> untilTs (معلّق مؤقت)

function tgQueueOf(chatKey) {
  if (!tgQueues.has(chatKey)) tgQueues.set(chatKey, pLimit(1));
  return tgQueues.get(chatKey);
}

/**
 * إرسال رسالة تيليجرام محميّة من حدود المعدل:
 * - طابور تسلسلي لكل محادثة (لا رسالتان بنفس اللحظة).
 * - عند 429 ينتظر retry_after ثم يعيد المحاولة مرتين.
 * - يُعيد دائماً نتيجة { ok } بدل رمي استثناء يُعلّق المعالج.
 */
export async function tgSendSafe(ctxOrTelegram, chatId, text, extra = {}) {
  const key = String(chatId);
  const telegram = ctxOrTelegram?.telegram || ctxOrTelegram;
  return tgQueueOf(key)(async () => {
    for (let attempt = 0; attempt < 3; attempt += 1) {
      try {
        return await telegram.sendMessage(chatId, text, extra);
      } catch (err) {
        const desc = String(err?.description || err?.message || err);
        const retryAfter = err?.response?.parameters?.retry_after;
        if ((err?.response?.error_code === 429 || /too many|429/i.test(desc)) && attempt < 2) {
          await delay(((Number(retryAfter) || 2) + 0.6) * 1000);
          continue;
        }
        logger.debug({ desc, chatId }, 'فشل إرسال تيليجرام (tgSendSafe)');
        return { ok: false, error: desc };
      }
    }
    return { ok: false, error: 'exhausted retries' };
  });
}

/** تغليف أي نداء تيليجرام (copyMessage, editMessageText…) بنفس الحماية */
export function tgCallSafe(ctxOrTelegram, chatId, fn) {
  const key = String(chatId);
  return tgQueueOf(key)(fn).catch((err) => {
    const desc = String(err?.description || err?.message || err);
    logger.debug({ desc, chatId }, 'فشل نداء تيليجرام (tgCallSafe)');
    return { ok: false, error: desc };
  });
}

// ─────────── تجهيز الوسائط للإرسال (إصلاح فشل الصورة/الفيديو) ───────────
/**
 * يوحّد أي مصدر وسيط إلى ما يقبله Baileys sendMessage بأمان:
 *  - Buffer → يُعاد كما هو (الأفضل: بلا تبعية للشبكة).
 *  - Stream → يُقرأ كاملاً إلى Buffer (يتفادى انغلاق الستريم قبل الصعود).
 *  - http(s) URL → يُنزَّل إلى Buffer مع مهلة (أكثر توافقاً من {url} مع الروابط الحسّاسة).
 *  - مسار محلي → يُقرأ من القرص.
 */
export async function packageMedia(input) {
  try {
    if (Buffer.isBuffer(input)) return input;
    if (input && typeof input.pipe === 'function') {
      const chunks = [];
      for await (const chunk of input) chunks.push(chunk);
      return Buffer.concat(chunks);
    }
    const s = String(input || '');
    if (/^https?:\/\//i.test(s)) {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 60_000);
      try {
        const res = await fetch(s, { signal: ctrl.signal });
        if (!res.ok) return null;
        return Buffer.from(await res.arrayBuffer());
      } finally { clearTimeout(t); }
    }
    if (s && !s.includes('\n')) {
      const { default: fs } = await import('node:fs');
      if (fs.existsSync(s)) return fs.readFileSync(s);
    }
    if (input && typeof input === 'object' && input.url) return packageMedia(input.url);
    return null;
  } catch (err) {
    logger.debug({ err: err?.message || err }, 'packageMedia فشل');
    return null;
  }
}

// ─────────── تنظيف دوري للذاكرة (استقرار 24/7) ───────────
export function startMemoryGC() {
  const everyMs = 30 * 60_000; // كل 30 دقيقة
  return setInterval(() => {
    try {
      global.gc?.();
      const used = process.memoryUsage().heapUsed / 1024 / 1024;
      if (used > (config.performance?.memoryWarnMb || 700)) {
        logger.warn({ heapUsedMb: Math.round(used) }, 'استهلاك ذاكرة مرتفع — تم تفعيل gc يدوي');
      }
    } catch { /* تجاهل */ }
  }, everyMs);
}

export default {
  sessionMsgLimit, sessionCmdQueue, tgSendSafe, tgCallSafe, packageMedia, startMemoryGC
};
