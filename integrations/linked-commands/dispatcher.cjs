'use strict'

const fs = require('fs')
const path = require('path')
const Module = require('module')
const { pathToFileURL } = require('url')
const { menuLuffy } = require('./menu-image.cjs')
// بعض الإضافات لا تمرر timeout صراحة؛ ارفع المهلة العامة حتى لا تفشل
// التحميلات البطيئة برسالة Axios الافتراضية بعد 30 ثانية.
try {
  const axios = require('axios')
  axios.defaults.timeout = Math.max(Number(axios.defaults.timeout) || 0, 120000)
  axios.defaults.maxContentLength = Infinity
  axios.defaults.maxBodyLength = Infinity
} catch {}
const CODES_DIR = path.join(__dirname, 'codes')
const RESERVED = new Set(['.gitkeep'])

function liveWebsiteUrl() {
  const fallback = String(process.env.WEBSITE_URL || '').trim().replace(/\/+$/, '')
  try {
    const raw = fs.readFileSync(path.join(__dirname, '..', '.env'), 'utf8')
    const match = raw.match(/^\s*WEBSITE_URL\s*=\s*["']?([^"'\r\n#]+)["']?\s*$/m)
    return String(match?.[1] || fallback).trim().replace(/\/+$/, '') || fallback
  } catch { return fallback }
}

function withWebsiteFooter(text) {
  const body = String(text ?? '').trim()
  const url = liveWebsiteUrl()
  if (!body || !url || body.includes(url)) return body
  return `${body}\n\n🌐 الموقع: ${url}`
}
let manifestCache = null

const ARABIC_ALIASES = {
  'gif.js': ['جيف'],
  'ytmp3.js': ['صوت', 'يوتيوب_صوت'],
  'ytdl.js': ['يوتيوب_تحميل'],
  'youtube.js': ['يوتيوب'],
  'youtube-1.js': ['يوتيوب_بحث'],
  'ig-downloader.js': ['انستا_قديم', 'انستا_تحميل'],
  'instagram-dl.js': ['انستا', 'انستغرام', 'انستا_فيديو', 'ريل'],
  'instagram-search.js': ['انستا_بحث'],
  'pinterest-video.js': ['بنترست'],
  'pinterest-video-search.js': ['بنترست_بحث'],
  'facebook-sh-dl.js': ['فيسبوك'],
  'tiktok.js': ['تيك_توك'],
  'code-23.js': ['تيكتوك'],
  'code-9.js': ['تيكو', 'تيك', 'تيك_يوزر', 'تيك_معلومات', 'تيك-معلومات'],
  'terabox.js': ['تيرابوكس'],
  'wattpad.js': ['واتباد'],
  'moviebox.js': ['افلام'],
  'suno.js': ['اغاني'],
  'quran.js': ['قران', 'قرآن', 'سورة', 'سور'],
  'code-2.js': ['سمسم', 'سمسمي', 'سيمسيمي'],
  'quran-web.html': ['قران_ويب'],
  'anime.js': ['انمي'],
  'ai-notrack.js': ['ذكاء'],
  'gemini.js': ['جيميني'],
  'gpt.js': ['جي_بي_تي'],
  'deepseek.js': ['ديب_سيك'],
  'gmine-chat': ['جيمناي'],
  'img-genrator.js': ['توليد_صورة'],
  'ai-Generated-Pictures': ['صور_ذكاء'],
  'remvalai.js': ['ازالة_خلفية'],
  'upscale.js': ['تحسين_صورة'],
  '4x.js': ['تحسين_اربعة'],
  'upload.js': ['رفع'],
  'shazem.js': ['شازام'],
  'tts-anime.js': ['صوت_انمي'],
  'tts-elevenlab.js': ['صوت_ذكاء'],
  'group-Story': ['ستوري_قروب'],
  'group-Members': ['اعضاء_قروب'],
  'Add-Meta-in-Group': ['اضافة_ميتا'],
  'Warning': ['تحذير'],
  'Sound-Cloud': ['ساوند_كلاود'],
  'Made-Pictures': ['صور_ستايل'],
  'azura-manga.js': ['مانجا'],
  'team-x.js': ['مانهوا'],
  'all-dl.js': ['تحميل_شامل'],
  'code.js': ['ملصقات_بنترست'],
  'تحقيق-رقم.js': ['تحقيق-رقم', 'تحقق-رقم', 'رقم'],
  'روايات-واتباد.js': ['روايات', 'روايات-واتباد', 'واتباد-روايات'],
  'روايات-كتب2.js': ['روايات-كتب2', 'كتب-روايات'],
  'روايات-كتب.js': ['روايات-كتب', 'كتب'],
  'اعلان.js': ['اعلان', 'إعلان'],
  'ستوري-للقروب.js': ['ستوري-للقروب', 'ستوري_للقروب', 'ستوري'],
  'نشيد.js': ['نشيد', 'اناشيد'],
  'تحميل-ملصقات-تيليجرام.js': ['ملصقات', 'تحميل-ملصقات', 'تحميل-ملصقات-تيليجرام', 'ملصقات-تيليجرام'],
  'اضافة-ميتا-للجروب.js': ['اضافة-ميتا', 'اضافه-ميتا', 'ميتا', 'اضافة-ميتا-للجروب'],
}

