// utils/tg.js — تحصين واجهة تيليجرام (إصلاح v3.7)
// ─────────────────────────────────────────────────────────────────────
// سبب مشكلة «أمر/زر المساعدة يعطي خطأ»: النصوص تُرسل بـ parse_mode = Markdown،
// وأي علامة * أو _ غير مغلقة تجعل تيليجرام يرفض الرسالة كاملة برسالة
// «can't parse entities». هنا نغلّف دوال الإرسال/التعديل: إن وقع هذا الخطأ
// نُعيد الإرسال *بلا parse_mode* فيصل النص دائماً بدل أن يسقط الزر.
// ─────────────────────────────────────────────────────────────────────
import logger from './logger.js';

const PARSE_ERR = /parse entities|can't parse|Can't find end of|unsupported start tag|entity/i;

const descOf = (err) => String(err?.description || err?.message || err || '');

/** هل الخطأ سببه تنسيق Markdown؟ */
export function isParseError(err) {
  return PARSE_ERR.test(descOf(err));
}

/** نسخة بلا parse_mode من خيارات الإرسال */
function withoutParse(extra) {
  if (!extra || typeof extra !== 'object') return extra;
  const { parse_mode, parse_mode_deprecated, ...rest } = extra;
  return rest;
}

/**
 * يغلّف كائن تيليجرام (ctx.telegram / bot.telegram) بحيث يصبح كل إرسال
 * محصّناً ضد أخطاء التنسيق. لا يغيّر أي سلوك آخر.
 */
export function hardenTelegramApi(tg) {
  if (!tg || tg.__hardened) return tg;

  const wrapSimple = (name) => {
    if (typeof tg[name] !== 'function') return;
    const orig = tg[name].bind(tg);
    tg[name] = async (...args) => {
      try {
        return await orig(...args);
      } catch (err) {
        const extra = args[args.length - 1];
        if (isParseError(err) && extra && typeof extra === 'object' && extra.parse_mode) {
          logger.warn({ method: name, err: descOf(err) }, 'فشل تنسيق Markdown — إعادة الإرسال كنص خام');
          return orig(...args.slice(0, -1), withoutParse(extra));
        }
        throw err;
      }
    };
  };

  // التوقيع: (chatId, text, extra)
  for (const m of ['sendMessage', 'sendPhoto', 'sendVideo', 'sendAudio', 'sendDocument', 'sendAnimation', 'sendVoice']) {
    wrapSimple(m);
  }

  // editMessageText(chatId, messageId, inlineMessageId, text, extra)
  if (typeof tg.editMessageText === 'function') {
    const origEdit = tg.editMessageText.bind(tg);
    tg.editMessageText = async (...args) => {
      try {
        return await origEdit(...args);
      } catch (err) {
        const extra = args[args.length - 1];
        if (isParseError(err) && extra && typeof extra === 'object' && extra.parse_mode) {
          logger.warn({ err: descOf(err) }, 'فشل تنسيق Markdown في تعديل الرسالة — إعادة كنص خام');
          return origEdit(...args.slice(0, -1), withoutParse(extra));
        }
        throw err;
      }
    };
  }

  // editMessageCaption / editMessageReplyMarkup لا تحمل نصاً — لا حاجة لتغليفها.
  tg.__hardened = true;
  return tg;
}

export default hardenTelegramApi;
