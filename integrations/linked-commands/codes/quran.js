import axios from 'axios'

const SURAHS = [
  'الفاتحة','البقرة','آل عمران','النساء','المائدة','الأنعام','الأعراف','الأنفال','التوبة','يونس','هود','يوسف','الرعد','إبراهيم','الحجر','النحل','الإسراء','الكهف','مريم','طه','الأنبياء','الحج','المؤمنون','النور','الفرقان','الشعراء','النمل','القصص','العنكبوت','الروم','لقمان','السجدة','الأحزاب','سبأ','فاطر','يس','الصافات','ص','الزمر','غافر','فصلت','الشورى','الزخرف','الدخان','الجاثية','الأحقاف','محمد','الفتح','الحجرات','ق','الذاريات','الطور','النجم','القمر','الرحمن','الواقعة','الحديد','المجادلة','الحشر','الممتحنة','الصف','الجمعة','المنافقون','التغابن','الطلاق','التحريم','الملك','القلم','الحاقة','المعارج','نوح','الجن','المزمل','المدثر','القيامة','الإنسان','المرسلات','النبأ','النازعات','عبس','التكوير','الانفطار','المطففين','الانشقاق','البروج','الطارق','الأعلى','الغاشية','الفجر','البلد','الشمس','الليل','الضحى','الشرح','التين','العلق','القدر','البينة','الزلزلة','العاديات','القارعة','التكاثر','العصر','الهمزة','الفيل','قريش','الماعون','الكوثر','الكافرون','النصر','المسد','الإخلاص','الفلق','الناس'
]

function normalizeArabic(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[\u064B-\u065F\u0670]/g, '')
    .replace(/ـ/g, '')
    .replace(/[أإآٱ]/g, 'ا')
    .replace(/ة/g, 'ه')
    .replace(/ى/g, 'ي')
    .replace(/[^\u0621-\u063A\u0641-\u064A\u0660-\u0669\d\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function findSurah(query) {
  const raw = String(query || '').trim()
  if (!raw) return null
  const number = Number(raw)
  if (Number.isInteger(number) && number >= 1 && number <= 114) return { number, name: SURAHS[number - 1] }
  const q = normalizeArabic(raw).replace(/^(سوره|سور|القران|قران)\s*/u, '').trim()
  if (!q) return null
  const index = SURAHS.findIndex((name) => {
    const normalized = normalizeArabic(name)
    return normalized === q || normalized.includes(q) || q.includes(normalized)
  })
  return index >= 0 ? { number: index + 1, name: SURAHS[index] } : null
}

async function getRemoteSurahs() {
  try {
    const response = await axios.get('https://api.alquran.cloud/v1/surah', { timeout: 8000 })
    const data = response.data?.data
    if (Array.isArray(data) && data.length) return data.map((item) => ({ number: item.number, name: item.name, ayahs: item.numberOfAyahs }))
  } catch {}
  return SURAHS.map((name, index) => ({ number: index + 1, name }))
}

const handler = async (m, { conn, text, usedPrefix, command }) => {
  const query = String(text || '').trim()
  if (query.startsWith('تحميل|')) {
    const parts = query.split('|')
    const surah = findSurah(parts[1] || '')
    if (!surah) return m.reply(`❌ لم أجد السورة. الاستخدام: ${usedPrefix}${command} تحميل|رقم السورة`)
    await m.reply(`⏳ جاري تجهيز سورة ${surah.name} بصوت القارئ مشاري العفاسي...`)
    try {
      const audioUrl = `https://server8.mp3quran.net/afs/${String(surah.number).padStart(3, '0')}.mp3`
      await conn.sendMessage(m.chat, { audio: { url: audioUrl }, mimetype: 'audio/mpeg', ptt: false, fileName: `سورة_${surah.name}.mp3` }, { quoted: m })
      return m.reply(`✅ تم إرسال سورة ${surah.name}`)
    } catch (error) {
      return m.reply(`❌ تعذر إرسال السورة حالياً: ${error?.message || 'خطأ في الاتصال'}`)
    }
  }

  await m.react('🕋').catch(() => {})
  const surahs = await getRemoteSurahs()
  if (query) {
    const found = findSurah(query) || surahs.find((item) => normalizeArabic(item.name) === normalizeArabic(query.replace(/^(سوره|سور|القران|قران)\s*/u, '')) || String(item.number) === query)
    if (!found) return m.reply(`❌ لم أجد سورة بهذا الاسم. أرسل ${usedPrefix}${command} لعرض القائمة.`)
    return m.reply(`🕌 السورة: ${found.name}\n🔢 الرقم: ${found.number}\n\nلتحميلها أرسل:\n${usedPrefix}${command} تحميل|${found.number}`)
  }

  const lines = surahs.map((item) => `${item.number}. ${item.name}`)
  return m.reply(`قائمة سور القرآن الكريم\n\n${lines.join('\n')}\n\nللبحث: ${usedPrefix}${command} اسم السورة\nللتحميل: ${usedPrefix}${command} تحميل|رقم السورة`)
}

handler.help = ['قرآن', 'سورة']
handler.command = /^(قرآن|قران|سورة|سور|quran)$/i
handler.tags = ['قرآن']

export default handler