function normalize(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[\u064B-\u065F\u0670]/g, '')
    .replace(/ـ/g, '')
    .replace(/[أإآٱ]/g, 'ا')
    .replace(/ة/g, 'ه')
    .replace(/ى/g, 'ي')
    .replace(/\.[^.]+$/i, '')
    .replace(/[^\p{L}\p{N}]+/gu, '_')
    .replace(/^_+|_+$/g, '')
}

function getText(message) {
  let m = message?.message || {}
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
    } catch {}
  }
  return String(m.conversation || m.extendedTextMessage?.text || m.imageMessage?.caption || m.videoMessage?.caption || m.documentMessage?.caption || m.buttonsResponseMessage?.selectedButtonId || m.buttonsResponseMessage?.selectedDisplayText || m.listResponseMessage?.singleSelectReply?.selectedRowId || m.listResponseMessage?.title || '').trim()
}

function getPhoneSettings(session) {
  try {
    const db = require('../db')
    return session ? (db.getPhoneSettings(session.userId, session.number) || {}) : {}
  } catch { return {} }
}

function prefixesFor(session) {
  const settings = getPhoneSettings(session)
  return Array.from(new Set([String(settings?.prefix || '.').trim() || '.', '.', '!', '#', '/']))
}

function toJid(value) {
  const digits = String(value || '').replace(/\D/g, '')
  return digits ? `${digits}@s.whatsapp.net` : ''
}

function cleanNumber(value) { return String(value || '').replace(/\D/g, '') }
function resolveCommandSender(session, rawMessage, chatId) {
  const candidates = [
    rawMessage?.key?.participantPn,
    rawMessage?.participantPn,
    rawMessage?.key?.senderPn,
    rawMessage?.senderPn,
    rawMessage?.key?.participant,
    rawMessage?.participant,
    rawMessage?.key?.participantAlt,
    rawMessage?.participantAlt,
    rawMessage?.key?.remoteJidAlt,
    rawMessage?.key?.remoteJid,
  ].filter(Boolean)
  const settings = getPhoneSettings(session)
  const allowed = [settings.ownerNumber, ...(Array.isArray(settings.ownerNumbers) ? settings.ownerNumbers : []), '967773987296', ...(Array.isArray(global.owner) ? global.owner : [])].map(cleanNumber).filter(Boolean)
  const ownerCandidate = candidates.find((candidate) => allowed.includes(cleanNumber(candidate)))
  if (ownerCandidate) return ownerCandidate
  return typeof session.extractSenderJid === 'function' ? session.extractSenderJid(rawMessage) : candidates[0] || chatId
}

function buildCommandConfig(session, prefix) {
  const settings = getPhoneSettings(session)
  const ownerNumbers = [settings.ownerNumber, ...(Array.isArray(settings.ownerNumbers) ? settings.ownerNumbers : [])]
    .map(toJid)
    .filter(Boolean)
  return {
    prefix,
    ownerNumber: ownerNumbers[0] || '',
    eliteNumbers: ownerNumbers,
    msgs: {
      elite: (command) => `❌ الأمر ${command || ''} متاح للمالك أو النخبة فقط.`,
      custom: {},
    },
  }
}

