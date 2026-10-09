'use strict'
const settings = require('../settings')
function normalize(value) { return String(value || '').replace(/\D/g, '') }
async function isOwner(senderId = '', sock = null, chatId = '') {
  if (!senderId && sock?.user?.id) senderId = sock.user.id
  const sender = normalize(senderId)
  const owners = new Set((settings.ownerNumbers || []).map(normalize).filter(Boolean))
  if (settings.ownerNumber) owners.add(normalize(settings.ownerNumber))
  try {
    if (sock?.user?.id) owners.add(normalize(sock.user.id))
    if (sock?.user?.jid) owners.add(normalize(sock.user.jid))
  } catch {}
  return owners.has(sender)
}
module.exports = isOwner
module.exports.isOwner = isOwner
