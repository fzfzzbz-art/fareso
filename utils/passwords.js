// utils/passwords.js — ★ v3.9: كلمة مرور فريدة وخاصة لكل رقم مربوط
// ─────────────────────────────────────────────────────────────────────────────
// الهدف: حماية موقع السيرفرات (Dashboard) بحيث يكون لكل مستخدم/رقم مربوط
// كلمة مرور خاصة به، ويُوجَّه عند الدخول بها حصرياً إلى لوحة التحكم الخاصة
// برقمه المربوط فقط (Scope) — دون رؤية أرقام المستخدمين الآخرين.
//
// • يولّد البوت كلمة المرور عند طلب المستخدم (زر «🔑 كلمة مرور رقمي»)
//   أو عند أمر المطور /genpass، وتُحفظ في data/dashboard-passwords.json.
// • تخزين النص الصريح مطلوب لأن البوت يعيد إرسال نفس كلمة المرور للمستخدم
//   عند الطلب (نفس أسلوب تخزين كلمة مرور اللوحة العامة في settings.json).
// • عند تسجيل الدخول بالموقع: تُفحص كلمة مرور المدير أولاً، ثم كلمات مرور
//   الأرقام — وإن طُابقت، يُصدَر توكن مقيّد بنطاق الرقم (scoped token).
// ─────────────────────────────────────────────────────────────────────────────
import crypto from 'node:crypto';
import { JsonStore } from './store.js';
import config from '../config.js';

export const passwordsStore = new JsonStore(config.passwordsFile, { phones: {} });

const digitsOf = (phone) => String(phone || '').replace(/\D/g, '');

/** أبجدية توليد واضحة (بلا حروف متشابهة o/0 و i/1) */
const ALPHABET = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789';

function generatePassword(len = 10) {
  const bytes = crypto.randomBytes(len * 2);
  let out = '';
  for (let i = 0; i < len; i += 1) out += ALPHABET[bytes[i] % ALPHABET.length];
  // ضمان وجود رقم وحرف كبير على الأقل
  if (!/\d/.test(out)) out = out.slice(0, -1) + String(bytes[len] % 10);
  if (!/[A-Z]/.test(out)) out = 'K' + out.slice(1);
  return out;
}

/** سجل رقم معيّن */
export function getPhonePasswordRecord(phone) {
  const phones = passwordsStore.get('phones') || {};
  return phones[digitsOf(phone)] || null;
}

/** إحضار كلمة مرور رقم — ويولّدها تلقائياً إن لم توجد بعد */
export function ensurePhonePassword(phone) {
  const key = digitsOf(phone);
  if (!key) return { ok: false, error: 'رقم غير صالح.' };
  const phones = { ...(passwordsStore.get('phones') || {}) };
  if (phones[key]?.password) {
    return { ok: true, password: phones[key].password, created: false, record: phones[key] };
  }
  const password = generatePassword(10);
  phones[key] = { password, createdAt: Date.now(), updatedAt: Date.now() };
  passwordsStore.set('phones', phones);
  return { ok: true, password, created: true, record: phones[key] };
}

/** توليد كلمة مرور جديدة (تُبطل القديمة) */
export function regeneratePhonePassword(phone) {
  const key = digitsOf(phone);
  if (!key) return { ok: false, error: 'رقم غير صالح.' };
  const phones = { ...(passwordsStore.get('phones') || {}) };
  const password = generatePassword(10);
  phones[key] = {
    password,
    createdAt: phones[key]?.createdAt || Date.now(),
    updatedAt: Date.now()
  };
  passwordsStore.set('phones', phones);
  return { ok: true, password, record: phones[key] };
}

/** تعيين كلمة مرور يدوياً من لوحة المدير (اختياري) */
export function setPhonePasswordManual(phone, password) {
  const key = digitsOf(phone);
  const pass = String(password || '').trim();
  if (!key) return { ok: false, error: 'رقم غير صالح.' };
  if (pass.length < 6) return { ok: false, error: 'كلمة المرور يجب أن تكون 6 أحرف على الأقل.' };
  const phones = { ...(passwordsStore.get('phones') || {}) };
  phones[key] = {
    password: pass,
    createdAt: phones[key]?.createdAt || Date.now(),
    updatedAt: Date.now(),
    manual: true
  };
  passwordsStore.set('phones', phones);
  return { ok: true, password: pass, record: phones[key] };
}

/** البحث عن الرقم صاحب كلمة المرور هذه (لشاشة الدخول) */
export function findPhoneByPassword(pass) {
  const p = String(pass || '');
  if (!p) return null;
  const phones = passwordsStore.get('phones') || {};
  for (const [phone, rec] of Object.entries(phones)) {
    if (rec?.password && String(rec.password) === p) return phone;
  }
  return null;
}

/** التحقق من كلمة مرور رقم محدّد */
export function verifyPhonePassword(phone, pass) {
  const rec = getPhonePasswordRecord(phone);
  return !!rec && String(rec.password) === String(pass);
}

/** حذف كلمة مرور رقم (عند فك الربط نهائياً) */
export function dropPhonePassword(phone) {
  const key = digitsOf(phone);
  const phones = { ...(passwordsStore.get('phones') || {}) };
  if (!phones[key]) return false;
  delete phones[key];
  passwordsStore.set('phones', phones);
  return true;
}

/** قائمة الأرقام المسجّلة (للوحة المدير — تُخفى الأرقام حسب الحاجة) */
export function listPhonePasswords({ mask = false } = {}) {
  const phones = passwordsStore.get('phones') || {};
  return Object.entries(phones).map(([phone, rec]) => ({
    phone: mask ? `${phone.slice(0, 3)}****${phone.slice(-3)}` : phone,
    updatedAt: rec?.updatedAt || 0,
    hasPassword: !!rec?.password
  }));
}
