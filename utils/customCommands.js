// utils/customCommands.js — نظام الأوامر النصية المخصّصة (التي يضيفها المطور من بوت تيليجرام)
// ─────────────────────────────────────────────────────────────────────────────
// • تُحفظ في data/custom-commands.json كأوامر نصية (اسم الأمر + نص الرد).
// • تُحمَّل تلقائياً عند إقلاع أي سيرفر (رئيسي أو عامل) وتُسجَّل في سجل أوامر
//   الواتساب (whatsapp/commands/registry.js) فتظهر مباشرة في قائمة «.الاوامر».
// • تُعاد مزامنتها لحظياً على كل السيرفرات العاملة عبر /api/custom-commands
//   (من الرئيسي) بحيث يراها ويكتبها كل رقم مربوط على أي سيرفر.
// • تُستخدم أيضاً لقراءة/كتابة «قائمة الأوامر التفاعلية أسفل الشاشة» في بوت
//   تيليجرام (Reply Keyboard) — انظر telegram/keyboards.js.
// ─────────────────────────────────────────────────────────────────────────────
import { JsonStore } from './store.js';
import config from '../config.js';
import logger from './logger.js';
import { defineCategory } from '../whatsapp/commands/registry.js';

// مخزن الأوامر المخصّصة: { commands: { <name>: { name, text, createdAt, updatedAt, addedVia } } }
export const customCommandsStore = new JsonStore(config.customCommandsFile, { commands: {} });
defineCategory('custom', { name: 'أوامر مخصّصة', icon: '⭐', desc: 'أوامر نصية أضافها المطور من تليجرام' });

/** تطبيع اسم الأمر (توحيد الألف/التاء/الياء، حذف التشكيل والمسافات والشرطات) */
export const normalizeCommandName = (s) =>
  String(s || '')
    .trim()
    .normalize('NFKC')
    .toLowerCase()
    .replace(/[\u064B-\u065F\u0670]/g, '')
    .replace(/\u0640/g, '')
    .replace(/[أإآٱ]/g, 'ا')
    .replace(/ة/g, 'ه')
    .replace(/[ىي]/g, 'ي')
    .replace(/[\s_-]+/g, '');

/** كل الأوامر المخصّصة كمصفوفة */
export function listCustomCommands() {
  const map = customCommandsStore.get('commands') || {};
  return Object.values(map);
}

/** أمر واحد بالاسم (تطبيع) */
export function getCustomCommand(name) {
  const map = customCommandsStore.get('commands') || {};
  const key = normalizeCommandName(name);
  return map[key] || null;
}

/**
 * إضافة/تحديث أمر مخصّص.
 * @returns {{ ok: boolean, error?: string, command?: object, replaced?: boolean }}
 */
