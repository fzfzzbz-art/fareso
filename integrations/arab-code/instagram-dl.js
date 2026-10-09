import fs from 'node:fs/promises'
import path from 'node:path'
import os from 'node:os'
import { fileURLToPath } from 'node:url'

const startDeco = `☽⚝ͫ͢❏ِꏍ🍡﴿ۦٕۛ۬٭ۦٕۛ۬❏ِ ﷽⎆☽⚝ͫ͢❏ِ🍡ꏍﭕ﴿ۦٕۛ۬٭ۦٕۛ۬❏ِ
╮ ⊰✫⊱─⊰✫⊱─⊰✫⊱╭`
const endDeco = `┘⊰✫⊱─⊰✫⊱─⊰✫⊱└
☽⚝ͫ͢❏ِꏍ🍡﴿ۦٕۛ۬٭ۦٕۛ۬❏ِ ﷽⎆☽⚝ͫ͢❏ِꏍﭕ🍡﴿ۦٕۛ۬٭ۦٕۛ۬❏ِ`
const MAX_BYTES = 100 * 1024 * 1024
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36'

function cookieHeader() {
  const inline = String(process.env.INSTAGRAM_COOKIE || process.env.IG_COOKIE || '').trim()
  if (inline) return inline
  return ''
}

async function loadCookie() {
  const inline = cookieHeader()
  if (inline) return inline
  const configured = String(process.env.INSTAGRAM_COOKIE_FILE || process.env.IG_COOKIE_FILE || '').trim()
  if (!configured) return ''
  const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../')
  const file = path.isAbsolute(configured) ? configured : path.resolve(projectRoot, configured)
  try {
    const text = await fs.readFile(file, 'utf8')
    // يدعم Cookie header العادي أو Netscape cookies.txt
    if (!text.includes('\t')) return text.trim()
    return text.split(/\r?\n/).filter(line => line && !line.startsWith('#')).map(line => {
      const p = line.split('\t')
      return p.length >= 7 ? `${p[5]}=${p[6]}` : ''
    }).filter(Boolean).join('; ')
  } catch { return '' }
}

function headers(cookie = '') {
  return {
    'user-agent': UA,
    accept: 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8',
    'accept-language': 'ar,en-US;q=0.9,en;q=0.8',
    'x-ig-app-id': '936619743392459',
    referer: 'https://www.instagram.com/',
    ...(cookie ? { cookie } : {})
  }
}

function postUrl(raw) {
  const match = String(raw || '').match(/https?:\/\/(?:www\.)?(?:instagram\.com|instagr\.am)\/[^\s<>'"]+/i)
  if (!match) return null
  return match[0].replace(/[)\]}.,،؛;!]+$/, '')
}

function addQuery(url, query) {
  const u = new URL(url)
  for (const [k, v] of Object.entries(query)) u.searchParams.set(k, v)
  return u.toString()
}

