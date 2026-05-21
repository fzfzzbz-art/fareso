const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const http = require('http');

// --- [ الإعدادات من البيئة Environment Variables ] ---
const token = process.env.BOT_TOKEN; 
const channel_id = process.env.CHANNEL_ID || '@fz_z_Z';
const admin_wallet = 'THxRZPDScimXo7F3Cmsg2uyEp2saCF4Afc';

// الكوكيز الخاصة بك للوصول للموقع
const my_cookies = `basha_iprn_vas_session=eyJpdiI6InJiZDFPZDVWZ1RJaXRpU3ZiRldEOUE9PSIsInZhbHVlIjoiOGh2L09xeEZmVHNRdzJCOFNYUTFvcGdTRVlvd3owdGQ1dDAxZFo0aG5PL0tEVHRtTkcvRWxPdGR6T3RqRDk0S3BxZkxQWkdWdnk3NjVpTkw1TEFGbnhhbHRGTXk5M05QTXpONUVtT1JQZ2RpT2NvWFNCQ0g0UEF5ZFFyUHJyc3MiLCJtYWMiOiJlOTBlMTdlMmRiYzllMDhlYzUyMTJjNWE2Zjk2ZjMxYmU1ZGYxZjJmZTg5NWZhNDhmMGEyNzQ1MmMwYjlmZDk0IiwidGFnIjoiIn0%3D; cf_clearance=Wcw_QXt5eEP9ij5Zlk_RZZhRMQGsZ4ILQhhKprApsds-1779385492-1.2.1.1-uwy2A9b0n0jBCQvuFQudtpC7wYMcUF.Tqpi2_1KTGD1RjipFpriGCQFpXQQbR0Jlg1JqdXThnl3e9RikXMbrqIXj1gOTl7APgYTAxEO4q0aG8bdt0m66KIVHUWw5YUvqob6PYVJOXrZZpz0pldAKDI6B0JRZpH7qGqCtpKMG62n1jg7Pu63LRcFjBmX3FzhFjNae3wcTVc2MAgB9SxXO5aaAnHMU0siiWOsaL8JaDK68eVTc_r0WC3PJKSW_Re1k7phiblvtt2I0bnF_sSioN4iKVzQk7jDnPLqk1P9d5aZMSyymbG5WeQsohTac3vVLjx0b15YNSUrhnSGePKYBYA; remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6Ii95enZ2VkRqRlhVUGdIQ0Z4SFlBVVE9PSIsInZhbHVlIjoiajVaWHdLaWEzdzRkajNhL2ZwUUMwQXVCaGMwK0R3dUd5bEQ4Z2tsOWNaUWdwNTh4Njk3NWE4RWQ2eHE2ak80SFVTVU94M3lFRWNuNjVrNkFURklGQXpFc3poc0cxS1pHUXRtVHRsdzRaQXEzMkhCWEZJb2NOWjFsTjRlYXUzaGRic3cwSzZId3V5Z2lkQ29xVko0NnRxbDNITEpqeDdFVTB0REFFTldHNkpWSWVWRFZHeXQwKy9WOWVXYUVsVGg4VlVkdE1qTDNGalQxSVhxQ09VVW1heHhHdWNRUVFUc0xlbk1Ob3FJTWdKND0iLCJtYWMiOiIwOTYzZWVjMjEwMDgzOTNiZDRhOTNmMDFkNTUyMzM5YzdlOTdlZjU3Njg4YTkwZDgzNGNkZTFmNTM1N2E2NzdiIiwidGFnIjoiIn0%3D; XSRF-TOKEN=eyJpdiI6InZQV3VXeU4yMHpucTYzQWVWTkxDK1E9PSIsInZhbHVlIjoiTW1xQWRMYTJRRy9HbGJFYjc2NWNvVFJScXNVOEFMVWNTWGZnWE1WMHNvTGw5RkVTaEFxVEpWc1UrMkFRcHNob3RkTThkenJwVkhJWW12U0tjVGh2aUNUNXFsRG5GazFFam5YTitOU2psUW5Ga1krTHY5R09zclVkWFZVQS9NQksiLCJtYWMiOiJjNGVkZjNhYjRiNTliZmZmMGQxNzI0MzgzNzVjMzAzOGQ1MTM1NzkxODZjM2M5OWRiNzIyMjJlOGUwZGEwMjI0IiwidGFnIjoiIn0%3D`;

const bot = new TelegramBot(token, { polling: true });

// --- [ منع التوقف ] ---
http.createServer((req, res) => { res.end("Basha Bot Running"); }).listen(process.env.PORT || 8080);

// --- [ التحقق من الاشتراك ] ---
async function checkSub(userId) {
    try {
        const m = await bot.getChatMember(channel_id, userId);
        return ['member', 'administrator', 'creator'].includes(m.status);
    } catch { return false; }
}

