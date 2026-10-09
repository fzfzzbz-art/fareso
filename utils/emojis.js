// utils/emojis.js — تحليل قائمة إيموجيات التفاعل مع الحفاظ على الرموز المركبة
// ─────────────────────────────────────────────────────────────────────────────
// ★ v3.10: يُحفظ أكثر من إيموجي كاملاً معاً (مثال: «🔥 ❤️» ⇒ ['🔥','❤️'])
//   • كل رمز يُقرأ كـ grapheme واحد، فتبقى الإيموجيات المركّبة (عائلة/أعلام) سليمة.
//   • قيم التعطيل (off/none/0…) تُفحص على العنصر الكامل لا على حروفه.
//   • حد أقصى 10 إيموجيات لكل رقم، وبلا تكرار.
// ─────────────────────────────────────────────────────────────────────────────

const DISABLED = new Set(['', '0', 'false', 'off', 'none', 'no', 'null', 'undefined', 'متوقف', 'ايقاف', 'إيقاف']);
export const MAX_EMOJIS = 10;

function graphemes(value) {
  const text = String(value ?? '').trim();
  if (typeof Intl?.Segmenter === 'function') {
    return [...new Intl.Segmenter('und', { granularity: 'grapheme' }).segment(text)].map((x) => x.segment);
  }
  return Array.from(text);
}

const isDisabled = (v) => DISABLED.has(String(v ?? '').trim().toLowerCase());

/** يقبل إيموجياً واحداً أو قائمة مفصولة بمسافة/فاصلة/سطر جديد. */
export function parseEmojiList(value, fallback = []) {
  const raw = Array.isArray(value) ? value : String(value ?? '').split(/[\s,،;؛|]+/u);
  const out = [];
  for (const item of raw) {
    // ★ الفحص على العنصر الكامل أولاً حتى لا تتحول كلمة مثل off إلى حروف
    if (item === null || item === undefined || isDisabled(item)) continue;
    for (const emoji of graphemes(item)) {
      const v = emoji.trim();
      if (!v || isDisabled(v) || out.includes(v)) continue;
      out.push(v);
      if (out.length >= MAX_EMOJIS) break;
    }
    if (out.length >= MAX_EMOJIS) break;
  }
  if (out.length) return out;
  if (fallback === value || (Array.isArray(fallback) && fallback.length === 0)) return [];
  return parseEmojiList(fallback, []);
}

export function primaryEmoji(value, fallback = '❤️') {
  return parseEmojiList(value, [fallback])[0] || fallback;
}

export function emojiText(value, fallback = '❤️') {
  return parseEmojiList(value, [fallback]).join(' ');
}

export default parseEmojiList;
