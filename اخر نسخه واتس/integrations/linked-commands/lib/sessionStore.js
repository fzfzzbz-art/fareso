// lib/sessionStore.js
// مدير تخزين محلي كامل - بديل mongodb/lowdb/nedb بدون اعتمادات ثقيلة.
// كل جلسة Baileys داخل مجلد دائم داخل المشروع:
//     ./sessions/<userId>/<number>/
// البيانات الوصفية (users, chats, stats) داخل ملفات JSON في ./data/
'use strict'
const fs = require('fs')
const path = require('path')

const PROJECT_ROOT = path.resolve(__dirname, '..')
const SESSIONS_ROOT = process.env.SILANA_SESSIONS_DIR || path.join(PROJECT_ROOT, 'sessions')
const DATA_ROOT = process.env.SILANA_DATA_DIR || path.join(PROJECT_ROOT, 'data')

fs.mkdirSync(SESSIONS_ROOT, { recursive: true })
fs.mkdirSync(DATA_ROOT, { recursive: true })

function safeRead(p, fallback) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')) } catch { return fallback }
}
function safeWrite(p, data) {
  fs.mkdirSync(path.dirname(p), { recursive: true })
  const tmp = p + '.tmp'
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2))
  fs.renameSync(tmp, p)
}

function sanitizeUserId(uid) { return String(uid == null ? 'anon' : uid).replace(/[^0-9a-zA-Z_\-]/g, '_') }
function sanitizeNumber(num) { return String(num == null ? '' : num).replace(/[^0-9]/g, '').replace(/^0+/, '') || 'unknown' }

function sessionDirFor(userId, number) {
  const dir = path.join(SESSIONS_ROOT, sanitizeUserId(userId), sanitizeNumber(number))
  fs.mkdirSync(dir, { recursive: true })
  return dir
}
function sessionCredPathFor(userId, number) { return path.join(sessionDirFor(userId, number), 'creds.json') }
function sessionHasAuth(userId, number) {
  const p = sessionCredPathFor(userId, number)
  return fs.existsSync(p)
}

function loadJson(name, fallback = {}) {
  return {
    name,
    path: path.join(DATA_ROOT, name + '.json'),
    data: safeRead(path.join(DATA_ROOT, name + '.json'), fallback)
  }
}
const fileDb = {
  users: loadJson('users'),
  chats: loadJson('chats'),
  settings: loadJson('settings'),
  stats: loadJson('stats'),
  sessions: loadJson('sessions_list'),
  saveAll() {
    for (const k of Object.keys(this)) {
      if (this[k] && this[k].path) safeWrite(this[k].path, this[k].data)
    }
  }
}

module.exports = {
  SESSIONS_ROOT, DATA_ROOT,
  sessionDirFor, sessionCredPathFor, sessionHasAuth,
  fileDb
}
