// utils/supportStore.js — ★ v3.15: مخزن تذاكر الدعم الفني (ملف JSON دائم على القرص)
// ─────────────────────────────────────────────────────────────────────────────
// البنية المحفوظة في data/support-tickets.json:
//   tickets   : { "<id>": { id, userJid, phone, name, text, at, status, devHeaderId, devMsgIds[] } }
//   byUser    : { "<أرقام المستخدم>": "<id>" }      ← آخر تذكرة لكل مستخدم
//   byDevMsg  : { "<معرّف رسالة المطور>": "<id>" }  ← لربط رد المطور بالاقتباس
//   awaiting  : { "<jid المستخدم>": <at> }          ← من ينتظر كتابة مشكلته الآن
//   counter   : عدد التذاكر منذ آخر تصفير (لتوليد رقم تذكرة قصير)
// ─────────────────────────────────────────────────────────────────────────────
import path from 'node:path';
import { JsonStore } from './store.js';
import config from '../config.js';

export const supportStore = new JsonStore(path.join(config.dataDir, 'support-tickets.json'), {
  tickets: {},
  byUser: {},
  byDevMsg: {},
  awaiting: {},
  counter: 0
});

const read = (key, fallback) => {
  const v = supportStore.get(key);
  return v && typeof v === 'object' ? v : fallback;
};

/** أرقام فقط من أي jid/رقم */
export function digitsOf(value) {
  return String(value || '').split('@')[0].split(':')[0].replace(/\D/g, '');
}

/** تحويل رقم إلى jid واتساب */
export function waJid(number) {
  const d = String(number || '').replace(/\D/g, '');
  return d ? `${d}@s.whatsapp.net` : '';
}

// ─────────── انتظار رسالة المستخدم ───────────
export function isAwaiting(userJid) {
  const awaiting = read('awaiting', {});
  return !!awaiting[String(userJid)];
}

export function setAwaiting(userJid, on = true) {
  const awaiting = read('awaiting', {});
  const key = String(userJid);
  if (on) awaiting[key] = Date.now();
  else delete awaiting[key];
  supportStore.set('awaiting', awaiting);
  return on;
}

export function clearAwaiting(userJid) {
  return setAwaiting(userJid, false);
}

// ─────────── إنشاء تذكرة ───────────
export function createTicket({ userJid, name, text, chatType = 'private' }) {
  const tickets = read('tickets', {});
  const counter = Number(supportStore.get('counter') || 0) + 1;
  const id = String(counter);
  const ticket = {
    id,
    userJid: String(userJid),
    phone: digitsOf(userJid),
    name: String(name || '').slice(0, 80),
    text: String(text || '').slice(0, 4000),
    chatType,
    at: Date.now(),
    status: 'open',
    devHeaderId: '',
    devMsgIds: []
  };
  tickets[id] = ticket;
  supportStore.set('tickets', tickets);
  supportStore.set('counter', counter);

  const byUser = read('byUser', {});
  byUser[ticket.phone] = id;
  supportStore.set('byUser', byUser);

  return ticket;
}

export function getTicket(id) {
  const tickets = read('tickets', {});
  return tickets[String(id)] || null;
}

export function getTicketIdForUser(userJid) {
  const byUser = read('byUser', {});
  return byUser[digitsOf(userJid)] || '';
}

/** ربط معرّف رسالة أرسلها البوت إلى المطور بالتذكرة (لكي يعمل الاقتباس) */
export function linkDevMessage(devMessageId, ticketId) {
  const key = String(devMessageId || '');
  if (!key || !ticketId) return;
  const byDevMsg = read('byDevMsg', {});
  byDevMsg[key] = String(ticketId);
  supportStore.set('byDevMsg', byDevMsg);

  const tickets = read('tickets', {});
  const t = tickets[String(ticketId)];
  if (t) {
    t.devMsgIds = Array.isArray(t.devMsgIds) ? t.devMsgIds : [];
    if (!t.devMsgIds.includes(key)) t.devMsgIds.push(key);
    if (t.devMsgIds.length > 30) t.devMsgIds = t.devMsgIds.slice(-30);
    tickets[String(ticketId)] = t;
    supportStore.set('tickets', tickets);
  }
}

export function getTicketIdByDevMessage(devMessageId) {
  const byDevMsg = read('byDevMsg', {});
  return byDevMsg[String(devMessageId || '')] || '';
}

export function setTicketHeader(ticketId, devHeaderId) {
  const tickets = read('tickets', {});
  const t = tickets[String(ticketId)];
  if (!t) return null;
  t.devHeaderId = String(devHeaderId || '');
  tickets[String(ticketId)] = t;
  supportStore.set('tickets', tickets);
  return t;
}

export function closeTicket(id) {
  const tickets = read('tickets', {});
  const t = tickets[String(id)];
  if (!t) return null;
  t.status = 'closed';
  tickets[String(id)] = t;
  supportStore.set('tickets', tickets);
  return t;
}

export function openTickets(limit = 20) {
  const tickets = read('tickets', {});
  return Object.values(tickets)
    .filter((t) => t && t.status !== 'closed')
    .sort((a, b) => (b.at || 0) - (a.at || 0))
    .slice(0, limit);
}

/** البحث عن تذكرة بالمعرّف أو برقم المستخدم */
export function findTicket(ref) {
  const raw = String(ref || '').trim();
  if (!raw) return null;
  if (getTicket(raw)) return getTicket(raw);
  const id = getTicketIdForUser(raw);
  return id ? getTicket(id) : null;
}

export default {
  supportStore,
  isAwaiting,
  setAwaiting,
  clearAwaiting,
  createTicket,
  getTicket,
  getTicketIdForUser,
  linkDevMessage,
  getTicketIdByDevMessage,
  setTicketHeader,
  closeTicket,
  openTickets,
  findTicket,
  waJid,
  digitsOf
};
