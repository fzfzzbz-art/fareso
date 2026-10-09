// lib/registryDispatch.js
// الموزِّع الموحَّد لجميع الأوامر داخل الرقم المربوط (يُحلُّ محل dispatchSilanaPlugin القديم).
// يدمج أوامر المجلد commands/ والأوامر العربية في commands_arabic/ في خريطة واحدة ويدير:
//  - مطابقة البادئة (موحَّدة من إعدادات الرقم + الاحتياطية)
//  - صلاحيات المالك
//  - قائمة الأوامر الكاملة
//  - التعامل مع الأخطاء وتمرير conn المناسب لكل أمر
'use strict'

const path = require('path')
const fs = require('fs')
const db = require('../db')
const config = require('../config')
const commandLoader = require('./commandLoader')
const { normalizeCommandKey } = commandLoader

// أوامر القائمة النظيفة
const MENU_COMMANDS = new Set([
  'الاوامر', 'اوامر', 'اوامر_خاص', 'القائمة', 'الائمة', 'منيو', 'قائمة',
  'menu', 'help', 'commands', 'list', 'cmd'
])

const DEFAULT_PREFIXES = ['.', '!', '#', '/']

function liveWebsiteUrl() {
  const fallback = String(config.WEBSITE_URL || process.env.WEBSITE_URL || '').trim().replace(/\/+$/, '')
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

// بناء قائمة البادئات من إعدادات الرقم + الاحتياطية
function buildPrefixList(waSession) {
  const settings = (db.getPhoneSettings(waSession.userId, waSession.number) || {})
  const raw = String(settings.prefix || '.').trim() || '.'
  const list = []
  if (raw.includes(',')) {
    for (const p of raw.split(',')) list.push(p.trim())
  } else {
    list.push(raw)
  }
  for (const p of DEFAULT_PREFIXES) if (!list.includes(p)) list.push(p)
  return list.filter(Boolean)
}

// استخراج نص الرسالة من أي بنية ممكنة داخل Baileys
function extractMessageText(rawMessage) {
  const m = rawMessage?.message
  if (!m) return typeof rawMessage?.text === 'string' ? rawMessage.text : ''
  const addCommandPrefix = (value) => {
    const text = String(value || '').trim()
    if (!text) return ''
    return /^[.!#/]/.test(text) ? text : `.${text}`
  }
  const selectionValues = [
    m.buttonsResponseMessage?.selectedButtonId,
    m.templateButtonReplyMessage?.selectedId,
    m.listResponseMessage?.singleSelectReply?.selectedRowId,
    m.interactiveResponseMessage?.listResponseMessage?.singleSelectReply?.selectedRowId,
  ]
  const nativeParams = m.interactiveResponseMessage?.nativeFlowResponseMessage?.paramsJson
  if (typeof nativeParams === 'string' && nativeParams.trim()) {
    try {
      const parsed = JSON.parse(nativeParams)
      selectionValues.unshift(parsed.id, parsed.selected_id, parsed.selectedId, parsed.selectedRowId, parsed.buttonId, parsed.params?.id, parsed.params?.selected_id)
    } catch {}
  }
  for (const value of selectionValues) {
    if (typeof value === 'string' && value.trim()) return addCommandPrefix(value)
  }
  const textValues = [
    m.conversation,
    m.extendedTextMessage?.text,
    m.imageMessage?.caption,
    m.videoMessage?.caption,
    m.documentMessage?.caption,
    m.buttonsResponseMessage?.selectedDisplayText,
    m.listResponseMessage?.title,
    m.templateButtonReplyMessage?.selectedDisplayText,
    m.interactiveResponseMessage?.listResponseMessage?.title,
    m.messageContextInfo?.quotedMessage?.conversation,
    m.reactionMessage?.text,
  ]
  for (const value of textValues) {
    if (typeof value === 'string' && value.trim()) return value.trim()
  }
  return ''
}

// تحويل رسالة Baileys الخام إلى m يشبه نموذج silana-lite ليقبلها معظم الأوامر
function adaptMessage(waSession, rawMessage) {
  const text = extractMessageText(rawMessage)
  const remoteJid = String(rawMessage?.key?.remoteJid || '').trim()
  const isGroup = remoteJid.endsWith('@g.us')
  const isStatus = remoteJid === 'status@broadcast'
  const senderJid = (() => {
    try {
      if (typeof waSession.extractSenderJid === 'function') return waSession.extractSenderJid(rawMessage)
    } catch {}
    if (isGroup) return rawMessage?.key?.participant || remoteJid
    return remoteJid
  })()
  const senderNumber = String(senderJid || '').replace(/\D/g, '')
  const raw = rawMessage?.message || {}
  const quotedContext = raw?.extendedTextMessage?.contextInfo || raw?.imageMessage?.contextInfo || raw?.videoMessage?.contextInfo || raw?.documentMessage?.contextInfo || {}
  const quotedPayload = quotedContext?.quotedMessage
  const quoted = quotedPayload ? {
    mtype: Object.keys(quotedPayload || {})[0] || '',
    msg: quotedPayload,
    key: {
      remoteJid,
      id: quotedContext.stanzaId || '',
      participant: quotedContext.participant || senderJid,
      fromMe: false,
    },
    message: quotedPayload,
    mimetype: Object.values(quotedPayload || {})[0]?.mimetype || '',
    download: async () => {
      const media = quotedPayload[Object.keys(quotedPayload || {})[0]]
      if (typeof waSession?.sock?.downloadContentFromMessage === 'function' && media) {
        const type = Object.keys(quotedPayload || {})[0].replace('Message', '').toLowerCase()
        const stream = await waSession.sock.downloadContentFromMessage(media, type)
        const chunks = []
        for await (const chunk of stream) chunks.push(chunk)
        return Buffer.concat(chunks)
      }
      if (typeof waSession?.sock?.downloadMediaMessage === 'function') {
        return waSession.sock.downloadMediaMessage({ key: { remoteJid, id: quotedContext.stanzaId || '', participant: quotedContext.participant || senderJid }, message: quotedPayload }, 'buffer')
      }
      throw new Error('تنزيل الرسالة المقتبس منها غير متاح')
    },
  } : null
  const adapted = {
    key: rawMessage?.key || {},
    message: rawMessage?.message || {},
    text,
    body: text,
    sender: senderJid,
    from: senderJid,
    chat: remoteJid,
    remoteJid,
    isGroup,
    fromMe: !!rawMessage?.key?.fromMe,
    pushName: String(rawMessage?.pushName || '').trim(),
    isStatus,
    quoted,
    raw: rawMessage,
  }
  adapted.reply = (value, options = {}) => waSession.sock.sendMessage(remoteJid, { text: withWebsiteFooter(value) }, { quoted: rawMessage, ...options })
  adapted.react = (emoji) => waSession.sock.sendMessage(remoteJid, { react: { text: String(emoji), key: rawMessage?.key } })
  adapted.download = async () => {
    if (typeof waSession.sock?.downloadMediaMessage === 'function') return waSession.sock.downloadMediaMessage(rawMessage, 'buffer')
    throw new Error('تنزيل الوسائط غير متاح')
  }
  return adapted
}

// قائمة أسطر وصف لكل أمر (مرتبطة بالعربي فقط)
const COMMAND_DESCRIPTIONS = require('./commandDescriptions')

// استخراج الكلمة العربية الأساسية للأمر لعرضها في القائمة
function primaryCommandOf(handler) {
  if (!handler || typeof handler !== 'function') return ''
  const candidates = []
  const collect = (c) => {
    if (!c) return
    if (c instanceof RegExp) {
      const src = c.source || ''
      const stripAnchors = src.replace(/^\^|\$$/g, '')
      candidates.push(...stripAnchors.split('|'))
    } else if (Array.isArray(c)) {
      for (const x of c) collect(x)
    } else {
      candidates.push(String(c))
    }
  }
  collect(handler.command)
  if (!candidates.length && Array.isArray(handler.help)) candidates.push(...handler.help)
  if (!candidates.length && typeof handler.help === 'string') candidates.push(handler.help)
  for (const c of candidates) {
    const raw = String(c || '').split('|')[0].trim().replace(/[\^$]/g, '')
    // اعتبر الكلمة صالحة إذا كانت عربية فقط (تتجنب المطابقة مع .menu أو .list الإنجليزية)
    if (/[\u0600-\u06FF]/.test(raw) && /^[\u0600-\u06FF_]+$/.test(raw)) return raw
  }
  return ''
}

async function buildCommandListText(waSession) {
  const prefixes = buildPrefixList(waSession)
  const mainPrefix = prefixes[0] || '.'
  const lines = []
  lines.push('╭─❖「 📜 قائمة الأوامر الكاملة 」─❖╮')
  lines.push(`│ البادئة: ${mainPrefix}`)
  lines.push('│ — جميع الأوامر تعمل في الخاص والرقم نفسه —')
  lines.push('│')
  const seen = new Set()
  const registry = await commandLoader.loadManifest()
  const orderedKeys = Array.from(registry.map.keys()).sort((a, b) => {
    if (a.includes('المطور')) return -1
    if (b.includes('المطور')) return 1
    return a.localeCompare(b, 'ar')
  })
  let idx = 1
  for (const key of orderedKeys) {
    const entry = registry.map.get(key)
    const handler = entry.handler
    const primary = primaryCommandOf(handler) || key
    if (seen.has(primary)) continue
    seen.add(primary)
    const desc = COMMAND_DESCRIPTIONS[primary] || COMMAND_DESCRIPTIONS[key] || 'أمر جاهز للاستخدام'
    lines.push(`│ ${String(idx).padStart(3, ' ')}› ${mainPrefix}${primary}  ⇽ ${desc}`)
    idx++
  }
  lines.push('╰─────────────────────────────────────╯')
  return lines.join('\n')
}

async function sendText(waSession, jid, text) {
  if (!waSession?.sock) return false
  try {
    await waSession.sock.sendMessage(jid, { text: withWebsiteFooter(text) })
    return true
  } catch (e) {
    console.error('[registryDispatch] send failed:', e?.message || e)
    return false
  }
}

async function sendCommandMenu(waSession, jid, text, prefix) {
  if (!waSession?.sock) return false
  const buttons = [
    ['📚 الأقسام الرئيسية', 'الأقسام'],
    ['🛡️ أوامر الأدمن', 'قسم_الأدمن'],
    ['🎮 أوامر الألعاب', 'قسم_الألعاب'],
    ['📥 أوامر التحميل', 'قسم_التحميل'],
    ['🛠️ أوامر الأدوات', 'قسم_الأدوات'],
    ['🤖 أوامر الذكاء', 'قسم_الذكاء'],
    ['🎨 أوامر الملصقات', 'قسم_الملصقات'],
    ['🖼️ أوامر الصور', 'قسم_الصور'],
    ['🎬 أوامر المانجا', 'قسم_المانجا'],
    ['🎉 أوامر الترفيه', 'قسم_الترفيه'],
  ].map(([displayText, command]) => ({
    buttonId: `${prefix}${command}`,
    buttonText: { displayText },
    type: 1,
  }))
  try {
    await waSession.sock.sendMessage(jid, {
      text,
      footer: '2B - اختر قسماً أو استخدم أي أمر مكتوب من القائمة',
      buttons,
      headerType: 1,
    })
    return true
  } catch (error) {
    console.error('[registryDispatch] menu button fallback:', error?.message || error)
    return sendText(waSession, jid, text)
  }
}

// الدالة الرئيسية — تُستدعى من onMessages داخل whatsapp.js قبل مسار الحماية
async function dispatchMessage(waSession, rawMessage) {
  const m = adaptMessage(waSession, rawMessage)

  if (m.isGroup && m.sender) {
    if (!global.groupData) global.groupData = {}
    if (!global.groupData[m.chat]) global.groupData[m.chat] = {}
    if (!global.groupData[m.chat][m.sender]) global.groupData[m.chat][m.sender] = { messagesSent: 0 }
    global.groupData[m.chat][m.sender].messagesSent += 1
  }

  if (!m.text) return false
  const prefixes = buildPrefixList(waSession)
  const attempt = await commandLoader.attemptDispatch(m.text, prefixes)
  if (!attempt) return false

  const { parsed } = attempt
  let entry = attempt.entry
  if (!entry) {
    const dynamicCommand = String(parsed.command || '')
    const dynamicFamilies = [
      { pattern: /^(تاريخ_(صحيح|خطأ)_)/i, files: ['تاريخ.js'] },
      { pattern: /^(ايموجي_(صحيح|خطأ)_)/i, files: ['اميوجي.js'] },
      { pattern: /^(جواب_(صحيح|خطأ)_)/i, files: ['سؤال.js'] },
      { pattern: /^(جوابي_)/i, files: ['احزر.js'] },
    ]
    const family = dynamicFamilies.find((item) => item.pattern.test(dynamicCommand))
    if (family) {
      const registry = await commandLoader.loadManifest()
      for (const candidate of registry.map.values()) {
        if (!family.files.includes(candidate.fileName)) continue
        const candidateHandler = await commandLoader.loadHandler(candidate)
        if (candidateHandler && (typeof candidateHandler.before === 'function' || family.files.includes('احزر.js'))) {
          entry = candidate
          break
        }
      }
    }
  }
  if (!entry) return false
  const sock = waSession.sock

  // يمر أمر .الاوامر إلى ملفه التفاعلي الفعلي؛ لا نحوله إلى نص قديم.

  const handler = await commandLoader.loadHandler(entry)
  if (!handler || typeof handler !== 'function') {
    await sendText(waSession, m.chat, '❌ تعذر تحميل هذا الأمر حالياً.')
    return true
  }
  if (!sock) return true // تم العثور على الأمر لكن لا يوجد اتصال لإرساله

  // تهيئة سياق مشترك للأوامر القديمة التي تعتمد على global.db.data.
  // هذا يمنع سقوط الألعاب عند تشغيلها من الرقم المربوط حتى لو لم تُحمّل
  // نسخة Silana القديمة من قاعدة البيانات العامة.
  if (!global.db || typeof global.db !== 'object') global.db = {}
  if (!global.db.data || typeof global.db.data !== 'object') global.db.data = {}
  if (!global.db.data.users || typeof global.db.data.users !== 'object') global.db.data.users = {}
  if (!global.db.data.chats || typeof global.db.data.chats !== 'object') global.db.data.chats = {}
  if (!global.db.data.settings || typeof global.db.data.settings !== 'object') global.db.data.settings = {}

  // بناء conn وفق ما يتوقعه معظم أوامر silana-lite (تحتوي الإضافات الاختيارية)
  const conn = waSession.__silanaConn || (waSession.__silanaConn = {
    sock,
    ev: sock?.ev,
    user: { id: sock?.user?.id || '', jid: sock?.user?.id || '' },
    __userId: waSession.userId,
    __number: waSession.number,
    sendMessage: (jid, content, opts) => sock.sendMessage(jid, content, opts),
    relayMessage: (...args) => sock.relayMessage(...args),
    newsletterMetadata: (...args) => typeof sock.newsletterMetadata === 'function' ? sock.newsletterMetadata(...args) : Promise.resolve(null),
    waUploadToServer: sock?.waUploadToServer?.bind(sock),
    downloadM: async (message, type) => {
      if (typeof sock.downloadContentFromMessage !== 'function') throw new Error('تنزيل الوسائط غير متاح')
      const stream = await sock.downloadContentFromMessage(message, type)
      const chunks = []
      for await (const chunk of stream) chunks.push(chunk)
      return Buffer.concat(chunks)
    },
    sendButton: async (jid, text, footer, image, video, buttons, sections, quoted) => {
      const content = { text: String(text || '') }
      if (Array.isArray(buttons) && buttons.length) content.buttons = buttons.map(([displayText, id]) => ({ buttonId: id, buttonText: { displayText }, type: 1 }))
      return sock.sendMessage(jid, content, { quoted })
    },
    reply: (jid, text, quoted, opts) => sock.sendMessage(jid, {
      text: String(text),
      mentions: [...String(text || '').matchAll(/@([0-9]{5,16}|0)/g)].map(v => `${v[1]}@s.whatsapp.net`),
    }, { quoted, ...opts }),
    sendText: (jid, text, quoted, opts) => sock.sendMessage(jid, { text }, { quoted, ...opts }),
    decodeJid: (j) => String(j || ''),
    getName: async (jid) => String(jid || '').replace(/\D/g, ''),
    groupMetadata: async (jid) => {
      try { return await sock.groupMetadata(jid) } catch { return { id: jid, subject: '', participants: [] } }
    },
    profilePictureUrl: async (jid) => {
      try { return await sock.profilePictureUrl(jid, 'image') } catch { return '' }
    },
    parseMention: (text) => [...String(text || '').matchAll(/@([0-9]{5,16}|0)/g)].map(v => `${v[1]}@s.whatsapp.net`),
    pushMessage: async (msgs) => {
      for (const msg of (Array.isArray(msgs) ? msgs : [msgs])) {
        if (!msg?.key?.remoteJid) continue
      }
    },
    readMessages: async (keys) => { try { await sock.readMessages(keys) } catch {} },
    sendPresenceUpdate: async (type, jid) => { try { await sock.sendPresenceUpdate(type, jid) } catch {} },
    sendContact: async (jid, data, quoted) => {
      const list = (Array.isArray(data?.[0]) ? data : [data]).map(([number, name]) => ({
        displayName: name,
        vcard: `BEGIN:VCARD\nVERSION:3.0\nFN:${name}\nTEL;type=CELL;type=VOICE;waid=${String(number).replace(/\D/g,'')}:+${String(number).replace(/\D/g,'')}\nEND:VCARD`,
      }))
      return sock.sendMessage(jid, { contacts: { displayName: list[0]?.displayName || 'Contact', contacts: list } }, { quoted })
    },
  })

  // تمرير سياق مشابه لـ silana-lite
  const extra = {
    match: null,
    usedPrefix: parsed.usedPrefix,
    noPrefix: parsed.text,
    _args: Array.isArray(parsed.args) ? parsed.args : [],
    args: Array.isArray(parsed.args) ? parsed.args : [],
    command: parsed.command,
    text: parsed.text,
    conn,
    groupMetadata: m.isGroup ? await conn.groupMetadata(m.chat).catch(() => ({})) : {},
    participants: m.isGroup ? (await conn.groupMetadata(m.chat).catch(() => ({})))?.participants || [] : [],
    user: { admin: 'superadmin' },
    bot: { admin: 'superadmin' },
    isROwner: true,
    isOwner: true,
    isRAdmin: true,
    isAdmin: true,
    isBotAdmin: true,
    isPrems: true,
    __dirname: path.join(__dirname, '..'),
    __filename: path.join(__dirname, '..', entry.fileName),
  }

  // إضافة m ككائن مُكيَّف يقبل .reply و .send
  const adaptedM = {
    ...m,
    isCommand: true,
    msg: m.message,
    quoted: m.quoted,
    download: async () => {
      if (typeof sock.downloadMediaMessage === 'function') return sock.downloadMediaMessage(m.raw, 'buffer')
      throw new Error('تنزيل الوسائط غير متاح')
    },
    reply: (text, opts) => sock.sendMessage(m.chat, {
      text: String(text),
      mentions: [...String(text || '').matchAll(/@([0-9]{5,16}|0)/g)].map(v => `${v[1]}@s.whatsapp.net`),
    }, { quoted: m.raw, ...opts }),
    send: (text, opts) => sock.sendMessage(m.chat, { text }, { quoted: m.raw, ...opts }),
    sendMessage: (jid, content, opts) => sock.sendMessage(jid, content, opts),
  }

  try {
    if (typeof handler.before === 'function') {
      const beforeResult = await handler.before.call(conn, adaptedM, extra)
      if (beforeResult) return true
    }
    if (entry.runtime === 'esm') {
      await handler.call(conn, adaptedM, extra)
    } else {
      const args = Array.isArray(parsed.args) ? parsed.args : []
      const text = parsed.text || ''
      // أغلب أوامر CJS القديمة تستخدم (sock, chatId, message)، بينما بعض
      // الملفات القديمة تستخدم النص أو match في المعامل الثالث/الرابع.
      const legacyArgs = (() => {
        const file = String(entry.fileName || '').toLowerCase()
        if (file === 'lyrics.js' || file === 'tts.js') return [sock, m.chat, text, rawMessage, ...args]
        if (file === 'weather.js') return [sock, m.chat, rawMessage, text, ...args]
        if (file === 'translate.js' || file === 'ss.js' || file === 'welcome.js') return [sock, m.chat, rawMessage, args, ...args]
        if (file === 'tictactoe.js') return [sock, m.chat, m.sender, text, ...args]
        return [sock, m.chat, rawMessage, args, text, m.sender]
      })()
      await handler(...legacyArgs)
    }
  } catch (e) {
    console.error('[registryDispatch]', entry.fileName, e?.message || e)
    try {
      await sock.sendMessage(m.chat, {
        text: `❌ حدث خطأ أثناء تنفيذ الأمر\n${e?.message || e}`,
      }, { quoted: m.raw })
    } catch {}
  }
  return true
}

module.exports = {
  dispatchMessage,
  buildCommandListText,
  extractMessageText,
  buildPrefixList,
  MENU_COMMANDS,
  PRIMARY_DIRS: commandLoader.PRIMARY_DIRS,
}
