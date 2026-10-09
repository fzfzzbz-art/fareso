// utils/sessionPrefs.js — إعدادات كل رقم (إيموجي/تفاعل/مشاهدة/قلب/سرعة) محفوظة على القرص
// ─────────────────────────────────────────────────────────────────────────────
// الهدف: ألا تتغيّر أو تُفقد إعدادات أي رقم مربوط عند إعادة تشغيل السيرفر.
// تُحفظ في data/session-prefs.json (كتابة ذرّية) وتُقرأ عند إنشاء الجلسة.
// ─────────────────────────────────────────────────────────────────────────────
import { JsonStore } from './store.js';
import config from '../config.js';

export const prefsStore = new JsonStore(config.prefsFile, { prefs: {} });

export const prefsKey = (userId, phone) => `${userId}:${String(phone || '').replace(/\D/g, '')}`;

/** إعدادات رقم واحد — تُرجع كائناً فارغاً إن لم يوجد سجل بعد */
export function getPrefs(userId, phone) {
  const all = prefsStore.get('prefs') || {};
  return all[prefsKey(userId, phone)] || {};
}

/** ترحيل واحد لكل رقم: فعّل تفاعل الحالات افتراضياً للنسخ السابقة واحفظه كإعداد مستخدم. */
export function ensureStatusReactionEnabled(userId, phone, defaultEmoji = '') {
  const current = getPrefs(userId, phone);
  if (Number(current.statusReactionPrefsVersion || 0) >= 1) return current;
  const patch = { reactEnabled: true, statusReactionPrefsVersion: 1 };
  if (!current.emoji && defaultEmoji) {
    patch.emoji = String(defaultEmoji).trim();
    patch.autoLike = false;
  }
  return setPrefs(userId, phone, patch);
}

/** دمج/تحديث إعدادات رقم — يُرجِع القيمة النهائية المحفوظة */
export function setPrefs(userId, phone, patch = {}) {
  const all = { ...(prefsStore.get('prefs') || {}) };
  const k = prefsKey(userId, phone);
  all[k] = { ...(all[k] || {}), ...patch, updatedAt: Date.now() };
  prefsStore.set('prefs', all);
  return all[k];
}

/** حذف إعدادات رقم (عند فك الربط) */
export function dropPrefs(userId, phone) {
  const all = { ...(prefsStore.get('prefs') || {}) };
  delete all[prefsKey(userId, phone)];
  prefsStore.set('prefs', all);
  return true;
}

export function allPrefs() {
  return prefsStore.get('prefs') || {};
}

export function prefsCount() {
  return Object.keys(allPrefs()).length;
}
