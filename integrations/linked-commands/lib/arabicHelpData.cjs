'use strict'

const labels = {
  ai: ['الذكاء الاصطناعي', 'طرح سؤال على الذكاء الاصطناعي'], alive: ['حالة البوت', 'التأكد من أن البوت يعمل'], anime: ['بحث الأنمي', 'البحث عن معلومات الأنمي'], antibadword: ['منع الكلمات', 'إدارة الكلمات الممنوعة'], anticall: ['منع الاتصالات', 'إدارة الاتصالات الواردة'], antidelete: ['منع الحذف', 'حفظ الرسائل المحذوفة'], antilink: ['منع الروابط', 'إدارة الروابط في المجموعة'], antitag: ['منع المنشن', 'منع الإشارة الجماعية'], attp: ['ملصق نصي', 'تحويل النص إلى ملصق'], autoread: ['القراءة التلقائية', 'إدارة القراءة التلقائية'], autostatus: ['الحالة التلقائية', 'إدارة التفاعل مع الحالات'], autotyping: ['الكتابة التلقائية', 'إظهار حالة الكتابة'], ban: ['حظر عضو', 'حظر مستخدم من المجموعة'], character: ['الشخصية', 'عرض معلومات الشخصية'], chatbot: ['المحادثة الآلية', 'تشغيل أو إيقاف الرد الآلي'], clear: ['تنظيف الرسائل', 'تنظيف الرسائل أو البيانات'], clearsession: ['تنظيف الجلسات', 'حذف الجلسات القديمة'], cleartmp: ['تنظيف المؤقت', 'حذف الملفات المؤقتة'], compliment: ['إطراء', 'إرسال إطراء عشوائي'], dare: ['تحدي', 'إرسال تحدي عشوائي'], delete: ['حذف', 'حذف رسالة'], demote: ['تنزيل مشرف', 'تنزيل المشرف إلى عضو'], eightball: ['الكرة السحرية', 'إجابة عشوائية على سؤال'], emojimix: ['دمج الإيموجي', 'دمج إيموجيين'], facebook: ['فيسبوك', 'تحميل رابط من فيسبوك'], fact: ['معلومة', 'إرسال معلومة عشوائية'], flirt: ['مغازلة', 'إرسال عبارة لطيفة'], gif: ['صورة متحركة', 'البحث عن صورة متحركة'], github: ['جيت هب', 'عرض معلومات مستودع'], goodnight: ['تصبح على خير', 'إرسال رسالة مسائية'], groupinfo: ['معلومات المجموعة', 'عرض معلومات المجموعة'], groupmanage: ['إدارة المجموعة', 'أدوات إدارة المجموعة'], hangman: ['الرجل المشنوق', 'بدء لعبة الرجل المشنوق'], hidetag: ['منشن مخفي', 'منشن الأعضاء دون إظهار أسمائهم'], igs: ['حالة إنستغرام', 'تحميل حالة إنستغرام'], imagine: ['تخيل صورة', 'إنشاء صورة بالذكاء الاصطناعي'], img_blur: ['تمويه الصورة', 'تمويه صورة'], instagram: ['إنستغرام', 'تحميل رابط من إنستغرام'], insult: ['مزحة', 'إرسال عبارة ساخرة'], joke: ['نكتة', 'إرسال نكتة عشوائية'], kick: ['طرد عضو', 'طرد مستخدم من المجموعة'], lyrics: ['كلمات الأغاني', 'البحث عن كلمات أغنية'], meme: ['ميم', 'إنشاء صورة ميم'], mention: ['منشن', 'منشن الأعضاء مع رسالة'], misc: ['أدوات متنوعة', 'أدوات الوسائط المتنوعة'], mute: ['كتم المجموعة', 'كتم المجموعة مؤقتاً'], news: ['الأخبار', 'عرض آخر الأخبار'], pair: ['ربط جهاز', 'إدارة الربط'], pies: ['فطائر', 'أمر ترفيهي'], ping: ['فحص السرعة', 'قياس سرعة استجابة البوت'], play: ['تشغيل صوت', 'تشغيل مقطع صوتي'], pmblocker: ['حظر الخاص', 'إدارة الرسائل الخاصة'], promote: ['ترقية مشرف', 'ترقية عضو إلى مشرف'], quote: ['اقتباس', 'إرسال اقتباس عشوائي'], remini: ['تحسين الصورة', 'تحسين جودة الصورة'], removebg: ['إزالة الخلفية', 'إزالة خلفية الصورة'], resetlink: ['إعادة الرابط', 'إعادة تعيين رابط المجموعة'], roseday: ['يوم الورد', 'أمر ترفيهي'], setpp: ['صورة المجموعة', 'تغيير صورة المجموعة'], settings: ['الإعدادات', 'عرض إعدادات البوت'], shayari: ['شعر', 'إرسال أبيات شعرية'], ship: ['التوافق', 'حساب نسبة التوافق'], simage: ['صورة ملصق', 'تحويل ملصق إلى صورة'], simp: ['إعجاب', 'حساب نسبة الإعجاب'], song: ['أغنية', 'تحميل أغنية'], sora: ['سورا', 'إنشاء فيديو وصفي'], spotify: ['سبوتيفاي', 'البحث في سبوتيفاي'], ss: ['لقطة موقع', 'تصوير موقع أو صفحة'], staff: ['المشرفون', 'عرض مشرفي المجموعة'], sticker: ['ملصق', 'تحويل صورة أو فيديو إلى ملصق'], stickercrop: ['قص الملصق', 'قص الملصق'], stickertelegram: ['ملصقات تيليجرام', 'تحميل ملصقات تيليجرام'], stupid: ['تفاعل ترفيهي', 'أمر ترفيهي'], sudo: ['صلاحيات المالك', 'إدارة صلاحيات المالك'], tag: ['منشن الأعضاء', 'منشن أعضاء المجموعة'], tagall: ['منشن الجميع', 'منشن جميع أعضاء المجموعة'], tagnotadmin: ['منشن غير المشرفين', 'منشن الأعضاء غير المشرفين'], take: ['بيانات الملصق', 'تعديل بيانات الملصق'], textmaker: ['صورة نصية', 'إنشاء صورة من نص'], tictactoe: ['إكس أو', 'بدء لعبة إكس أو'], tiktok: ['تيك توك', 'تحميل فيديو من تيك توك'], topmembers: ['أكثر الأعضاء نشاطاً', 'عرض إحصاءات الأعضاء'], translate: ['الترجمة', 'ترجمة نص'], trivia: ['أسئلة عامة', 'بدء مسابقة أسئلة'], truth: ['صراحة', 'إرسال سؤال صراحة'], tts: ['تحويل النص إلى صوت', 'تحويل النص إلى رسالة صوتية'], unban: ['فك الحظر', 'فك حظر مستخدم'], unmute: ['فك الكتم', 'إلغاء كتم المجموعة'], update: ['التحديث', 'فحص تحديثات المشروع'], url: ['الرابط', 'استخراج رابط من رسالة'], video: ['فيديو', 'تحميل فيديو'], viewonce: ['العرض مرة واحدة', 'فتح رسالة العرض مرة واحدة'], warn: ['تحذير', 'إعطاء تحذير لعضو'], warnings: ['التحذيرات', 'عرض تحذيرات العضو'], wasted: ['تأثير هزلي', 'إضافة تأثير للصورة'], weather: ['الطقس', 'معرفة حالة الطقس'], welcome: ['الترحيب', 'إدارة رسالة الترحيب'], ملكش: ['ملوكش', 'أمر ترفيهي عربي']
}
const groups = {
  '🌐 الأوامر العامة': ['alive', 'ping', 'help', 'joke', 'quote', 'fact', 'compliment', 'translate', 'weather', 'groupinfo', 'staff', 'url'],
  '🛡️ الإدارة والحماية': ['antibadword', 'anticall', 'antidelete', 'antilink', 'antitag', 'ban', 'clear', 'delete', 'demote', 'groupmanage', 'kick', 'mute', 'promote', 'resetlink', 'tagall', 'tagnotadmin', 'unban', 'unmute', 'warn', 'warnings'],
  '🎮 الألعاب والترفيه': ['character', 'dare', 'eightball', 'hangman', 'pies', 'ship', 'stupid', 'tictactoe', 'trivia', 'truth', 'ملكش', 'flirt', 'goodnight', 'roseday'],
  '🖼️ الصور والملصقات': ['attp', 'emojimix', 'gif', 'img_blur', 'imagine', 'meme', 'remini', 'removebg', 'setpp', 'simage', 'sticker', 'stickercrop', 'stickertelegram', 'take', 'textmaker', 'wasted'],
  '📥 التحميل والوسائط': ['facebook', 'igs', 'instagram', 'lyrics', 'play', 'song', 'spotify', 'ss', 'tiktok', 'video'],
  '🤖 الذكاء والإضافات': ['ai', 'anime', 'github', 'news', 'sora', 'topmembers'],
  '⚙️ إعدادات البوت': ['autoread', 'autostatus', 'autotyping', 'chatbot', 'clearsession', 'cleartmp', 'pair', 'pmblocker', 'settings', 'sudo', 'update', 'viewonce', 'welcome']
}
function makeSections(files) {
  const names = files.filter((name) => !['help', 'owner', 'المطور'].includes(name))
  const used = new Set()
  const sections = []
  for (const [title, wanted] of Object.entries(groups)) {
    const rows = names.filter((name) => wanted.includes(name)).map((name) => {
      used.add(name)
      const [label, description] = labels[name] || ['أمر إضافي', 'أمر عربي من المشروع الرئيسي']
      return { title: `🔹 ${label}`, description, id: `.${name}` }
    })
    if (rows.length) sections.push({ title, rows })
  }
  const extra = names.filter((name) => !used.has(name)).map((name) => {
    const [label, description] = labels[name] || ['أمر إضافي', 'أمر عربي من المشروع الرئيسي']
    return { title: `🔹 ${label}`, description, id: `.${name}` }
  })
  if (extra.length) sections.push({ title: '📚 أوامر إضافية', rows: extra })
  sections.push({ title: '📢 التواصل', rows: [{ title: '📢 تواصل واستفسار', description: 'رقم المطور ورابط قناة البوت', id: '.تواصل' }] })
  return sections
}
module.exports = { labels, groups, makeSections }
