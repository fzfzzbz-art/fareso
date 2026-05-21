const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const http = require('http');

// --- [ الإعدادات من البيئة ] ---
const token = process.env.BOT_TOKEN;
const channel_id = process.env.CHANNEL_ID || '@fz_z_Z';
const admin_wallet = 'THxRZPDScimXo7F3Cmsg2uyEp2saCF4Afc';

// نص الكوكيز الذي زودتني به (يفضل وضعه في متغير بيئة باسم COOKIES)
const cookiesString = `basha_iprn_vas_session=eyJpdiI6InJiZDFPZDVWZ1RJaXRpU3ZiRldEOUE9PSIsInZhbHVlIjoiOGh2L09xeEZmVHNRdzJCOFNYUTFvcGdTRVlvd3owdGQ1dDAxZFo0aG5PL0tEVHRtTkcvRWxPdGR6T3RqRDk0S3BxZkxQWkdWdnk3NjVpTkw1TEFGbnhhbHRGTXk5M05QTXpONUVtT1JQZ2RpT2NvWFNCQ0g0UEF5ZFFyUHJyc3MiLCJtYWMiOiJlOTBlMTdlMmRiYzllMDhlYzUyMTJjNWE2Zjk2ZjMxYmU1ZGYxZjJmZTg5NWZhNDhmMGEyNzQ1MmMwYjlmZDk0IiwidGFnIjoiIn0%3D; cf_clearance=Wcw_QXt5eEP9ij5Zlk_RZZhRMQGsZ4ILQhhKprApsds-1779385492-1.2.1.1-uwy2A9b0n0jBCQvuFQudtpC7wYMcUF.Tqpi2_1KTGD1RjipFpriGCQFpXQQbR0Jlg1JqdXThnl3e9RikXMbrqIXj1gOTl7APgYTAxEO4q0aG8bdt0m66KIVHUWw5YUvqob6PYVJOXrZZpz0pldAKDI6B0JRZpH7qGqCtpKMG62n1jg7Pu63LRcFjBmX3FzhFjNae3wcTVc2MAgB9SxXO5aaAnHMU0siiWOsaL8JaDK68eVTc_r0WC3PJKSW_Re1k7phiblvtt2I0bnF_sSioN4iKVzQk7jDnPLqk1P9d5aZMSyymbG5WeQsohTac3vVLjx0b15YNSUrhnSGePKYBYA; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6Ii95enZ2VkRqRlhVUGdIQ0Z4SFlBVVE9PSIsInZhbHVlIjoiajVaWHdLaWEzdzRkajNhL2ZwUUMwQXVCaGMwK0R3dUd5bEQ4Z2tsOWNaUWdwNTh4Njk3NWE4RWQ2eHE2ak80SFVTVU94M3lFRWNuNjVrNkFURklGQXpFc3poc0cxS1pHUXRtVHRsdzRaQXEzMkhCWEZJb2NOWjFsTjRlYXUzaGRic3cwSzZId3V5Z2lkQ29xVko0NnRxbDNITEpqeDdFVTB0REFFTldHNkpWSWVWRFZHeXQwKy9WOWVXYUVsVGg4VlVkdE1qTDNGalQxSVhxQ09VVW1heHhHdWNRUVFUc0xlbk1Ob3FJTWdKND0iLCJtYWMiOiIwOTYzZWVjMjEwMDgzOTNiZDRhOTNmMDFkNTUyMzM5YzdlOTdlZjU3Njg4YTkwZDgzNGNkZTFmNTM1N2E2NzdiIiwidGFnIjoiIn0%3D; XSRF-TOKEN=eyJpdiI6InZQV3VXeU4yMHpucTYzQWVWTkxDK1E9PSIsInZhbHVlIjoiTW1xQWRMYTJRRy9HbGJFYjc2NWNvVFJScXNVOEFMVWNTWGZnWE1WMHNvTGw5RkVTaEFxVEpWc1UrMkFRcHNob3RkTThkenJwVkhJWW12U0tjVGh2aUNUNXFsRG5GazFFam5YTitOU2psUW5Ga1krTHY5R09zclVkWFZVQS9NQksiLCJtYWMiOiJjNGVkZjNhYjRiNTliZmZmMGQxNzI0MzgzNzVjMzAzOGQ1MTM1NzkxODZjM2M5OWRiNzIyMjJlOGUwZGEwMjI0IiwidGFnIjoiIn0%3D`;

