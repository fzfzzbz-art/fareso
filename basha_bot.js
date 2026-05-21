const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const http = require('http');

// --- [ الإعدادات - Environment Variables ] ---
const token = process.env.BOT_TOKEN; 
const channel_id = process.env.CHANNEL_ID || '@fz_z_Z';
const admin_wallet = 'THxRZPDScimXo7F3Cmsg2uyEp2saCF4Afc';

// الكوكيز التي زودتني بها (تستخدم للوصول للموقع وقراءة البيانات)
const COOKIES = `basha_iprn_vas_session=eyJpdiI6InJiZDFPZDVWZ1RJaXRpU3ZiRldEOUE9PSIsInZhbHVlIjoiOGh2L09xeEZmVHNRdzJCOFNYUTFvcGdTRVlvd3owdGQ1dDAxZFo0aG5PL0tEVHRtTkcvRWxPdGR6T3RqRDk0S3BxZkxQWkdWdnk3NjVpTkw1TEFGbnhhbHRGTXk5M05QTXpONUVtT1JQZ2RpT2NvWFNCQ0g0UEF5ZFFyUHJyc3MiLCJtYWMiOiJlOTBlMTdlMmRiYzllMDhlYzUyMTJjNWE2Zjk2ZjMxYmU1ZGYxZjJmZTg5NWZhNDhmMGEyNzQ1MmMwYjlmZDk0IiwidGFnIjoiIn0%3D; cf_clearance=Wcw_QXt5eEP9ij5Zlk_RZZhRMQGsZ4ILQhhKprApsds-1779385492-1.2.1.1-uwy2A9b0n0jBCQvuFQudtpC7wYMcUF.Tqpi2_1KTGD1RjipFpriGCQFpXQQbR0Jlg1JqdXThnl3e9RikXMbrqIXj1gOTl7APgYTAxEO4q0aG8bdt0m66KIVHUWw5YUvqob6PYVJOXrZZpz0pldAKDI6B0JRZpH7qGqCtpKMG62n1jg7Pu63LRcFjBmX3FzhFjNae3wcTVc2MAgB9SxXO5aaAnHMU0siiWOsaL8JaDK68eVTc_r0WC3PJKSW_Re1k7phiblvtt2I0bnF_sSioN4iKVzQk7jDnPLqk1P9d5aZMSyymbG5WeQsohTac3vVLjx0b15YNSUrhnSGePKYBYA; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6Ii95enZ2VkRqRlhVUGdIQ0Z4SFlBVVE9PSIsInZhbHVlIjoiajVaWHdLaWEzdzRkajNhL2ZwUUMwQXVCaGMwK0R3dUd5bEQ4Z2tsOWNaUWdwNTh4Njk3NWE4RWQ2eHE2ak80SFVTVU94M3lFRWNuNjVrNkFURklGQXpFc3poc0cxS1pHUXRtVHRsdzRaQXEzMkhCWEZJb2NOWjFsTjRlYXUzaGRic3cwSzZId3V5Z2lkQ29xVko0NnRxbDNITEpqeDdFVTB0REFFTldHNkpWSWVWRFZHeXQwKy9WOWVXYUVsVGg4VlVkdE1qTDNGalQxSVhxQ09VVW1heHhHdWNRUVFUc0xlbk1Ob3FJTWdKND0iLCJtYWMiOiIwOTYzZWVjMjEwMDgzOTNiZDRhOTNmMDFkNTUyMzM5YzdlOTdlZjU3Njg4YTkwZDgzNGNkZTFmNTM1N2E2NzdiIiwidGFnIjoiIn0%3D; XSRF-TOKEN=eyJpdiI6InZQV3VXeU4yMHpucTYzQWVWTkxDK1E9PSIsInZhbHVlIjoiTW1xQWRMYTJRRy9HbGJFYjc2NWNvVFJScXNVOEFMVWNTWGZnWE1WMHNvTGw5RkVTaEFxVEpWc1UrMkFRcHNob3RkTThkenJwVkhJWW12U0tjVGh2aUNUNXFsRG5GazFFam5YTitOU2psUW5Ga1krTHY5R09zclVkWFZVQS9NQksiLCJtYWMiOiJjNGVkZjNhYjRiNTliZmZmMGQxNzI0MzgzNzVjMzAzOGQ1MTM1NzkxODZjM2M5OWRiNzIyMjJlOGUwZGEwMjI0IiwidGFnIjoiIn0%3D`;

const bot = new TelegramBot(token, { polling: true });

// --- [ منع التوقف لـ Render ] ---
http.createServer((req, res) => { res.end("Basha System Online"); }).listen(process.env.PORT || 8080);

// --- [ التحقق من الاشتراك ] ---
async function checkSub(userId) {
    try {
        const m = await bot.getChatMember(channel_id, userId);
        return ['member', 'administrator', 'creator'].includes(m.status);
    } catch { return false; }
}

// قائمة جميع الأقسام الممكنة في الموقع
const allServices = {
    'wa': 'واتساب ✅', 'tg': 'تلجرام ✈️', 'fb': 'فيسبوك 👤', 
    'ig': 'إنستقرام 📸', 'go': 'جوجل 📧', 'tk': 'تيك توك 🎵', 
    'tw': 'تويتر 🐦', 'vi': 'فايبر 📞', 'sc': 'سناب شات ✨'
};