function parseNamespace(text, prefixes) {
  const value = String(text || '').trim()
  for (const prefix of prefixes) {
    if (!value.startsWith(prefix)) continue
    const parts = value.slice(prefix.length).trim().split(/\s+/).filter(Boolean)
    if (!parts.length) return null
    const first = String(parts[0] || '').toLowerCase()
    if (first === 'fares') {
      return { prefix, namespace: true, args: parts.slice(1) }
    }
    // الأوامر المحلية تعمل مباشرة: .نشيد، .يوتيوب، .تحقيق-رقم، إلخ.
    // إذا لم يطابق الأمر ملفاً داخل fates/codes فسيُعاد false ليعالجه الموزع العام.
    return { prefix, namespace: false, args: parts }
  }
  return null
}

function arabicNames(entry) {
  const stemName = String(entry.file || '').replace(/\.[^.]+$/, '')
  const explicit = ARABIC_ALIASES[entry.file] || ARABIC_ALIASES[stemName] || ARABIC_ALIASES[`${stemName}.js`] || []
  if (explicit.length) return explicit
  const stem = entry.file.replace(/\.[^.]+$/, '')
  if (/^code(?:-\d+)?$/i.test(stem)) return [`كود_${stem.replace(/\D/g, '') || 'عام'}`]
  if (/^\d+\.js$/.test(entry.file)) return [`كود_${stem}`]
  return [`كود_${normalize(stem)}`]
}

function buildManifest() {
  if (manifestCache) return manifestCache
  const map = new Map()
  const entries = []
  for (const file of fs.readdirSync(CODES_DIR)) {
    const fullPath = path.join(CODES_DIR, file)
    if (RESERVED.has(file) || file.startsWith('.') || fs.statSync(fullPath).isDirectory()) continue
    const entry = { file, fullPath, handler: null, loadError: null, aliases: arabicNames({ file }) }
    entries.push(entry)
    for (const alias of entry.aliases) map.set(normalize(alias), entry)
  }
  manifestCache = { map, entries }
  return manifestCache
}

function compileCommonJs(fullPath) {
  const source = fs.readFileSync(fullPath, 'utf8')
  const mod = new Module(fullPath, module)
  mod.filename = fullPath
  mod.paths = Module._nodeModulePaths(path.dirname(fullPath))
  mod._compile(source, fullPath)
  return mod.exports
}

async function loadHandler(entry) {
  if (entry.handler) return entry.handler
  try {
    const source = fs.readFileSync(entry.fullPath, 'utf8')
    let exported
    if (/module\.exports|exports\./.test(source)) {
      // بعض ملفات fares قديمة CommonJS داخل مجلد type=module؛ نحمّلها
      // بمترجم CommonJS المحلي حتى لا يظهر require/module is not defined.
      exported = compileCommonJs(entry.fullPath)
    } else if (/\bexport\s+(default|const|let|function|class)\b|^\s*import\s/m.test(source)) {
      exported = await import(pathToFileURL(entry.fullPath).href + `?v=${fs.statSync(entry.fullPath).mtimeMs}`)
    } else {
      throw new Error('الملف ليس أمراً JavaScript قابلاً للتشغيل')
    }
    const value = exported?.default || exported?.handler || exported
    if (typeof value === 'function') entry.handler = value
    else if (typeof value?.execute === 'function') entry.handler = (m, context) => value.execute(context.sock || context.conn, m, context.args || [], { cfg: context.cfg || context.session?.config || context.session?.cfg || {} })
    else if (typeof value?.run === 'function') entry.handler = value.run
    else if (value && typeof value === 'object') {
      const candidate = Object.entries(value).find(([name, fn]) => typeof fn === 'function' && /(command|handler|run|main|start|execute)/i.test(name))
      entry.handler = candidate?.[1] || Object.values(value).find((fn) => typeof fn === 'function')
    }
    if (typeof entry.handler !== 'function') throw new Error('لا توجد دالة تنفيذ قابلة للاستدعاء')
    return entry.handler
  } catch (error) {
    entry.loadError = error
    return null
  }
}

function commandList() {
  return buildManifest().entries.filter((e) => /\.(?:js|mjs)$/i.test(e.file)).sort((a, b) => a.file.localeCompare(b.file, 'ar'))
}

