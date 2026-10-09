'use strict'
function normalizeJid(jid) {
  const raw = String(jid || '').trim()
  if (!raw) return ''
  if (/:\d+@/i.test(raw)) {
    const [left, server] = raw.split('@')
    return `${left.split(':')[0]}@${server}`
  }
  return raw
}
async function isAdmin(sock, chatId, senderId) {
  const result = { isGroup: String(chatId || '').endsWith('@g.us'), isSenderAdmin: false, isBotAdmin: false, admins: [], participants: [] }
  if (!result.isGroup || !sock?.groupMetadata) return result
  try {
    const md = await sock.groupMetadata(chatId)
    const parts = Array.isArray(md?.participants) ? md.participants : []
    result.participants = parts
    const admins = parts.filter((p) => ['admin', 'superadmin'].includes(String(p?.admin || '').toLowerCase())).map((p) => normalizeJid(p.id))
    result.admins = admins
    result.isSenderAdmin = admins.includes(normalizeJid(senderId))
    const botId = normalizeJid(sock?.user?.id || sock?.user?.jid || '')
    result.isBotAdmin = admins.includes(botId)
  } catch {}
  return result
}
module.exports = isAdmin
module.exports.isAdmin = isAdmin