function parseEmbeddedJson(html) {
  const values = []
  const patterns = [
    /<script[^>]+type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi,
    /<script[^>]+id=["']__NEXT_DATA__["'][^>]*>([\s\S]*?)<\/script>/gi,
    /<script[^>]*>\s*window\._sharedData\s*=\s*([\s\S]*?);\s*<\/script>/gi
  ]
  for (const re of patterns) {
    let m
    while ((m = re.exec(html))) {
      try { values.push(JSON.parse(m[1])) } catch {}
    }
  }
  return values
}

function walkMedia(value, out = [], seen = new Set()) {
  if (!value || typeof value !== 'object' || seen.has(value)) return out
  seen.add(value)
  if (Array.isArray(value)) { for (const item of value) walkMedia(item, out, seen); return out }
  const push = (url, type = '') => {
    if (typeof url !== 'string' || !/^https?:\/\//i.test(url) || out.some(x => x.url === url)) return
    out.push({ url, type: String(type || '').toLowerCase() })
  }
  if (value.video_url) push(value.video_url, 'video')
  for (const v of value.video_versions || []) push(v?.url, 'video')
  for (const v of value.videoResources || []) push(v?.src || v?.url, 'video')
  for (const v of value.image_versions2?.candidates || []) push(v?.url, 'image')
  if (value.display_url) push(value.display_url, 'image')
  if (value.thumbnail_src) push(value.thumbnail_src, 'image')
  if (value.contentUrl) push(value.contentUrl, 'video')
  if (value.url && /\.(?:mp4|m3u8)(?:[?#]|$)/i.test(value.url)) push(value.url, 'video')
  for (const [key, child] of Object.entries(value)) {
    if (key !== 'url' || typeof child !== 'string') walkMedia(child, out, seen)
  }
  return out
}

function parseMeta(html) {
  const out = []
  const re = /<meta[^>]+(?:property|name)=["'](?:og:video(?::secure_url)?|twitter:player:stream|og:image)["'][^>]+content=["']([^"']+)["'][^>]*>/gi
  let m
  while ((m = re.exec(html))) out.push({ url: m[1].replace(/&amp;/g, '&'), type: /image/i.test(m[0]) ? 'image' : 'video' })
  return out
}

async function resolveMedia(url, cookie) {
  const requestHeaders = headers(cookie)
  const candidates = [
    addQuery(url, { __a: '1', __d: 'dis' }),
    addQuery(url, { __a: '1' }),
    `${url.replace(/\/$/, '')}/embed/`,
    `${url.replace(/\/$/, '')}/embed/captioned/`,
    url
  ]
  let lastStatus = 0
  let lastHtml = ''
  let networkError = ''
  for (const candidate of candidates) {
    let response
    try {
      response = await fetch(candidate, { headers: requestHeaders, redirect: 'follow', signal: AbortSignal.timeout(30000) })
    } catch (error) {
      networkError = `${error?.cause?.code || error?.message || error}`
      continue
    }
    lastStatus = response.status
    const text = await response.text()
    lastHtml = text
    if (!response.ok) continue
    let media = []
    try { media = walkMedia(JSON.parse(text)) } catch {}
    if (!media.length) for (const data of parseEmbeddedJson(text)) media.push(...walkMedia(data))
    if (!media.length) media = parseMeta(text)
    const unique = media.filter((item, i, arr) => arr.findIndex(x => x.url === item.url) === i)
    if (unique.length) return unique
  }
  const loginWall = /is_logged_out_user\"?\s*:\s*true|loginPage|Log in to Instagram|تسجيل الدخول/i.test(lastHtml)
  const explicitPrivate = /login_required|is_private|هذا الحساب خاص|This account is private/i.test(lastHtml)
  if (explicitPrivate) {
    throw new Error('هذا المحتوى خاص فعلاً أو يتطلب صلاحية متابعة. استخدم INSTAGRAM_COOKIE_FILE لحساب يملك صلاحية المشاهدة.')
  }
  if (loginWall) {
    throw new Error('إنستغرام حجب بيانات الرابط خلف صفحة تسجيل الدخول. قد يكون الرابط عاماً، لكن السيرفر يحتاج جلسة إنستغرام صالحة؛ ضع كوكيز حسابك في INSTAGRAM_COOKIE_FILE.')
  }
  if (networkError) throw new Error(`تعذر الاتصال بإنستغرام من السيرفر: ${networkError}`)
  throw new Error(`تعذر استخراج الوسائط من إنستغرام (HTTP ${lastStatus || 'غير معروف'}). تأكد من الرابط ثم حاول مرة أخرى.`)
}

async function downloadBuffer(url, cookie) {
  const response = await fetch(url, { headers: { ...headers(cookie), accept: '*/*' }, redirect: 'follow', signal: AbortSignal.timeout(90000) })
  if (!response.ok) throw new Error(`تعذر تنزيل ملف الوسائط (HTTP ${response.status})`)
  const length = Number(response.headers.get('content-length') || 0)
  if (length > MAX_BYTES) throw new Error('حجم الفيديو أكبر من 100MB')
  const buffer = Buffer.from(await response.arrayBuffer())
  if (buffer.length > MAX_BYTES) throw new Error('حجم الفيديو أكبر من 100MB')
  return { buffer, type: response.headers.get('content-type') || '' }
}

function isVideo(item, pageUrl) {
  return item.type.includes('video') || /\.(?:mp4|mov|webm)(?:[?#]|$)/i.test(item.url) || /\/(?:reel|tv)\//i.test(pageUrl)
}

const handler = async (m, { conn, args, usedPrefix, command }) => {
  const url = postUrl(args?.join(' '))
  if (!url) return conn.reply(m.chat, `${startDeco}\n\n*• أرسل رابط Reel أو Post من إنستغرام*\n\n*مثال:*\n${usedPrefix + command} https://www.instagram.com/reel/…/\n\n${endDeco}`, m)
  const cookie = await loadCookie()
  await conn.reply(m.chat, `${startDeco}\n\n*⏳ جاري استخراج الفيديو مباشرة من إنستغرام…*\n\n${endDeco}`, m)
  try {
    const media = await resolveMedia(url, cookie)
    const items = media.slice(0, 20)
    for (let index = 0; index < items.length; index += 1) {
      const item = items[index]
      const file = await downloadBuffer(item.url, cookie)
      const video = isVideo(item, url)
      await conn.sendMessage(m.chat, video
        ? { video: file.buffer, mimetype: file.type || 'video/mp4', caption: `${startDeco}\n\n🎬 *تم تحميل فيديو إنستغرام مباشرة*\n${endDeco}` }
        : { image: file.buffer, mimetype: file.type || 'image/jpeg', caption: `${startDeco}\n\n🖼️ *تم تحميل صورة إنستغرام مباشرة*\n${endDeco}` }, { quoted: m })
    }
  } catch (error) {
    await conn.reply(m.chat, `${startDeco}\n\n*❌ فشل تحميل إنستغرام:*\n${String(error?.message || error).slice(0, 700)}\n\n${endDeco}`, m)
  }
}

handler.help = ['انستا <رابط>', 'ريل <رابط>']
handler.tags = ['downloader']
handler.command = /^(انستا|انستغرام|insta|instagram|reel|ريل)$/i

export default handler
