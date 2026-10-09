'use strict'

const fs = require('fs')
const path = require('path')
const { pathToFileURL } = require('url')

const PRIMARY_DIRS = [
  // النسخة المدمجة تحتوي على مسارات core الصحيحة؛ تُفهرس أولاً لتجنب
  // تظليلها بنسخ قديمة ذات imports نسبية مكسورة في commands_arabic/.
  path.join(__dirname, '..', 'silana-lite', 'commands'),
  path.join(__dirname, '..', 'commands'),
  path.join(__dirname, '..', 'commands_arabic'),
]

let cachedRegistry = null

function normalizeCommandKey(value) {
  return String(value == null ? '' : value)
    .toLowerCase()
    .replace(/[\u064B-\u0652\u0670]/g, '')
    .replace(/\u0640/g, '')
    .replace(/[\s\-_]+/g, '_')
    .replace(/[\u0623\u0625\u0622]/g, '\u0627')
    .replace(/\u0629/g, '\u0647')
    .replace(/\u0649/g, '\u064A')
    .trim()
}

const uniq = (values) => Array.from(new Set((values || []).filter(Boolean)))

function parseCommandField(source) {
  const out = []
  let match = source.match(/handler\.command\s*=\s*([\s\S]+?)(?:\nhandler\.|\n\/\/|\nexport|\n\s*\n\s*export|\n\s*\n\s*handler\.)/)
  if (match && match[1]) {
    const expr = match[1].trim().replace(/[,;]+$/g, '').trim()
    if (expr.startsWith('/') && expr !== '/') {
      const r = expr.match(/^\/(.+?)\/[gimsuy]*\s*$/)
      if (r) out.push(...r[1].split('|').map((s) => s.replace(/[\\^$()]/g, '').trim()).filter(Boolean))
    } else if (expr.startsWith('[')) {
      for (const s of expr.match(/[\'"`]([^\'"`]+)[\'"`]/g) || []) out.push(s.slice(1, -1))
    } else {
      const s = expr.replace(/[\'"`]/g, '').trim()
      if (s) out.push(s)
    }
  }
  const cp = source.match(/handler\.customPrefix\s*=\s*(\/[^/]+\/[gimsuy]*)/)
  if (cp) {
    const r = cp[1].match(/^\/(.+?)\/[gimsuy]*$/)
    if (r) out.push(...r[1].split('|').map((s) => s.replace(/[\\^$()]/g, '').trim()).filter(Boolean))
  }
  match = source.match(/(?:let|const|var)\s+handler\s*=\s*\{([\s\S]+?)\}\s*(?:as\s+PluginOption|;|$)/)
  if (match && match[1]) {
    const body = match[1]
    const cm = body.match(/command\s*:\s*([\'"`])([^\'"`]+)\1/)
    if (cm) out.push(cm[2])
    const reg = body.match(/command\s*:\s*(\/[^/]+\/[gimsuy]*)/)
    if (reg) {
      const r = reg[1].match(/^\/(.+?)\/[gimsuy]*$/)
      if (r) out.push(...r[1].split('|').map((s) => s.replace(/[\\^$()]/g, '').trim()).filter(Boolean))
    }
    const arr = body.match(/(?:command|aliases)\s*:\s*\[([^\]]+)\]/g) || []
    for (const item of arr) for (const s of item.match(/[\'"`]([^\'"`]+)[\'"`]/g) || []) out.push(s.slice(1, -1))
  }
  match = source.match(/module\.exports\s*=\s*([\s\S]+?)(?:;\s*$|$)/)
  if (match && match[1]) {
    const cm = match[1].match(/command\s*:\s*([\'"`])([^\'"`]+)\1/)
    if (cm) out.push(cm[2])
  }
  return uniq(out)
}

function recordEntry(map, fileName, fullPath, runtime, names) {
  let total = 0
  const fallback = [fileName.replace(/\.js$/, '')]
  for (const name of names.length ? names : fallback) {
    const key = normalizeCommandKey(name)
    if (!key) continue
    const candidate = { fileName, fullPath, runtime, key, handler: null, loadError: null }
    const existing = map.get(key)
    if (existing) {
      existing.alternatives = existing.alternatives || []
      if (!existing.alternatives.some((item) => item.fullPath === fullPath)) existing.alternatives.push(candidate)
      continue
    }
    map.set(key, candidate)
    total++
  }
  return total
}

function _loadInto(map, dir, runtime) {
  if (!fs.existsSync(dir)) return 0
  let total = 0
  for (const fileName of fs.readdirSync(dir).filter((name) => name.endsWith('.js'))) {
    const fullPath = path.join(dir, fileName)
    const source = fs.readFileSync(fullPath, 'utf8')
    total += recordEntry(map, fileName, fullPath, runtime, parseCommandField(source))
  }
  return total
}

async function loadManifest() {
  if (cachedRegistry) return cachedRegistry
  const map = new Map()
  let total = 0
  for (const dir of PRIMARY_DIRS) {
    const runtime = dir.endsWith(path.join('silana-lite', 'commands')) || dir.endsWith('commands_arabic') ? 'esm' : 'cjs'
    total += _loadInto(map, dir, runtime)
  }
  cachedRegistry = { map, size: map.size, total }
  return cachedRegistry
}

function selectExportedHandler(value, entry) {
  if (typeof value === 'function') return value
  if (!value || typeof value !== 'object') return null
  if (typeof value.run === 'function') return value.run
  if (value.handler && typeof value.handler === 'object' && typeof value.handler.run === 'function') return value.handler.run

  const functions = Object.entries(value).filter(([, candidate]) => typeof candidate === 'function')
  if (!functions.length) return null

  // بعض أوامر CJS القديمة تصدّر كائناً يحوي دالة الأمر مع دوال مساعدة.
  // نختار الاسم الأقرب لاسم الملف، ثم الأسماء المنتهية بـ Command/Handler، ثم أول دالة.
  const stem = String(entry?.fileName || '').replace(/\.js$/i, '').toLowerCase()
  const score = ([name]) => {
    const n = String(name).toLowerCase()
    let points = 0
    if (n === stem) points += 100
    if (n.includes(stem)) points += 40
    if (/(command|handler|start|run|execute|main)/i.test(name)) points += 20
    if (/(valid|country|state|config|helper|read|increment|toggle|alias)/i.test(name)) points -= 15
    return points
  }
  functions.sort((a, b) => score(b) - score(a))
  return functions[0][1]
}

async function loadHandler(entry) {
  if (!entry) return null
  if (entry.handler) return entry.handler
  const candidates = [entry, ...(entry.alternatives || [])]
  const failures = []
  for (const candidate of candidates) {
    if (candidate.handler) {
      entry.handler = candidate.handler
      return candidate.handler
    }
    try {
      let exported
      if (candidate.runtime === 'esm') {
        const mod = await import(pathToFileURL(candidate.fullPath).href + `?v=${fs.statSync(candidate.fullPath).mtimeMs}`)
        exported = mod.default || mod.handler || mod
      } else {
        delete require.cache[require.resolve(candidate.fullPath)]
        const mod = require(candidate.fullPath)
        exported = mod?.default || (typeof mod?.handler === 'function' ? mod.handler : mod)
      }
      candidate.handler = selectExportedHandler(exported, candidate)
      if (!candidate.handler) throw new TypeError(`لا توجد دالة تنفيذ قابلة للاستدعاء في ${candidate.fileName}`)
      entry.handler = candidate.handler
      entry.activePath = candidate.fullPath
      entry.loadError = null
      return candidate.handler
    } catch (error) {
      candidate.loadError = error
      failures.push(`${candidate.fullPath}: ${error?.message || error}`)
      console.error(`[commandLoader] failed to load ${candidate.fileName}:`, error?.message || error)
    }
  }
  entry.loadError = new Error(failures.join(' | ') || `تعذر تحميل ${entry.fileName}`)
  return null
}

function listCommands() {
  if (!cachedRegistry) return []
  const seen = new Set()
  const out = []
  for (const [key, entry] of cachedRegistry.map.entries()) {
    if (seen.has(entry.fileName)) continue
    seen.add(entry.fileName)
    out.push({ key, file: entry.fileName, runtime: entry.runtime })
  }
  return out
}

function matchCommand(registry, rawKey) {
  if (!registry?.map) return null
  const want = normalizeCommandKey(rawKey)
  return registry.map.get(want) || null
}

const DEFAULT_PREFIXES = ['.', '!', '#', '/']
function parseCommand(text, prefixes = DEFAULT_PREFIXES) {
  if (typeof text !== 'string') return null
  const full = text.replace(/[\u200e\u200f]/g, '').trim()
  for (const prefix of prefixes) {
    if (!prefix || !full.startsWith(prefix)) continue
    const rest = full.slice(prefix.length).trim()
    if (!rest) return null
    const [command, ...args] = rest.split(/\s+/)
    return { prefix, usedPrefix: prefix, command, args, text: args.join(' '), noPrefix: rest, full }
  }
  return null
}

async function attemptDispatch(text, prefixes = DEFAULT_PREFIXES) {
  const parsed = parseCommand(text, prefixes)
  if (!parsed) return null
  const registry = await loadManifest()
  return { parsed, entry: matchCommand(registry, parsed.command) }
}

async function buildMenuText() {
  const items = listCommands()
  return { count: items.length, text: [`📋 *قائمة الأوامر الكاملة (${items.length})*`, ...items.map((it, i) => `${i + 1}. ${it.file.replace(/\.js$/, '')}`)].join('\n') }
}

module.exports = {
  PRIMARY_DIRS,
  normalizeCommandKey,
  parseCommand,
  matchCommand,
  loadManifest,
  loadHandler,
  attemptDispatch,
  listCommands,
  buildMenuText,
  DEFAULT_PREFIXES,
}
