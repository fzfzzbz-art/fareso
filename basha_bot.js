const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const http = require('http');

// --- [ الإعدادات ] ---
const token = 'ضع_التوكن_هنا'; 
const api_key = 'ضع_مفتاح_الموقع_هنا'; 
const channel_id = '@fz_z_Z'; 
const admin_wallet = 'THxRZPDScimXo7F3Cmsg2uyEp2saCF4Afc';

// تشغيل البوت مع معالجة أخطاء الاتصال
const bot = new TelegramBot(token, { polling: true });

bot.on('polling_error', (error) => {
    console.log("خطأ في الاتصال بتلجرام: ", error.message); 
});

// --- [ سيرفر وهمي لمنع التوقف ] ---
const port = process.env.PORT || 8080;
http.createServer((req, res) => {
    res.write("Bot is running!");
    res.end();
}).listen(port);

// --- [ أسماء الخدمات ] ---
const serviceNames = { 'wa': 'واتساب ✅', 'tg': 'تلجرام ✈️', 'ig': 'إنستقرام 📸', 'fb': 'فيسبوك 👤' };
const countryNames = { '0': 'روسيا 🇷🇺', '1': 'أوكرانيا 🇺🇦', '6': 'إندونيسيا 🇮🇩' };

// --- [ التحقق من الاشتراك ] ---
async function checkSub(userId) {
    try {
        const member = await bot.getChatMember(channel_id, userId);
        return ['creator', 'administrator', 'member'].includes(member.status);
    } catch (e) {
        console.log("فشل التحقق من القناة: تأكد أن البوت مشرف هناك.");
        return false;
    }
}

// --- [ استقبال /start ] ---
bot.onText(/\/start/, async (msg) => {
    const chatId = msg.chat.id;
    
    try {
        const isSub = await checkSub(chatId);
        if (!isSub) {
            return bot.sendMessage(chatId, `⚠️ يجب الاشتراك في القناة أولاً:\n${channel_id}`, {
                reply_markup: { inline_keyboard: [[{ text: "اضغط للاشتراك", url: `https://t.me/${channel_id.replace('@', '')}` }]] }
            });
        }

        bot.sendMessage(chatId, "🔎 جاري فحص الأقسام المتوفرة...");

        // جلب الحالات من الموقع
        const res = await axios.get(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getNumbersStatus`);
        let keyboard = [];
        
        for (let code in serviceNames) {
            if (res.data[code + "_0"] > 0) { // التحقق من توفر أرقام
                keyboard.push([{ text: `${serviceNames[code]} (${res.data[code + "_0"]})`, callback_data: `p_${code}` }]);
            }
        }

        if (keyboard.length === 0) {
            return bot.sendMessage(chatId, "❌ لا توجد أرقام متوفرة حالياً في الموقع.");
        }

        bot.sendMessage(chatId, "✅ الأقسام المتوفرة:", { reply_markup: { inline_keyboard: keyboard } });

    } catch (err) {
        bot.sendMessage(chatId, "حدث خطأ فني، يرجى المحاولة لاحقاً.");
        console.log("Error in /start: ", err.message);
    }
});

// ملاحظة: أكمل باقي الكود الخاص بـ callback_query كما في الرسالة السابقة
