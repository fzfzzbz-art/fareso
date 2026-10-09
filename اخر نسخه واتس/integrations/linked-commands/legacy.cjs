'use strict'
// ═══════════════════════════════════════════════════════════════════════════════
// integrations/linked-commands/legacy.cjs
// موزّع مجلد «commands» المرفق مع أوامر الرقم المربوط (أسلوب KnightBot - CJS)
// ───────────────────────────────────────────────────────────────────────────────
// • يحمّل كل ملف بـ CommonJS (كما في المجلد الأصلي: require('../settings') …)
// • يكتشف توقيع الدالة تلقائياً:
//     (sock, chatId, message)  → الأسلوب الأصلي
//     (sock, chatId)           → أوامر بلا رسالة
//     غير ذلك                  → (m, { conn, args, text … })
// • يعمل على أي رقم مربوط، وفشل ملف واحد لا يعطّل الباقي.
// ═══════════════════════════════════════════════════════════════════════════════
const fs = require('fs')
const path = require('path')
const Module = require('module')

const DIR = path.join(__dirname, 'source-commands')
const cache = new Map()

function compile(file) {
  if (cache.has(file)) return cache.get(file)
  try {
    const mod = new Module(file, module)
    mod.filename = file
    mod.paths = Module._nodeModulePaths(path.dirname(file))
    mod._compile(fs.readFileSync(file, 'utf8'), file)
    const value = mod.exports?.default || mod.exports
    cache.set(file, value)
    return value
  } catch (err) {
    cache.set(file, { __error: err })
    return cache.get(file)
  }
}

function files() {
  try { return fs.readdirSync(DIR).filter((f) => f.toLowerCase().endsWith('.js')).sort((a, b) => a.localeCompare(b, 'ar')) }
  catch { return [] }
}

function pickHandler(value) {
  if (typeof value === 'function') return value
  if (!value || typeof value !== 'object') return null
  const keys = Object.keys(value).filter((k) => typeof value[k] === 'function')
  if (!keys.length) return null
  const preferred =
    keys.find((k) => /command$/i.test(k)) ||
    keys.find((k) => /command|handler|run|main|start/i.test(k)) ||
    keys[0]
  return value[preferred]
}

function declaredAliases(value) {
  const out = []
  const list = value && !value.__error ? (value.command || value.help) : null
  const arr = Array.isArray(list) ? list : (list ? [list] : [])
  for (const v of arr) if (typeof v === 'string') out.push(v.replace(/^[.!#/]+/, '').trim())
  return out.filter(Boolean)
}

let namesCache = null
function names() {
  if (namesCache) return namesCache
  namesCache = files().map((file) => {
    const full = path.join(DIR, file)
    const value = compile(full)
    return {
      name: path.basename(file, '.js'),
      aliases: declaredAliases(value),
      file,
      path: full,
      error: value?.__error?.message || null
    }
  })
  return namesCache
}

function normalize(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .normalize('NFKC')
    .replace(/[\u064B-\u065F\u0670]/g, '')
    .replace(/\u0640/g, '')
    .replace(/[أإآٱ]/g, 'ا')
    .replace(/ة/g, 'ه')
    .replace(/[ىي]/g, 'ي')
    .replace(/[\s_-]+/g, '')
    .replace(/^\.+/, '')
}

function getText(raw) {
  let m = raw?.message || {}
  for (let depth = 0; depth < 5; depth += 1) {
    const wrapped = m.ephemeralMessage?.message || m.viewOnceMessage?.message || m.viewOnceMessageV2?.message || m.documentWithCaptionMessage?.message
    if (!wrapped) break
    m = wrapped
  }
  const native = m.interactiveResponseMessage?.nativeFlowResponseMessage
  if (native?.paramsJson) {
    try {
      const params = typeof native.paramsJson === 'string' ? JSON.parse(native.paramsJson) : native.paramsJson
      const selected = params.id || params.selected_id || params.selectedId || params.selectedRowId || params.buttonId || params.params?.id || params.params?.selected_id || params.params?.selectedRowId
      if (typeof selected === 'string' && selected.trim()) return selected.trim()
    } catch { /* تجاهل */ }
  }
  return String(
    m.conversation || m.extendedTextMessage?.text || m.imageMessage?.caption ||
    m.videoMessage?.caption || m.documentMessage?.caption ||
    m.buttonsResponseMessage?.selectedButtonId || m.listResponseMessage?.singleSelectReply?.selectedRowId || ''
  ).trim()
}

async function dispatch(session, raw) {
  if (!session?.sock) return false
  const text = getText(raw)
  if (!text.startsWith('.')) return false
  const parts = text.slice(1).trim().split(/\s+/).filter(Boolean)
  const requested = normalize(parts.shift() || '')
  if (!requested) return false
  const item = names().find(
    (x) => normalize(x.name) === requested || (x.aliases || []).some((a) => normalize(a) === requested)
  )
  if (!item) return false

  const value = compile(item.path)
  if (value?.__error) return false // ملف معطوب → نترك الأمر للسجل العام
  const fn = pickHandler(value)
  const chat = raw.key.remoteJid
  if (typeof fn !== 'function') {
    await session.sendText(chat, `⚠️ ملف الأمر ${item.file} لا يحتوي دالة تنفيذ.`, {}, { quoted: raw }).catch(() => {})
    return true
  }

  const sock = session.sock
  const argText = parts.join(' ')
  try {
    if (fn.length >= 3) await fn(sock, chat, raw, argText)
    else if (fn.length === 2) await fn(sock, chat)
    else {
      const m = {
        ...raw, chat, key: raw.key, message: raw.message,
        sender: raw.key?.participant || chat,
        text: argText, body: argText,
        isGroup: String(chat).endsWith('@g.us'),
        pushName: raw.pushName || ''
      }
      m.reply = (v, options = {}) =>
        sock.sendMessage(chat, typeof v === 'string' ? { text: v } : v, { quoted: raw, ...options })
      m.react = (emoji) => sock.sendMessage(chat, { react: { text: String(emoji), key: raw.key } })
      await fn(m, { conn: sock, sock, args: parts, text: argText, command: item.name, usedPrefix: '.', prefix: '.', session, chat, m })
    }
  } catch (err) {
    await session.sendText(chat, `❌ خطأ في أمر ${item.name}: ${err?.message || err}`, {}, { quoted: raw }).catch(() => {})
  }
  return true
}

async function loadAll() {
  const ok = []
  const fail = []
  for (const file of files()) {
    const value = compile(path.join(DIR, file))
    if (value?.__error) fail.push({ file, error: value.__error.message })
    else if (!pickHandler(value)) fail.push({ file, error: 'لا توجد دالة تنفيذ' })
    else ok.push(file)
  }
  return { ok, fail }
}

function reload() { cache.clear(); namesCache = null }

module.exports = { dispatch, names, loadAll, reload, DIR }
