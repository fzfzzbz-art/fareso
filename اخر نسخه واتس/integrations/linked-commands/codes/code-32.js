import ws from 'ws'

const handler = async (m, { conn, usedPrefix, command, args }) => {
  try {
    if (!args[0] && !m.quoted && (!m.mentionedJid || m.mentionedJid.length === 0)) {
      return m.reply(`⚠️ يرجى منشن رقم البوت أو الرد على رسالته.\nمثال: ${usedPrefix}${command} @0`)
    }

    if (!global.db) global.db = { data: {} }
    if (!global.db.data) global.db.data = {}
    if (!global.db.data.chats) global.db.data.chats = {}
    if (!global.db.data.chats[m.chat]) global.db.data.chats[m.chat] = {}
    const chat = global.db.data.chats[m.chat]

    let targetJid = ''
    if (m.mentionedJid && m.mentionedJid.length) targetJid = m.mentionedJid[0]
    else if (m.quoted?.sender) targetJid = m.quoted.sender
    else if (args[0]) {
      const cleanNum = String(args[0]).replace(/[^0-9]/g, '')
      targetJid = cleanNum ? `${cleanNum}@s.whatsapp.net` : ''
    }

    if (!targetJid) return m.reply('❌ لم يتم التعرف على رقم البوت.')
    const targetNum = targetJid.split('@')[0].replace(/:.*/, '')
    const allBots = [global.conn, ...(global.conns || [])].filter((c) => {
      if (!c?.user) return false
      return c.ws?.socket ? c.ws.socket.readyState !== ws.CLOSED : true
    })

    const selectedBot = allBots.find((c) => {
      const botJid = c.user?.jid || c.user?.id || ''
      const botLid = c.user?.lid || ''
      const botNum1 = botJid.split('@')[0].replace(/:.*/, '')
      const botNum2 = botLid.split('@')[0].replace(/:.*/, '')
      return botJid === targetJid || botLid === targetJid || botNum1 === targetNum || botNum2 === targetNum
    })

    if (!selectedBot) {
      return conn.reply(m.chat, `⚠️ هذا البوت ليس من نفس الجلسة.\nتأكد من أن البوت متصل، ثم استخدم ${usedPrefix}البوتات`, m)
    }

    const officialBotJid = selectedBot.user?.jid || selectedBot.user?.id || targetJid
    if (chat.primaryBot === officialBotJid) return conn.reply(m.chat, '⚠️ هذا البوت هو الرئيسي بالفعل.', m)

    chat.primaryBot = officialBotJid
    await conn.sendMessage(m.chat, {
      text: '✅ تم تعيين البوت كبوت رئيسي.\nالبوتات الأخرى لن ترد هنا.'
    }, { quoted: m })
  } catch (error) {
    console.error('خطأ في أمر تعيين البوت الرئيسي:', error)
    await m.reply(`❌ حدث خطأ أثناء تنفيذ الأمر: ${error?.message || 'خطأ غير معروف'}`)
  }
}

handler.help = ['تعيين_اساسي <منشن>']
handler.tags = ['إدارة']
handler.command = /^(تعيين_اساسي|بوت_اساسي)$/i
handler.group = true
handler.admin = true

export default handler