// --- [ جلب الأرقام المضافة من الموقع ] ---
async function fetchNumbersFromSite() {
    try {
        const res = await axios.get('https://basha.cc/free-numbers', { // الرابط الذي تظهر فيه الأرقام المضافة
            headers: { 'Cookie': my_cookies }
        });
        // ملاحظة: هنا نحتاج عمل Parsing للبيانات. إذا كان الموقع يرجع JSON يكون أسهل
        return res.data; 
    } catch (e) { return null; }
}

// --- [ الرد على /start ] ---
bot.onText(/\/start/, async (msg) => {
    const chatId = msg.chat.id;
    
    if (!(await checkSub(chatId))) {
        return bot.sendMessage(chatId, `⚠️ يجب الاشتراك أولاً في القناة لاستخدام البوت:\n${channel_id}`, {
            reply_markup: {
                inline_keyboard: [[{ text: "اضغط هنا للاشتراك ✅", url: `https://t.me/${channel_id.replace('@','')}` }]]
            }
        });
    }

    const opts = {
        reply_markup: {
            inline_keyboard: [
                [{ text: "واتساب ✅", callback_data: "list_wa" }],
                [{ text: "تلجرام ✈️", callback_data: "list_tg" }],
                [{ text: "فيسبوك 👤", callback_data: "list_fb" }]
            ]
        }
    };
    bot.sendMessage(chatId, "مرحباً بك في بوت أرقام باشا 🤖\nالرجاء اختيار القسم لرؤية الأرقام المضافة:", opts);
});

// --- [ معالجة الضغط على الأقسام ] ---
bot.on('callback_query', async (q) => {
    const chatId = q.message.chat.id;
    const msgId = q.message.message_id;
    const data = q.data;

    // عرض الدول المتاحة للقسم المختار
    if (data.startsWith("list_")) {
        const service = data.split("_")[1];
        const countries = [
            { id: '0', name: 'روسيا 🇷🇺' },
            { id: '1', name: 'أوكرانيا 🇺🇦' },
            { id: '6', name: 'إندونيسيا 🇮🇩' }
        ];

        const keys = countries.map(c => [{ text: c.name, callback_data: `getnum_${service}_${c.id}` }]);
        bot.editMessageText("🌍 اختر الدولة لرؤية الرقم المتاح:", {
            chat_id: chatId, message_id: msgId, reply_markup: { inline_keyboard: keys }
        });
    }

    // جلب الرقم الفعلي
    if (data.startsWith("getnum_")) {
        const [, service, countryId] = data.split("_");
        
        bot.answerCallbackQuery(q.id, { text: "جاري قراءة الأرقام المضافة... 🔍" });

        try {
            // محاكاة جلب الرقم الأخير المضاف من الموقع لهذا القسم
            const siteData = await fetchNumbersFromSite();
            
            // هنا نفترض أن الموقع يعطينا الرقم. سأضع رقم تجريبي (يجب ربطه ببيانات الموقع الفعلية)
            const demoNumber = "+79991234567"; 

            const msgText = `✅ الرقم المضاف حالياً لهذا القسم:\n\n` +
                            `📱 الرقم: \`${demoNumber}\` (اضغط للنسخ)\n` +
                            `💳 المحفظة: \`${admin_wallet}\`\n\n` +
                            `🔔 انتظر وصول الكود... سيتم تحديثك فور استلامه من الموقع.`;

            bot.editMessageText(msgText, {
                chat_id: chatId,
                message_id: msgId,
                parse_mode: 'Markdown',
                reply_markup: {
                    inline_keyboard: [
                        [{ text: "🔄 تحديث/تغيير الرقم", callback_data: `getnum_${service}_${countryId}` }]
                    ]
                }
            });

            // بدء مراقبة الرسائل لهذا الرقم
            monitorSms(chatId, demoNumber);

        } catch (e) {
            bot.sendMessage(chatId, "⚠️ فشل في قراءة البيانات من الموقع. تأكد من الكوكيز.");
        }
    }
});

// --- [ مراقبة وصول الكود ] ---
async function monitorSms(chatId, phoneNumber) {
    const interval = setInterval(async () => {
        try {
            // طلب جلب الرسائل الأخيرة للرقم من basha.cc
            const res = await axios.get(`https://basha.cc/api/v1/messages?number=${phoneNumber}`, {
                headers: { 'Cookie': my_cookies }
            });

            if (res.data && res.data.code) {
                bot.sendMessage(chatId, `📩 **وصل كود جديد للرقم ${phoneNumber}:**\n\nالكود: \`${res.data.code}\``, { parse_mode: 'Markdown' });
                clearInterval(interval);
            }
        } catch (e) { /* استمرار المحاولة */ }
    }, 7000);

    // توقف المراقبة بعد 15 دقيقة
    setTimeout(() => clearInterval(interval), 900000);
}
