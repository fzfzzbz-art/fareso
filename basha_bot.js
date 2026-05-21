const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const http = require('http');

// --- [ الإعدادات ] ---
// تأكد عند وضع التوكن أنه لا توجد مسافات قبل أو بعده
const token = 'ضع_التوكن_هنا_بدون_مسافات'.trim(); 
const api_key = 'ضع_مفتاح_api_هنا_بدون_مسافات'.trim(); 
const channel_id = '@fz_z_Z'; 
const admin_wallet = 'THxRZPDScimXo7F3Cmsg2uyEp2saCF4Afc';

// تشغيل البوت
const bot = new TelegramBot(token, { polling: true });

// سيرفر Render لضمان استمرار التشغيل (Keep Alive)
const port = process.env.PORT || 8080;
http.createServer((req, res) => {
    res.writeHead(200);
    res.end("Bot is Online!");
}).listen(port);

// صائد الأخطاء لكي لا يتوقف البوت باللون الأحمر مرة أخرى
bot.on('polling_error', (error) => {
    console.log("هناك مشكلة في الاتصال: ", error.message);
});

// أسماء الخدمات
const serviceNames = {
    'wa': 'واتساب ✅',
    'tg': 'تلجرام ✈️',
    'ig': 'إنستقرام 📸',
    'fb': 'فيسبوك 👤'
};

const countries = {
    '0': 'روسيا 🇷🇺',
    '1': 'أوكرانيا 🇺🇦',
    '6': 'إندونيسيا 🇮🇩'
};

// وظيفة التحقق من الاشتراك
async function checkSub(userId) {
    try {
        const member = await bot.getChatMember(channel_id, userId);
        return ['creator', 'administrator', 'member'].includes(member.status);
    } catch { return false; }
}

// استقبال /start
bot.onText(/\/start/, async (msg) => {
    const chatId = msg.chat.id;
    if (!(await checkSub(chatId))) {
        return bot.sendMessage(chatId, `⚠️ يجب الاشتراك في القناة أولاً:\n${channel_id}`, {
            reply_markup: { inline_keyboard: [[{ text: "اضغط هنا للاشتراك", url: `https://t.me/${channel_id.replace('@','')}` }]] }
        });
    }

    try {
        // فحص الأقسام المتوفرة (الديناميكي)
        const res = await axios.get(encodeURI(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getNumbersStatus`));
        let keyboard = [];
        for (let code in serviceNames) {
            if (res.data[code + "_0"] > 0) {
                keyboard.push([{ text: `${serviceNames[code]} (${res.data[code + "_0"]})`, callback_data: `p_${code}` }]);
            }
        }
        if (keyboard.length === 0) return bot.sendMessage(chatId, "❌ لا توجد أرقام بالرصيد حالياً.");
        bot.sendMessage(chatId, "✅ اختر القسم المطلوب:", { reply_markup: { inline_keyboard: keyboard } });
    } catch (e) {
        bot.sendMessage(chatId, "⚠️ خطأ في الاتصال بالموقع، تأكد من الـ API Key.");
    }
});

// معالجة الأزرار
bot.on('callback_query', async (q) => {
    const chatId = q.message.chat.id;
    if (q.data.startsWith('p_')) {
        const s = q.data.split('_')[1];
        let keys = Object.entries(countries).map(([id, n]) => [{ text: n, callback_data: `g_${s}_${id}` }]);
        bot.editMessageText("🌍 اختر الدولة:", { chat_id: chatId, message_id: q.message.message_id, reply_markup: { inline_keyboard: keys } });
    }
    if (q.data.startsWith('g_')) {
        const [, s, c] = q.data.split('_');
        try {
            const url = encodeURI(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getNumber&service=${s}&country=${c}`);
            const res = await axios.get(url);
            if (res.data.includes('ACCESS_NUMBER')) {
                const [, id, num] = res.data.split(':');
                bot.editMessageText(`✅ تم حجز الرقم:\n\n📱 \`${num}\`\n\n💰 المحفظة: \`${admin_wallet}\`\n\nوصل الكود؟ سيتم إرساله هنا فوراً...`, {
                    chat_id: chatId, message_id: q.message.message_id, parse_mode: 'Markdown',
                    reply_markup: { inline_keyboard: [[{ text: "🔄 تغيير الرقم", callback_data: `g_${s}_${c}` }]] }
                });
                startCheck(chatId, id);
            } else {
                bot.answerCallbackQuery(q.id, { text: "نفدت الأرقام!", show_alert: true });
            }
        } catch { bot.sendMessage(chatId, "⚠️ فشل طلب الرقم."); }
    }
});

async function startCheck(chatId, id) {
    let timer = setInterval(async () => {
        try {
            const res = await axios.get(encodeURI(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getStatus&id=${id}`));
            if (res.data.includes('STATUS_OK')) {
                bot.sendMessage(chatId, `📩 كود التفعيل الخاص بك:\n\n\`${res.data.split(':')[1]}\``, { parse_mode: 'Markdown' });
                clearInterval(timer);
            }
        } catch {}
    }, 5000);
    setTimeout(() => clearInterval(timer), 600000);
}
