const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const http = require('http');

// --- [ الإعدادات ] ---
const token = 'YOUR_TELEGRAM_BOT_TOKEN'; 
const api_key = 'YOUR_SMS_SERVICE_API_KEY'; 
const channel_id = '@fz_z_Z'; 
const admin_wallet = 'THxRZPDScimXo7F3Cmsg2uyEp2saCF4Afc';

const bot = new TelegramBot(token, { polling: true });

// --- [ حل مشكلة Render - Keep Alive ] ---
// Render يتطلب وجود سيرفر ويب ليظل البوت يعمل
const port = process.env.PORT || 8080;
http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.write("Bot basha_bot.js is active!");
    res.end();
}).listen(port, () => {
    console.log(`Server is listening on port ${port}`);
});

// --- [ الأقسام والدول ] ---
const platforms = {
    'wa': 'واتساب ✅',
    'tg': 'تلجرام ✈️',
    'ig': 'إنستقرام 📸',
    'fb': 'فيسبوك 👤'
};

const countries = {
    '0': 'روسيا 🇷🇺',
    '1': 'أوكرانيا 🇺🇦',
    '6': 'إندونيسيا 🇮🇩',
    '13': 'البرازيل 🇧🇷',
    '22': 'الهند 🇮🇳'
};

// --- [ التحقق من الاشتراك الإجباري ] ---
async function checkSub(userId) {
    try {
        const member = await bot.getChatMember(channel_id, userId);
        return ['creator', 'administrator', 'member'].includes(member.status);
    } catch { return false; }
}

// --- [ الأوامر ] ---
bot.onText(/\/start/, async (msg) => {
    const chatId = msg.chat.id;
    const isSub = await checkSub(chatId);

    if (!isSub) {
        return bot.sendMessage(chatId, `❌ يجب الاشتراك في القناة أولاً:\n${channel_id}`, {
            reply_markup: {
                inline_keyboard: [[{ text: "اضغط للاشتراك", url: `https://t.me/${channel_id.replace('@', '')}` }]]
            }
        });
    }

    const keyboard = Object.entries(platforms).map(([code, name]) => [{ text: name, callback_data: `p_${code}` }]);
    bot.sendMessage(chatId, "مرحباً بك! اختر المنصة:", { reply_markup: { inline_keyboard: keyboard } });
});

bot.on('callback_query', async (query) => {
    const chatId = query.message.chat.id;
    const data = query.data;

    if (data.startsWith('p_')) {
        const pCode = data.split('_')[1];
        const keys = Object.entries(countries).map(([id, n]) => [{ text: n, callback_data: `g_${pCode}_${id}` }]);
        bot.editMessageText("اختر الدولة بالعربي:", {
            chat_id: chatId,
            message_id: query.message.message_id,
            reply_markup: { inline_keyboard: keys }
        });
    }

    if (data.startsWith('g_')) {
        const [, plat, country] = data.split('_');
        try {
            const res = await axios.get(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getNumber&service=${plat}&country=${country}`);
            if (res.data.includes('ACCESS_NUMBER')) {
                const [, id, num] = res.data.split(':');
                bot.editMessageText(`✅ رقمك الجديد جاهز:\n\nالرقم: \`${num}\`\n\nالمحفظة: \`${admin_wallet}\`\n\nانتظر وصول الكود هنا...`, {
                    chat_id: chatId,
                    message_id: query.message.message_id,
                    parse_mode: 'Markdown',
                    reply_markup: {
                        inline_keyboard: [[{ text: "🔄 تغيير الرقم", callback_data: `g_${plat}_${country}` }]]
                    }
                });
                startCheck(chatId, id);
            } else {
                bot.answerCallbackQuery(query.id, { text: "لا توجد أرقام حالياً", show_alert: true });
            }
        } catch { bot.sendMessage(chatId, "خطأ في السيرفر"); }
    }
});

async function startCheck(chatId, id) {
    let timer = setInterval(async () => {
        try {
            const res = await axios.get(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getStatus&id=${id}`);
            if (res.data.includes('STATUS_OK')) {
                bot.sendMessage(chatId, `📩 كود التفعيل: \`${res.data.split(':')[1]}\``, { parse_mode: 'Markdown' });
                clearInterval(timer);
            }
        } catch { /* silence */ }
    }, 5000);
    setTimeout(() => clearInterval(timer), 600000);
}
