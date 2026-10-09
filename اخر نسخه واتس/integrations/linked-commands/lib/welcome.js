'use strict'
const { loadGroupData, saveGroupData } = require('./index')
async function handleWelcome(sock, chatId, message, matchText = '') {
  const value = String(matchText || '').trim()
  const data = loadGroupData()
  data.welcome = data.welcome || {}
  if (!value || /^(status|الحالة)$/i.test(value)) {
    const row = data.welcome[chatId]
    const text = row?.enabled ? `✅ الترحيب مفعل\nالرسالة: ${row.message || 'الافتراضية'}` : '❌ الترحيب متوقف'
    return sock.sendMessage(chatId, { text }, { quoted: message })
  }
  if (/^(on|تشغيل|enable)$/i.test(value)) data.welcome[chatId] = { enabled: true, message: data.welcome[chatId]?.message || '' }
  else if (/^(off|ايقاف|إيقاف|disable)$/i.test(value)) data.welcome[chatId] = { enabled: false, message: data.welcome[chatId]?.message || '' }
  else data.welcome[chatId] = { enabled: true, message: value }
  saveGroupData(data)
  return sock.sendMessage(chatId, { text: '✅ تم تحديث إعدادات الترحيب.' }, { quoted: message })
}
async function handleGoodbye(sock, chatId, message, matchText = '') {
  const value = String(matchText || '').trim()
  const data = loadGroupData()
  data.goodbye = data.goodbye || {}
  if (!value || /^(status|الحالة)$/i.test(value)) {
    const row = data.goodbye[chatId]
    const text = row?.enabled ? `✅ الوداع مفعل\nالرسالة: ${row.message || 'الافتراضية'}` : '❌ الوداع متوقف'
    return sock.sendMessage(chatId, { text }, { quoted: message })
  }
  if (/^(on|تشغيل|enable)$/i.test(value)) data.goodbye[chatId] = { enabled: true, message: data.goodbye[chatId]?.message || '' }
  else if (/^(off|ايقاف|إيقاف|disable)$/i.test(value)) data.goodbye[chatId] = { enabled: false, message: data.goodbye[chatId]?.message || '' }
  else data.goodbye[chatId] = { enabled: true, message: value }
  saveGroupData(data)
  return sock.sendMessage(chatId, { text: '✅ تم تحديث إعدادات الوداع.' }, { quoted: message })
}
module.exports = { handleWelcome, handleGoodbye }
