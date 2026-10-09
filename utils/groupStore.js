// utils/groupStore.js — ★ v3.12: مخزن حالة الحماية لكل مجموعة (JSON دائم + ذاكرة فورية)
// ─────────────────────────────────────────────────────────────────────────────
// يحفظ لكل مجموعة (chatJid):
//   antilink        : off | delete | warn | kick
//   antiflood       : { on, max, windowSec, action }
//   locks           : { sticker, image, video, audio, document, poll, contact }
//   welcome/goodbye : نص الترحيب والوداع (فارغ = معطل)
//   whitelist       : أرقام مستثناة من الحماية
//   linkWhitelist   : روابط مسموح بها رغم مضاد الروابط
//   warnLimit       : عدد التحذيرات قبل الطرد (افتراضي 5)
//   warns           : { <jid>: { count, reasons[] } }
//   muted           : { <jid>: untilTs }
//   counts          : { <يوم>: { <jid>: n } }  ← عدّاد النشاط اليومي
//   locksExtras     : { name, desc, picture } ← حماية اسم/وصف/صورة المجموعة
//   protectAdds     : منع الإضافة من غير المشرفين
// ─────────────────────────────────────────────────────────────────────────────
import path from 'node:path';
import { JsonStore } from './store.js';
import config from '../config.js';

export const gpStore = new JsonStore(path.join(config.dataDir, 'group-protection.json'), { groups: {} });

const digitsOf = (v) => String(v || '').split('@')[0].split(':')[0].replace(/\D/g, '');

/** إعدادات مجموعة مع إنشائها عند الغياب */
export function gset(chatId) {
  const groups = gpStore.get('groups') || {};
  if (!groups[chatId]) {
    groups[chatId] = {
      antilink: 'off',
      antiflood: { on: false, max: 6, windowSec: 10, action: 'delete' },
      locks: { sticker: false, image: false, video: false, audio: false, document: false, poll: false, contact: false },
      welcome: '',
      goodbye: '',
      whitelist: [],
      linkWhitelist: [],
      warnLimit: 5,
      warns: {},
      muted: {},
      counts: {},
      locksExtras: { name: false, desc: false, picture: false },
      protectAdds: false
    };
    gpStore.set('groups', groups);
  }
  return groups[chatId];
}

/** تعديل إعدادات مجموعة وحفظ */
export function gpatch(chatId, patch = {}) {
  const groups = gpStore.get('groups') || {};
  const cur = gset(chatId);
  groups[chatId] = { ...cur, ...patch };
  gpStore.set('groups', groups);
  return groups[chatId];
}

export function allGroups() {
  return gpStore.get('groups') || {};
}

// ─────────── التحذيرات ───────────
export function addWarn(chatId, jid, reason = '') {
  const g = gset(chatId);
  const key = digitsOf(jid);
  const cur = g.warns[key] || { count: 0, reasons: [] };
  cur.count += 1;
  if (reason) cur.reasons.push(String(reason).slice(0, 120));
  g.warns[key] = cur;
  gpatch(chatId, { warns: g.warns });
  return cur;
}

export function getWarns(chatId, jid) {
  const g = gset(chatId);
  const key = digitsOf(jid);
  return g.warns[key] || { count: 0, reasons: [] };
}

export function resetWarns(chatId, jid = null) {
  const g = gset(chatId);
  if (jid) delete g.warns[digitsOf(jid)];
  else g.warns = {};
  gpatch(chatId, { warns: g.warns });
}

// ─────────── الكتم ───────────
export function mute(chatId, jid, minutes = 10) {
  const g = gset(chatId);
  g.muted[digitsOf(jid)] = Date.now() + Math.min(Math.max(minutes, 1), 60 * 24 * 7) * 60_000;
  gpatch(chatId, { muted: g.muted });
}

export function unmute(chatId, jid) {
  const g = gset(chatId);
  delete g.muted[digitsOf(jid)];
  gpatch(chatId, { muted: g.muted });
}

export function isMuted(chatId, jid) {
  const g = gset(chatId);
  const until = g.muted[digitsOf(jid)] || 0;
  return until > Date.now();
}

export function listMuted(chatId) {
  const g = gset(chatId);
  return Object.entries(g.muted)
    .filter(([, until]) => until > Date.now())
    .map(([d, until]) => ({ digits: d, until }));
}

// ─────────── عدّاد النشاط اليومي ───────────
const todayKey = () => new Date().toISOString().slice(0, 10);

export function bumpCount(chatId, jid) {
  const g = gset(chatId);
  const day = todayKey();
  if (!g.counts[day]) g.counts[day] = {};
  const key = digitsOf(jid);
  g.counts[day][key] = (g.counts[day][key] || 0) + 1;
  // نظافة: أبقِ آخر 3 أيام فقط
  const days = Object.keys(g.counts).sort();
  while (days.length > 3) delete g.counts[days.shift()];
  gpatch(chatId, { counts: g.counts });
  return g.counts[day][key];
}

export function topCounts(chatId, n = 10) {
  const g = gset(chatId);
  const day = todayKey();
  const map = g.counts[day] || {};
  return Object.entries(map)
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([digits, count]) => ({ digits, count }));
}

// ─────────── كاش بيانات المجموعة (للفحص الإداري السريع) ───────────
const metaCache = new Map(); // chatId -> { meta, at }

export function cacheMeta(chatId, meta) {
  metaCache.set(chatId, { meta, at: Date.now() });
}

export function getCachedMeta(chatId, maxAgeMs = 60_000) {
  const hit = metaCache.get(chatId);
  if (hit && Date.now() - hit.at < maxAgeMs) return hit.meta;
  return null;
}

/** هل المرسل مشرف؟ (بكاش 60 ثانية) */
export async function isAdmin(session, chatId, jid) {
  try {
    let meta = getCachedMeta(chatId);
    if (!meta) {
      meta = await session.sock.groupMetadata(chatId);
      cacheMeta(chatId, meta);
    }
    const d = digitsOf(jid);
    return meta.participants.some((p) => (p.admin === 'admin' || p.admin === 'superadmin') && digitsOf(p.id) === d);
  } catch {
    return false;
  }
}