const bot = new TelegramBot(token, { polling: true });

// --- [ منع التوقف ] ---
http.createServer((req, res) => { res.end("Basha Bot is Running"); }).listen(process.env.PORT || 8080);

// --- [ الوظائف المساعدة ] ---
async function checkSub(userId) {
    try {
        const m = await bot.getChatMember(channel_id, userId);
        return ['member', 'administrator', 'creator'].includes(m.status);
    } catch { return false; }
}

// محاكاة طلب جلب الأقسام المتوفرة من الموقع
async function getAvailableServices() {
    try {
        const response = await axios.get('https://basha.cc/api/v1/services', { // هذا الرابط افتراضي بناءً على دومينك
            headers: { 'Cookie': cookiesString }
        });
        return response.data; 
    } catch (e) { return null; }
}

bot.onText(/\/start/, async (msg) => {
    const chatId = msg.chat.id;
    if (!(await checkSub(chatId))) {
        return bot.sendMessage(chatId, `⚠️ اشترك أولاً: ${channel_id}`, {
            reply_markup: { inline_keyboard: [[{ text: "اشترك الآن", url: `https://t.me/${channel_id.replace('@','')}` }]] }
        });
    }

    // عرض الأقسام (تعديل يدوي بناءً على خدمات basha.cc)
    const opts = {
        reply_markup: {
            inline_keyboard: [
                [{ text: "واتساب ✅", callback_data: "get_wa" }],
                [{ text: "تلجرام ✈️", callback_data: "get_tg" }],
                [{ text: "فيسبوك 👤", callback_data: "get_fb" }]
            ]
        }
    };
    bot.sendMessage(chatId, "مرحباً بك في بوت باشا 🤖\nاختر المنصة المطلوبة:", opts);
});

bot.on('callback_query', async (q) => {
    const chatId = q.message.chat.id;
    const action = q.data;

    if (action.startsWith("get_")) {
        const service = action.split("_")[1];
        
        // هنا نقوم بطلب رقم من الموقع باستخدام الكوكيز
        bot.sendMessage(chatId, "⏳ جاري استخراج الرقم من basha.cc...");
        
        try {
            // محاكاة طلب الرقم (POST request عادة في المواقع)
            const res = await axios.post('https://basha.cc/api/v1/numbers/order', { service: service }, {
                headers: { 'Cookie': cookiesString, 'X-XSRF-TOKEN': 'دقق في قيمة التوكن هنا' }
            });

            if (res.data.number) {
                const num = res.data.number;
                const orderId = res.data.id;

                bot.sendMessage(chatId, `✅ تم تجهيز الرقم:\n\n📱 \`${num}\`\n💰 المحفظة: \`${admin_wallet}\`\n\nسيتم إرسال الكود هنا فور وصوله...`, {
                    parse_mode: 'Markdown',
                    reply_markup: { inline_keyboard: [[{ text: "🔄 تغيير الرقم", callback_data: `get_${service}` }]] }
                });

                // بدء فحص الرسائل (جلب الكود)
                checkMessages(chatId, orderId);
            }
        } catch (e) {
            bot.sendMessage(chatId, "⚠️ فشل جلب الرقم. تأكد من رصيدك في الموقع أو صلاحية الكوكيز.");
        }
    }
});

// وظيفة جلب الرسائل بالكوكيز
async function checkMessages(chatId, orderId) {
    let checkCount = 0;
    const timer = setInterval(async () => {
        try {
            const res = await axios.get(`https://basha.cc/api/v1/orders/${orderId}`, {
                headers: { 'Cookie': cookiesString }
            });

            if (res.data.sms_code) {
                bot.sendMessage(chatId, `📩 كود التفعيل المستلم:\n\n\`${res.data.sms_code}\``, { parse_mode: 'Markdown' });
                clearInterval(timer);
            }
        } catch (e) { /* استمرار المحاولة */ }

        checkCount++;
        if (checkCount > 100) clearInterval(timer); // توقف بعد فترة
    }, 5000);
}
