// utils/interactive.js — ★ v3.12: القوائم التفاعلية الفخمة لأرقام الواتساب
// ─────────────────────────────────────────────────────────────────────────────
// الاستراتيجية المزدوجة (لا يوجد مسار واحد مضمون على كل الأجهزة):
//   1) Interactive/NativeFlow (interactiveMessage) — قوائم أصلية بتفاعل نقرة.
//   2) fallback: صورة واجهة (لوفي 🎨) + نص مقسّم بأقسام مرتبة فخمة (يعمل على كل الأجهزة).
//
// صراحة فنية: واتساب يقيّد القوائم/الأزرار التفاعلية بالحسابات التجارية — على
// الحسابات العادية قد تصل كنص أو لا تصل. لذلك تُجرَّب القائمة الأصلية دائماً،
// وعند أي فشل يُرسل الـfallback الفخم تلقائياً بلا خطأ يظهر للمستخدم.
// ─────────────────────────────────────────────────────────────────────────────
import fs from 'node:fs';
import logger from './logger.js';
import { packageMedia } from './performance.js';
import config from '../config.js';

/** بناء أقسام القائمة التفاعلية من خريطة التصنيفات */
export function buildSections(categoriesMap) {
  const sections = [];
  for (const [key, cat] of categoriesMap) {
    if (!cat.list?.length) continue;
    sections.push({
      title: `${cat.icon} ${cat.name} (${cat.list.length})`.slice(0, 24),
      rows: cat.list.slice(0, 10).map((c, i) => ({
        header: '',
        title: `◈ .${c.name}`.slice(0, 24),
        description: `${c.desc || ''}${c.owner ? ' 👑' : ''}`.slice(0, 72),
        id: `menu_${key}_${i}`
      }))
    });
  }
  return sections.filter((s) => s.rows.length);
}

/** إرسال النص على دفعات آمنة لحدود واتساب. */
async function sendTextChunks(session, jid, text, maxLength = 3800) {
  const value = String(text || '').trim();
  if (!value) return 0;
  let sent = 0;
  for (let i = 0; i < value.length; i += maxLength) {
    await session.sendText(jid, value.slice(i, i + maxLength));
    sent += 1;
  }
  return sent;
}

/**
 * إرسال قائمة تفاعلية مع fallback فخم (صورة + أقسام).
 * @param {object} session جلسة واتساب
 * @param {string} jid     جهة الإرسال
 * @param {object} opts    { title, subtitle, footer, buttonText, sections, bigText, imageUrl }
 * @returns {Promise<{mode: 'interactive'|'fallback-image'|'fallback-text'|'failed'}>}
 */
export async function sendInteractiveMenu(session, jid, opts = {}) {
  const {
    title = 'قــائــمــة الأوامـر',
    subtitle = 'اختر قسماً لتظهر لك أوامره',
    footer = '',
    buttonText = '☰ افتح الأقسام',
    sections = [],
    bigText = '',
    imageUrl = ''
  } = opts;

  // ─── المسار المضمون أولاً: نص عادي ظاهر على كل أنواع الحسابات ───
  // بعض الحسابات العادية تُرجع نجاحاً من interactiveMessage رغم أن الرسالة
  // لا تظهر للمستخدم، لذلك لا نعتمد عليه لإظهار القائمة.
  if (bigText) {
    try {
      const count = await sendTextChunks(session, jid, bigText);
      return { mode: 'fallback-text', chunks: count };
    } catch (err) {
      logger.debug({ err: err?.message || err }, 'فشل إرسال نص القائمة — سنجرب الصورة');
    }
  }

  // ─── fallback بصري عند تعذر إرسال النص ───
  // الأولوية: الملف المرفق داخل assets ← ثم رابط URL من الإعدادات
  let imgBuffer = null;
  const localFile = config.menu?.imageFile;
  try { if (localFile && fs.existsSync(localFile)) imgBuffer = fs.readFileSync(localFile); } catch { /* تجاهل */ }
  if (!imgBuffer?.length && imageUrl) imgBuffer = await packageMedia(imageUrl);

  if (imgBuffer?.length) {
    try {
      await session.sock.sendMessage(jid, {
        image: imgBuffer,
        caption: String(bigText).slice(0, 4000) || `*${title}*\n${footer}`
      });
      return { mode: 'fallback-image' };
    } catch (err) {
      logger.debug({ err: err?.message || err }, 'فشل إرسال صورة الواجهة — نص فقط');
    }
  }

  return { mode: 'failed' };
}

/** صياغة نص الأقسام الفخم (يُستخدم في الـfallback وفي الأمر النصي) */
export function buildFancyText(title, headerLines, categoriesMap, footer = '') {
  let out =
    `╔═══❖ *「 ${title} 」* ❖═══╗\n` +
    (headerLines || []).map((l) => `║  ✦ ${l}`).join('\n') +
    `\n║\n`;

  for (const [, cat] of categoriesMap) {
    if (!cat.list?.length) continue;
    out += `╠═════════════════════════\n`;
    out += `║ ${cat.icon} *『 ${cat.name} 』* (${cat.list.length})\n`;
    out += `╠═════════════════════════\n`;
    for (const c of cat.list) {
      out += `║  ◈ *.${c.name}*${c.owner ? ' 👑' : ''}\n`;
      if (c.desc) out += `║     └ _${c.desc}_\n`;
    }
    out += `║\n`;
  }
  out += `╚═════════════════════════\n> ${footer}`;
  return out;
}

/** رابط صورة الواجهة من الإعدادات (URL فقط — الملف المحلي يُقرأ تلقائياً) */
export function luffyImageUrl() {
  return config.menu?.luffyImageUrl || '';
}

export default { sendInteractiveMenu, buildFancyText, buildSections, luffyImageUrl };
