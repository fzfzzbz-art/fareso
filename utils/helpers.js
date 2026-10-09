// utils/helpers.js — أدوات مساعدة عامة
import path from 'node:path';
import config from '../config.js';

// تحقّق صارم من رقم الهاتف: أرقام فقط، 6-15 خانة، مع رمز الدولة
export function normalizePhone(input) {
  if (!input) return { ok: false, error: 'لم يتم إدخال أي رقم.' };
  const raw = String(input).trim();
  // نسمح بـ + ومسافات وشرطات، ثم نزيلها
  let digits = raw.replace(/[\s\-().+]/g, '');
  if (!/^\d+$/.test(digits)) {
    return { ok: false, error: 'الرقم يحتوي على رموز غير مسموحة. استخدم أرقاماً فقط مع رمز الدولة.' };
  }
  if (digits.startsWith('00')) digits = digits.slice(2);
  if (digits.startsWith('0')) {
    return { ok: false, error: 'الرقم يبدأ بصفر. أدخل الرقم مع رمز الدولة بدون صفر (مثال: 9665xxxxxxxx).' };
  }
  if (digits.length < 6 || digits.length > 15) {
    return { ok: false, error: 'طول الرقم غير صحيح (يجب أن يكون بين 6 و 15 خانة).' };
  }
  return { ok: true, phone: digits };
}

export function sessionDirFor(userId, phone) {
  return path.join(config.sessionsDir, `${userId}_${phone}`);
}

export function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

export function randomDelay(min = config.whatsapp.reactDelayMinMs, max = config.whatsapp.reactDelayMaxMs) {
  const ms = Math.floor(Math.random() * (max - min + 1)) + min;
  return sleep(ms);
}

export function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function nowStamp() {
  return new Date().toLocaleString('ar-EG', { hour12: false });
}

// إخفاء جزء من الرقم في العروض
export function maskPhone(phone) {
  if (!phone || phone.length < 5) return phone || '';
  return `${phone.slice(0, 3)}****${phone.slice(-3)}`;
}

// jid واتساب من رقم: أرقام فقط + لاحقة s.whatsapp.net
export function jidOf(phone) {
  const digits = String(phone || '').replace(/\D/g, '');
  return digits ? `${digits}@s.whatsapp.net` : '';
}

// استخراج الرقم من jid
export function phoneOfJid(jid) {
  return String(jid || '').split('@')[0].replace(/\D/g, '');
}

// اسم ملف آمن من نص
export function safeFileName(name) {
  return String(name || 'file')
    .replace(/[^\w\u0600-\u06FF.\-]+/g, '_')
    .slice(0, 80);
}

// قطع نص طويل مع علامة
export function clip(text, n = 120) {
  const s = String(text || '');
  return s.length > n ? `${s.slice(0, n)}…` : s;
}