export async function upsertCustomCommand(name, text, meta = {}) {
  // تنظيف الاسم: بلا نقطة بادئة، بلا أسطر جديدة، وبلا علامات تكسر تنسيق تيليجرام
  const rawName = String(name || '')
    .replace(/[\r\n`]+/g, '')
    .trim()
    .replace(/^\./, '')
    .replace(/\s+/g, '_');
  const body = String(text ?? '').trim();
  if (!rawName) return { ok: false, error: 'اسم الأمر فارغ.' };
  if (rawName.length > 60) return { ok: false, error: 'اسم الأمر طويل جداً (60 حرفاً كحد أقصى).' };
  if (!body) return { ok: false, error: 'نص الأمر فارغ.' };
  if (body.length > 4000) return { ok: false, error: 'نص الأمر طويل جداً (4000 حرف كحد أقصى).' };

  const key = normalizeCommandName(rawName);
  if (!key) return { ok: false, error: 'اسم الأمر غير صالح.' };

  const map = { ...(customCommandsStore.get('commands') || {}) };
  const existing = map[key] || null;
  const entry = {
    name: rawName,
    key,
    text: body,
    createdAt: existing?.createdAt || Date.now(),
    updatedAt: Date.now(),
    addedVia: meta.addedVia || 'telegram',
    server: meta.server || config.localServer.name
  };
  map[key] = entry;
  customCommandsStore.set('commands', map);

  // تسجيله فوراً في سجل أوامر الواتساب ليظهر في «.الاوامر» بلا إعادة تشغيل
  await registerCustomCommandInRegistry(entry, { silent: true });

  return { ok: true, command: entry, replaced: !!existing };
}

/** حذف أمر مخصّص بالاسم (مطابقة متسامحة: بالمفتاح المطبّع أو بالاسم) */
export async function removeCustomCommand(name) {
  const key = normalizeCommandName(name);
  const map = { ...(customCommandsStore.get('commands') || {}) };
  let foundKey = map[key] ? key : null;
  if (!foundKey) {
    for (const [k, v] of Object.entries(map)) {
      if (k === key || normalizeCommandName(v?.name) === key || normalizeCommandName(v?.key) === key) {
        foundKey = k;
        break;
      }
    }
  }
  if (!foundKey) return { ok: false, error: 'لا يوجد أمر بهذا الاسم.' };
  const removed = map[foundKey];
  delete map[foundKey];
  customCommandsStore.set('commands', map);
  try {
    const { unregisterCommandExact } = await import('../whatsapp/commands/registry.js');
    // نزيل الأمر المخصّص باسمه ثم بمفتاحه — بلا مطابقة الأسماء البديلة
    // (حتى لا نحذف أمراً داخلياً يشترك في الاسم)
    unregisterCommandExact(removed.name);
    unregisterCommandExact(removed.key);
    unregisterCommandExact(foundKey);
  } catch { /* تجاهل */ }
  return { ok: true, command: removed };
}

/**
 * تسجيل كل الأوامر المخصّصة داخل سجل أوامر الواتساب.
 * يُستدعى مرة عند الإقلاع (من index.js / worker-core.js) ومرة عند كل تحديث.
 */
export async function loadCustomCommandsIntoRegistry() {
  // تصنيف «أوامر مخصّصة» يُسجَّل دائماً (حتى لو كانت القائمة فارغة) ليظهر
  // في قائمة «.الاوامر» كتصنيف متاح يمكن للمطور الإضافة إليه لاحقاً.
  try {
    const { defineCategory } = await import('../whatsapp/commands/registry.js');
    defineCategory('custom', {
      name: 'أوامر مخصّصة',
      icon: '⭐',
      desc: 'أوامر نصية أضافها المطور من بوت تيليجرام'
    });
  } catch { /* تجاهل */ }
  const list = listCustomCommands();
  let registered = 0;
  for (const entry of list) {
    try {
      await registerCustomCommandInRegistry(entry, { silent: true });
      registered += 1;
    } catch (err) {
      logger.warn({ err, name: entry?.name }, 'تعذّر تسجيل أمر مخصّص');
    }
  }
  if (registered) logger.info({ registered }, 'تم تحميل الأوامر المخصّصة في سجل أوامر الواتساب');
  return registered;
}

/** تسجيل أمر واحد في السجل (بتبديل أي أمر مماثل سابق — بلا تكرار) */
async function registerCustomCommandInRegistry(entry, { silent = false } = {}) {
  const { define, defineCategory, unregisterCommandExact } = await import('../whatsapp/commands/registry.js');
  defineCategory('custom', {
    name: 'أوامر مخصّصة',
    icon: '⭐',
    desc: 'أوامر نصية أضافها المطور من بوت تيليجرام'
  });
  // إزالة النسخة القديمة *بنفس الاسم فقط* لمنع التكرار عند التحديث
  // (لا نستخدم مطابقة الأسماء البديلة حتى لا نحذف أمراً داخلياً يشترك في الاسم)
  unregisterCommandExact(entry.name);
  define({
    name: entry.name,
    aliases: [entry.name.replace(/_/g, ' ')],
    category: 'custom',
    desc: 'أمر مخصّص (نصّي) — أضافه المطور',
    handler: async (session, msg) => {
      // نقرأ النص الأحدث من المخزن دائماً (فالتعديل يسري فوراً بلا إعادة تشغيل)
      const fresh = getCustomCommand(entry.name) || entry;
      const body = String(fresh.text || '').trim();
      if (!body) return;
      await session.sendText(msg.key.remoteJid, body, {}, { quoted: msg });
    }
  });
  if (!silent) logger.info({ name: entry.name }, 'تم تسجيل أمر مخصّص');
}
