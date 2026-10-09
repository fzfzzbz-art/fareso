// utils/autoReplies.js — ردود تلقائية نصية للخاص فقط لكل رقم مربوط
import config from '../config.js';
import { JsonStore } from './store.js';

export const autoRepliesStore = new JsonStore(config.autoRepliesFile, { phones: {} });
const digits = (v) => String(v || '').replace(/\D/g, '');

export function listAutoReplies(phone) {
  const key = digits(phone);
  const all = autoRepliesStore.get('phones') || {};
  const rows = Array.isArray(all[key]) ? all[key] : [];
  return rows
    .filter((r) => r && String(r.trigger || '').trim() && String(r.reply || '').trim())
    .map((r) => ({ trigger: String(r.trigger).trim(), reply: String(r.reply).trim() }));
}

export function replaceAutoReplies(phone, rows = []) {
  const key = digits(phone);
  if (!key) return { ok: false, error: 'رقم الهاتف مطلوب.' };
  const clean = [];
  for (const row of Array.isArray(rows) ? rows : []) {
    const trigger = String(row?.trigger || '').trim();
    const reply = String(row?.reply || '').trim();
    if (!trigger || !reply) continue;
    if (trigger.length > 200 || reply.length > 4000) return { ok: false, error: 'طول كلمة الرد أو نصه كبير.' };
    if (!clean.some((x) => x.trigger.toLocaleLowerCase() === trigger.toLocaleLowerCase())) clean.push({ trigger, reply });
  }
  const phones = { ...(autoRepliesStore.get('phones') || {}) };
  phones[key] = clean.slice(0, 500);
  autoRepliesStore.set('phones', phones);
  return { ok: true, phone: key, replies: phones[key] };
}

export function findAutoReply(phone, text) {
  const value = String(text || '').trim().toLocaleLowerCase();
  if (!value) return null;
  return listAutoReplies(phone).find((r) => r.trigger.toLocaleLowerCase() === value) || null;
}

export function parseAutoRepliesText(text) {
  return String(text || '').split(/\r?\n/).map((line) => {
    const i = line.indexOf('=');
    return i < 0 ? null : { trigger: line.slice(0, i).trim(), reply: line.slice(i + 1).trim() };
  }).filter(Boolean);
}
