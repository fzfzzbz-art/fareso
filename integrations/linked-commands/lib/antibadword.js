'use strict'
const { loadGroupData, saveGroupData } = require('./index')
async function handleAntiBadwordCommand(sock, chatId, message, match = '') {
  const value = String(match || '').trim().toLowerCase()
  const data = loadGroupData()
  data.antibadword = data.antibadword || {}
  if (!value) {
    const row = data.antibadword[chatId]
    const text = row?.enabled ? `✅ منع السب مفعل (${row.action || 'delete'})` : '❌ منع السب متوقف'
    return sock.sendMessage(chatId, { text }, { quoted: message })
  }
  if (['on','تشغيل','enable'].includes(value)) data.antibadword[chatId] = { enabled: true, action: 'delete' }
  else if (['off','ايقاف','إيقاف','disable'].includes(value)) data.antibadword[chatId] = { enabled: false, action: 'delete' }
  else if (value.startsWith('set ')) data.antibadword[chatId] = { enabled: true, action: value.split(/\s+/)[1] || 'delete' }
  else data.antibadword[chatId] = { enabled: true, action: 'delete' }
  saveGroupData(data)
  return sock.sendMessage(chatId, { text: '✅ تم تحديث منع الكلمات السيئة.' }, { quoted: message })
}
module.exports = { handleAntiBadwordCommand }