function declaredCommandNames(handler) {
  const values = []
  for (const declared of [handler?.command, handler?.help]) {
    if (Array.isArray(declared)) values.push(...declared)
    else if (declared) values.push(declared)
  }
  const names = []
  for (const value of values) {
    if (value instanceof RegExp) {
      const source = String(value.source || '')
        .replace(/^\^|\$$/g, '')
        .replace(/\\([()[\]{}])/g, '$1')
        .replace(/[()[\]]/g, '')
      names.push(...source.split('|'))
    } else if (typeof value === 'string') {
      names.push(value.replace(/^[.!#/]+/, '').trim().split(/\s+/)[0])
    }
  }
  return names.map((name) => String(name || '').trim()).filter((name) => /^[\p{L}\p{N}_-]+$/u.test(name))
}

function commandMatches(handler, requested, rawRequested) {
  const declared = handler?.command
  if (!declared) return false
  const values = Array.isArray(declared) ? declared : [declared]
  return values.some((value) => {
    if (value instanceof RegExp) {
      value.lastIndex = 0
      return value.test(rawRequested) || value.test(requested)
    }
    return normalize(value) === requested
  })
}

async function resolveEntry(manifest, requested, rawRequested) {
  const direct = manifest.map.get(requested)
  if (direct) return direct
  for (const entry of manifest.entries) {
    if (!/\.(?:js|mjs)$/i.test(entry.file)) continue
    const handler = await loadHandler(entry)
    if (handler && commandMatches(handler, requested, rawRequested)) {
      manifest.map.set(requested, entry)
      return entry
    }
  }
  return null
}

async function sendFaresHelp(session, rawMessage, chatId, prefix = '.') {
  const names = []
  for (const entry of commandList()) {
    const handler = await loadHandler(entry)
    const declared = declaredCommandNames(handler)
    const arabic = declared.filter((name) => /[\u0600-\u06ff]/u.test(name))
    names.push(...(arabic.length ? arabic : arabicNames(entry)))
  }
  const uniqueNames = Array.from(new Map(names.map((name) => [normalize(name), name])).values())
    .filter(Boolean)
    .sort((a, b) => normalize(a).localeCompare(normalize(b), 'ar'))
  const sections = []
  for (let index = 0; index < uniqueNames.length; index += 30) {
    const rows = uniqueNames.slice(index, index + 30).map((name) => ({
      title: `🔹 ${prefix}${name}`,
      description: 'اختيار الأمر لتشغيله مباشرة، ويمكن إرسال المعاملات بعده.',
      id: `${prefix}${name}`,
    }))
    sections.push({ title: `📚 أوامر fares ${Math.floor(index / 30) + 1}`, rows })
  }
  const body = [
    '❄️ 2B - YoRHa Unit No.2 Type B ❄️',
    '',
    `📚 قائمة أوامر fares المحلية (${uniqueNames.length} أمراً)`,
    'اختر أي أمر من القائمة وسيتم تشغيله مباشرة.',
    'يمكنك أيضاً كتابته يدوياً مثل: .نشيد أو .يوتيوب رابط',
  ].join('\n')
  try {
    const { ButtonV2 } = await import('./core/NIXCODE.js')
    const conn = session.__silanaConn || session.sock
    const builder = new ButtonV2(conn)
      .setBody(body)
      .setFooter('❄️ اختر الأمر المطلوب من القائمة ❄️')
      .setThumbnail(menuLuffy)
      .addRawButton({
        buttonText: { displayText: '📚 عرض أوامر fares' },
        buttonId: 'fares_commands',
        type: 1,
        nativeFlowInfo: { name: 'single_select', paramsJson: JSON.stringify({ title: 'أوامر fares', sections }) },
      })
      .addButton('📖 المساعدة العامة', `${prefix}help`)
    await builder.send(chatId, { quoted: rawMessage })
  } catch (error) {
    console.error('[fares] interactive menu failed:', error?.message || error)
    const lines = [body, '', ...uniqueNames.map((name, index) => `${index + 1}. ${prefix}${name}`), '', `🌐 الموقع: ${liveWebsiteUrl()}`]
    await session.sock.sendMessage(chatId, { text: lines.join('\n') }, { quoted: rawMessage })
  }
}

function createCompatibleMessage(session, raw, chatId, sender, text) {
  const m = { ...raw, chat: chatId, sender, from: sender, text, body: text, isGroup: String(chatId).endsWith('@g.us'), mentionedJid: raw?.message?.extendedTextMessage?.contextInfo?.mentionedJid || [] }
  m.quoted = raw?.quoted || null
  m.reply = (message, options = {}) => session.sock.sendMessage(chatId, { text: withWebsiteFooter(message) }, { quoted: raw, ...options })
  m.react = (emoji) => session.sock.sendMessage(chatId, { react: { text: String(emoji), key: raw.key } })
  m.download = async () => {
    if (typeof session.sock.downloadMediaMessage === 'function') return session.sock.downloadMediaMessage(raw, 'buffer')
    throw new Error('تنزيل الوسائط غير متاح')
  }
  return m
}

async function dispatch(session, rawMessage) {
  const text = getText(rawMessage)
  const parsed = parseNamespace(text, prefixesFor(session))
  if (!parsed) return false
  const chatId = rawMessage?.key?.remoteJid
  if (!chatId || !session?.sock) return true
  const rawRequested = String(parsed.args[0] || '').trim()
  const requested = normalize(rawRequested)
  const manifest = buildManifest()
  if (parsed.namespace && (!requested || ['مساعدة', 'قائمة', 'help', 'list'].includes(requested))) {
    await sendFaresHelp(session, rawMessage, chatId, parsed.prefix)
    return true
  }
  if (!requested) return false
  // استخدم alias أولاً ثم افحص handler.command/RegExp داخل الملفات فعلياً.
  // هذا يصلح أوامر مثل نشيد التي يكون ملفها code-26.js لا نشيد.js.
  const entry = await resolveEntry(manifest, requested, rawRequested)
  if (!entry) {
    // في الصيغة المباشرة لا نحتكر الرسالة؛ قد يكون الأمر تابعاً للموزع العام.
    if (!parsed.namespace) return false
    await session.sock.sendMessage(chatId, { text: withWebsiteFooter(`❌ الأمر «${rawRequested}» غير موجود داخل fates/codes. أرسل .fares لعرض القائمة المحلية.`) }, { quoted: rawMessage })
    return true
  }
  const handler = await loadHandler(entry)
  if (!handler) {
    await session.sock.sendMessage(chatId, { text: withWebsiteFooter(`❌ تعذر تشغيل الأمر ${arabicNames(entry)[0]}: ${entry.loadError?.message || 'اعتماد غير متوفر'}`) }, { quoted: rawMessage })
    return true
  }
  const args = parsed.args.slice(1)
  const commandText = args.join(' ')
  const sender = resolveCommandSender(session, rawMessage, chatId)
  const compatibleMessage = createCompatibleMessage(session, rawMessage, chatId, sender, commandText)
  const conn = session.__silanaConn || session.sock
  // تأكد من أن الغلاف القديم للجلسة يرث دوال Baileys قبل تشغيل handler.
  const bindSockMethod = (name) => {
    if (!conn[name] && typeof session.sock[name] === 'function') conn[name] = session.sock[name].bind(session.sock)
  }
  for (const name of ['groupParticipantsUpdate', 'groupMetadata', 'groupSettingUpdate', 'updateBlockStatus', 'updateProfilePicture', 'query', 'newsletterFollow', 'profilePictureUrl']) bindSockMethod(name)
  if (!conn.reply) conn.reply = (jid, value, quoted, options = {}) => session.sock.sendMessage(jid, { text: String(value ?? '') }, { quoted, ...options })
  if (!conn.sendText) conn.sendText = (jid, value, quoted) => session.sock.sendMessage(jid, { text: String(value ?? '') }, { quoted })
  for (const method of ['relayMessage', 'sendMessage', 'sendPresenceUpdate', 'prepareMessage', 'loadMessage']) {
    if (!conn[method] && typeof session.sock[method] === 'function') conn[method] = session.sock[method].bind(session.sock)
  }
  if (!conn.sendPresenceUpdate && session.sock.sendPresenceUpdate) conn.sendPresenceUpdate = session.sock.sendPresenceUpdate.bind(session.sock)
  const context = { conn, sock: session.sock, args, text: commandText, usedPrefix: parsed.prefix, prefix: parsed.prefix, command: rawRequested || requested, normalizedCommand: requested, m: compatibleMessage, message: compatibleMessage, session, sender, chatId, cfg: buildCommandConfig(session, parsed.prefix) }
  try {
    await handler(compatibleMessage, context)
  } catch (error) {
    await session.sock.sendMessage(chatId, { text: withWebsiteFooter(`❌ حدث خطأ أثناء تشغيل ${arabicNames(entry)[0]}: ${error?.message || 'خطأ غير معروف'}`) }, { quoted: rawMessage })
  }
  return true
}

module.exports = { dispatch, commandList, buildManifest, arabicNames }
