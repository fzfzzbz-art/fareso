// utils/store.js — تخزين JSON دائم بكتابة آمنة (atomic write)
// نكتب على ملف مؤقت ثم نعيد تسميته، لتجنّب تلف الملف عند انقطاع الكهرباء/الكسر.
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import logger from './logger.js';
import config from '../config.js';

const writeLocks = new Map();

export class JsonStore {
  constructor(filePath, defaultValue = {}) {
    this.filePath = filePath;
    this.defaultValue = defaultValue;
    this.data = defaultValue;
    this._loaded = false;
  }

  // تحميل تلقائي عند أول وصول — يضمن أن أي مخزن يُقرأ من القرص فعلاً عند الإقلاع،
  // حتى لو نُسي استدعاء load() في نقطة التشغيل (كان السبب في ضياع الإعدادات والسيرفرات).
  _ensureLoaded() {
    if (!this._loaded) this.load();
  }

  load() {
    try {
      fs.mkdirSync(path.dirname(this.filePath), { recursive: true });
      if (fs.existsSync(this.filePath)) {
        const raw = fs.readFileSync(this.filePath, 'utf8');
        this.data = raw.trim() ? JSON.parse(raw) : structuredClone(this.defaultValue);
      } else {
        this.data = structuredClone(this.defaultValue);
        this.saveSync();
      }
    } catch (err) {
      logger.error({ err, file: this.filePath }, 'فشل تحميل ملف التخزين — سيتم نسخ احتياطي');
      try {
        if (fs.existsSync(this.filePath)) {
          fs.renameSync(this.filePath, `${this.filePath}.corrupt-${Date.now()}`);
        }
      } catch { /* تجاهل */ }
      this.data = structuredClone(this.defaultValue);
    }
    this._loaded = true;
    return this.data;
  }

  saveSync() {
    try {
      fs.mkdirSync(path.dirname(this.filePath), { recursive: true });
      const tmp = `${this.filePath}.${process.pid}.tmp`;
      fs.writeFileSync(tmp, JSON.stringify(this.data, null, 2), 'utf8');
      fs.renameSync(tmp, this.filePath);
    } catch (err) {
      logger.error({ err, file: this.filePath }, 'فشل حفظ ملف التخزين');
    }
  }

  // حفظ غير متزامن مع قفل لكل ملف لتسلسل الكتابات
  async save() {
    const prev = writeLocks.get(this.filePath) || Promise.resolve();
    const next = prev.then(async () => {
      try {
        await fsp.mkdir(path.dirname(this.filePath), { recursive: true });
        const tmp = `${this.filePath}.${process.pid}.tmp`;
        await fsp.writeFile(tmp, JSON.stringify(this.data, null, 2), 'utf8');
        await fsp.rename(tmp, this.filePath);
      } catch (err) {
        logger.error({ err, file: this.filePath }, 'فشل حفظ ملف التخزين (async)');
      }
    });
    writeLocks.set(this.filePath, next);
    return next;
  }

  get(key) { this._ensureLoaded(); return this.data[key]; }
  set(key, value) { this._ensureLoaded(); this.data[key] = value; return this.save(); }
  delete(key) { this._ensureLoaded(); delete this.data[key]; return this.save(); }
  has(key) { this._ensureLoaded(); return Object.prototype.hasOwnProperty.call(this.data, key); }
  all() { this._ensureLoaded(); return this.data; }
}

// ─────────── مخزن بيانات مستخدمي تيليجرام ───────────
export const usersStore = new JsonStore(
  config.usersFile || path.join(config.dataDir, 'users.json'),
  {}
);

// ─────────── مخزن الإعدادات (نص /start، تفعيل الأوامر الداخلية…) ───────────
export const settingsStore = new JsonStore(config.settingsFile, {});

// ─────────── سجل السيرفرات (على السيرفر الرئيسي) ───────────
// الشكل: { servers: { <name>: { name, url, maxSessions, alive, sessionCount, lastSeen, isLocal } } }
export const serversStore = new JsonStore(config.serversFile, { servers: {} });

// بادئة مفاتيح المستخدمين داخل التخزين
export const userKey = (id) => `u_${id}`;

export function getUser(id) {
  return usersStore.get(userKey(id)) || null;
}

