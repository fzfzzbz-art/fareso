// أمر محادثة سمسمي — يعتمد الخدمة الخارجية عند توفرها، مع رد محلي احتياطي.
import axios from 'axios'

const clean = (value) => String(value || '').trim()

function localReply(input) {
  const text = clean(input).toLowerCase()
  if (/^(مرحبا|مرحباً|اهلا|أهلا|هلا|السلام عليكم|سلام)[!.؟\s]*$/u.test(text)) return 'أهلًا! كيف أقدر أساعدك؟'
  if (/كيف حالك|عامل ايه|شلونك|كيفك/u.test(text)) return 'أنا بخير، شكرًا لسؤالك! وأنت كيف حالك؟'
  if (/شكرا|شكرًا|مشكور|تسلم/u.test(text)) return 'العفو، هذا واجبي!'
  if (/اسمك|من انت|من أنت/u.test(text)) return 'أنا سمسمي، موجود للدردشة معك.'
  if (/احبك|أحبك/u.test(text)) return 'كلامك لطيف! وأنا سعيد بالدردشة معك.'
  return `فهمت عليك: «${clean(input).slice(0, 180)}» — قل لي أكثر، أنا أسمعك.`
}

async function askPrimary(text) {
  const { data } = await axios.get('https://engez.a7a.online/api/v1/ai/ai/simsimi', {
    params: { action: 'تكلم', message: text },
    timeout: 7000,
    headers: { accept: 'application/json', 'user-agent': '2B-WhatsApp-Bot/1.0' },
    validateStatus: (status) => status >= 200 && status < 500,
  })
  const reply = data?.response?.reply || data?.reply || data?.text || data?.message
  if ((data?.success === true || data?.status === true || typeof reply === 'string') && typeof reply === 'string' && reply.trim()) return reply.trim()
  throw new Error(`استجابة غير صالحة من خدمة سمسمي (HTTP ${data?.status || 'غير معروف'})`)
}

const handler = async (m, { text, prefix = '.', command = 'سمسمي' }) => {
  const input = clean(text)
  if (!input) return m.reply(`❌ *استخدام الأمر:*
${prefix}${command} <النص>

*مثال:*
${prefix}${command} كيف حالك؟`)

  await m.reply('⏳ جاري تجهيز الرد…')
  let reply
  try {
    reply = await askPrimary(input)
  } catch (error) {
    console.warn('[simsimi] تعذر الاتصال بالخدمة الخارجية، سيُستخدم الرد الاحتياطي:', error?.message || error)
    reply = localReply(input)
  }
  return m.reply(`🤖 *سمسمي:* ${reply}`)
}

handler.help = ['سمسمي <نص>', 'سمسم <نص>']
handler.tags = ['fun']
handler.command = /^(سمسم|سمسمي|simsimi)$/i

export default handler