// --- [ وظيفة فحص الموقع وقراءة الأرقام المضافة ] ---
async function getLiveStock() {
    try {
        // يتم الاتصال بالموقع وجلب حالة الأرقام المضافة فعلياً
        const res = await axios.get('https://basha.cc/api/v1/stock/available', {
            headers: { 'Cookie': COOKIES }
        });
        return res.data; // نفترض أن الموقع يعيد قائمة بالأقسام التي فيها أرقام
    } catch (e) {
        console.error("خطأ في قراءة مخزون الموقع");
        return null;
    }
}

// --- [ معالجة /start ] ---
bot.onText(/\/start/, async (msg) => {
    const chatId = msg.chat.id;
    
    if (!(await checkSub(chatId))) {
        return bot.sendMessage(chatId, `⚠️ عذراً! يجب عليك الانضمام لقناة البوت أولاً:\n${channel_id}`, {
            reply_markup: { inline_keyboard: [[{ text: "اضغط هنا للانضمام ✅", url: `https://t.me/${channel_id.replace('@','')}` }]] }
        });
    }

    bot.sendMessage(chatId, "🔎 جاري فحص الأقسام المتوفرة حالياً في الموقع...");

    const stock = await getLiveStock();
    let keyboard = [];

    // فحص كل قسم: إذا كان مضافاً في الموقع تظهر المنصة في البوت
    for (let key in allServices) {
        // شرط: يظهر القسم فقط إذا وجد في الموقع أرقام مضافة لهذا القسم (أكبر من 0)
        if (stock && stock[key] > 0) {
            keyboard.push([{ text: `${allServices[key]} (${stock[key]})`, callback_data: `list_${key}` }]);
        }
    }

    if (keyboard.length === 0) {
        return bot.sendMessage(chatId, "❌ لا توجد أرقام مضافة في الموقع حالياً. يرجى المحاولة لاحقاً.");
    }

    bot.sendMessage(chatId, "✅ الأقسام المتوفرة (التي تحتوي على أرقام حالياً):", {
        reply_markup: { inline_keyboard: keyboard }
    });
});

// --- [ معالجة الاختيارات ] ---
bot.on('callback_query', async (q) => {
    const chatId = q.message.chat.id;
    const msgId = q.message.message_id;
    const data = q.data;

    if (data.startsWith("list_")) {
        const service = data.split("_")[1];
        bot.answerCallbackQuery(q.id, { text: "جاري جلب الدول المضافة... 🌍" });

        try {
            // جلب الدول التي أضيفت لها أرقام لهذا القسم حصراً
            const res = await axios.get(`https://basha.cc/api/v1/countries/${service}`, { headers: { 'Cookie': COOKIES } });
            const countries = res.data; // نفترض مصفوفة تحتوي على الدول المتاحة

            let keys = countries.map(c => [{ text: c.name_ar, callback_data: `get_${service}_${c.id}` }]);
            bot.editMessageText("🌍 اختر الدولة التي تم إضافة رقم لها:", {
                chat_id: chatId, message_id: msgId, reply_markup: { inline_keyboard: keys }
            });
        } catch (e) {
            bot.sendMessage(chatId, "⚠️ فشل جلب الدول المضافة.");
        }
    }

    if (data.startsWith("get_")) {
        const [, service, countryId] = data.split("_");
        
        try {
            const res = await axios.get(`https://basha.cc/api/v1/get-number?service=${service}&country=${countryId}`, {
                headers: { 'Cookie': COOKIES }
            });

            if (res.data.number) {
                const num = res.data.number;
                const actId = res.data.id;

                bot.editMessageText(`✅ تم استخراج الرقم المضاف:\n\n📱 الرقم: \`${num}\`\n💳 المحفظة: \`${admin_wallet}\`\n\n🔔 سيتم إرسال كود التحقق هنا تلقائياً فور وصوله للموقع...`, {
                    chat_id: chatId, message_id: msgId, parse_mode: 'Markdown',
                    reply_markup: { inline_keyboard: [[{ text: "🔄 تغيير الرقم / تحديث", callback_data: `get_${service}_${countryId}` }]] }
                });

                // بدء فحص الكود تلقائياً
                startSmsLoop(chatId, actId);
            }
        } catch (e) { bot.sendMessage(chatId, "⚠️ خطأ في قراءة الرقم."); }
    }
});

// --- [ وظيفة فحص الكود المستمر ] ---
async function startSmsLoop(chatId, actId) {
    const interval = setInterval(async () => {
        try {
            const res = await axios.get(`https://basha.cc/api/v1/check-sms/${actId}`, { headers: { 'Cookie': COOKIES } });
            if (res.data.code) {
                bot.sendMessage(chatId, `📩 **وصل كود التفعيل الجديد:**\n\n\`${res.data.code}\``, { parse_mode: 'Markdown' });
                clearInterval(interval);
            }
        } catch (e) {}
    }, 6000);
    setTimeout(() => clearInterval(interval), 900000);
}