export function ensureUser(id, defaults = {}) {
  const key = userKey(id);
  let user = usersStore.get(key);
  if (!user) {
    user = {
      id,
      createdAt: Date.now(),
      statusEmoji: null,
      numbers: [],       // [{ phone, server, sessionDir, linkedAt }]
      activePhone: null,
      ...defaults
    };
    usersStore.set(key, user);
  }
  return user;
}

export function updateUser(id, patch = {}) {
  const user = ensureUser(id);
  const updated = { ...user, ...patch, updatedAt: Date.now() };
  usersStore.set(userKey(id), updated);
  return updated;
}

// ─────────── الإعدادات العامة ───────────
export function getSettings() {
  return settingsStore.all();
}

export function getStartText() {
  return settingsStore.get('startText') || null;
}

export function setStartText(text) {
  settingsStore.set('startText', String(text || '').trim());
}

// تفعيل/تعطيل الأوامر الداخلية لكل الأرقام (عبر المطور)
export function commandsEnabled() {
  return settingsStore.get('waCommandsEnabled') !== false;
}

export function setCommandsEnabled(on) {
  settingsStore.set('waCommandsEnabled', !!on);
}

// ─────────── قنوات الاشتراك الإجباري (تيليجرام) ───────────
// الشكل: [ { id, title, username, link, addedAt } ]
export function getSubChannels() {
  return settingsStore.get('subChannels') || [];
}

export function addSubChannel(entry) {
  const list = getSubChannels();
  if (!list.find((c) => String(c.id) === String(entry.id))) list.push(entry);
  settingsStore.set('subChannels', list);
  return list;
}

export function removeSubChannel(idOrUsername) {
  const key = String(idOrUsername || '').replace(/^@/, '').trim();
  const list = getSubChannels();
  const next = list.filter(
    (c) => String(c.id) !== key && String(c.username || '').toLowerCase() !== key.toLowerCase()
  );
  settingsStore.set('subChannels', next);
  return { removed: next.length < list.length, list: next };
}

export function clearSubChannels() {
  settingsStore.set('subChannels', []);
}

// ─────────── المستخدمون المتحقّق من اشتراكهم ───────────
// الشكل: { <userId>: verifiedAt }
export function isSubVerified(userId) {
  const m = settingsStore.get('subVerified') || {};
  return !!m[String(userId)];
}

export function setSubVerified(userId) {
  const m = settingsStore.get('subVerified') || {};
  m[String(userId)] = Date.now();
  settingsStore.set('subVerified', m);
}

export function clearSubVerified(userId) {
  const m = settingsStore.get('subVerified') || {};
  delete m[String(userId)];
  settingsStore.set('subVerified', m);
}

// ─────────── الحظر (يمنع المستخدم من استخدام البوت) ───────────
// الشكل: { <userId>: { at, reason } }
export function getBanned() {
  return settingsStore.get('banned') || {};
}

export function isBanned(userId) {
  return !!getBanned()[String(userId)];
}

export function banUser(userId, reason = '') {
  const m = { ...getBanned(), [String(userId)]: { at: Date.now(), reason: String(reason || '') } };
  settingsStore.set('banned', m);
  return m;
}

export function unbanUser(userId) {
  const m = { ...getBanned() };
  const had = !!m[String(userId)];
  delete m[String(userId)];
  settingsStore.set('banned', m);
  return had;
}

export function listBanned() {
  return Object.entries(getBanned()).map(([id, v]) => ({ id, at: v?.at || 0, reason: v?.reason || '' }));
}

// ─────────── وضع الصيانة ───────────
// الشكل: { on: boolean, message: string, since: number }
export function getMaintenance() {
  const m = settingsStore.get('maintenance') || {};
  return { on: !!m.on, message: m.message || '', since: m.since || 0 };
}

export function setMaintenance(on, message = '') {
  const cur = getMaintenance();
  const next = {
    on: !!on,
    message: on ? (String(message || '').trim() || cur.message || '🛠️ البوت تحت الصيانة حالياً، عد بعد قليل.') : '',
    since: on ? (cur.on ? cur.since : Date.now()) : 0
  };
  settingsStore.set('maintenance', next);
  return next;
}

// ─────────── محرّك الحالات (مشاهدة/أرشفة/تفاعل) ───────────
export function statusEngineEnabled() {
  return settingsStore.get('statusEngineEnabled') !== false;
}

export function setStatusEngineEnabled(on) {
  settingsStore.set('statusEngineEnabled', !!on);
  return !!on;
}
