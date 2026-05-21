const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const http = require('http');

// --- [ الإعدادات - تأكد من دقة النسخ ] ---
const token = 'ضع_هنا_التوكن_الذي_أخذته_من_botfather'; 
const api_key = 'ضع_هنا_مفتاح_api_الخاص_بموقع_الأرقام'; 
const channel_id = '@fz_z_Z'; 
const admin_wallet = 'THxRZPDScimXo7F3Cmsg2uyEp2saCF4Afc';

// تشغيل البوت
const bot = new TelegramBot(token, { polling: true });

// سيرفر Render لضمان التشغيل
const port = process.env.PORT || 8080;
http.createServer((req, res) => {
    res.writeHead(200);
    res.end("Bot Active");
}).listen(port);

// صائد أخطاء الاتصال
bot.on('polling_error', (error) => {
    console.log("Error Detail:", error.message);
});

// مصفوفة الخدمات
const services = {
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

// الأمر start
bot.onText(/\/start/, async (msg) => {
    const chatId = msg.chat.id;
    
    if (!(await checkSub(chatId))) {
        return bot.sendMessage(chatId, `⚠️ يجب الاشتراك أولاً في القناة:\n${channel_id}`, {
            reply_markup: { inline_keyboard: [[{ text: "اشتراك", url: `https://t.me/${channel_id.replace('@','')}` }]] }
        });
    }

    try {
        // فحص الأقسام التي تتوفر فيها أرقام فقط
        const res = await axios.get(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getNumbersStatus`);
        let keyboard = [];
        
        for (let code in services) {
            // التحقق من توفر أرقام في القسم
            if (res.data[code + "_0"] > 0) {
                keyboard.push([{ text: `${services[code]} (${res.data[code + "_0"]})`, callback_data: `p_${code}` }]);
            }
        }

        if (keyboard.length === 0) return bot.sendMessage(chatId, "❌ لا توجد أرقام متوفرة حالياً.");

        bot.sendMessage(chatId, "✅ الأقسام المتوفرة حالياً بالرصيد:", {
            reply_markup: { inline_keyboard: keyboard }
        });
    } catch (e) {
        bot.sendMessage(chatId, "⚠️ فشل في الاتصال بموقع الأرقام.");
    }
});

// معالجة الضغط على الأزرار
bot.on('callback_query', async (q) => {
    const chatId = q.message.chat.id;
    const msgId = q.message.message_id;

    if (q.data.startsWith('p_')) {
        const s = q.data.split('_')[1];
        let keys = [];
        for (let cID in countries) {
            keys.push([{ text: countries[cID], callback_data: `g_${s}_${cID}` }]);
        }
        bot.editMessageText("🌍 اختر الدولة:", { chat_id: chatId, message_id: msgId, reply_markup: { inline_keyboard: keys } });
    }

    if (q.data.startsWith('g_')) {
        const [, s, c] = q.data.split('_');
        try {
            const res = await axios.get(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getNumber&service=${s}&country=${c}`);
            if (res.data.includes('ACCESS_NUMBER')) {
                const [, id, num] = res.data.split(':');
                bot.editMessageText(`✅ رقمك: \`${num}\`\n💰 المحفظة: \`${admin_wallet}\`\n\nوصل الكود؟ سيتم إرساله هنا فوراً...`, {
                    chat_id: chatId, message_id: msgId, parse_mode: 'Markdown',
                    reply_markup: { inline_keyboard: [[{ text: "🔄 تغيير الرقم", callback_data: `g_${s}_${c}` }]] }
                });
                checkSms(chatId, id);
            } else {
                bot.answerCallbackQuery(q.id, { text: "نفدت الأرقام!", show_alert: true });
            }
        } catch { bot.sendMessage(chatId, "خطأ في الطلب."); }
    }
});

async function checkSms(chatId, id) {
    let timer = setInterval(async () => {
        try {
            const res = await axios.get(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getStatus&id=${id}`);
            if (res.data.includes('STATUS_OK')) {
                bot.sendMessage(chatId, `📩 كودك هو: \`${res.data.split(':')[1]}\``, { parse_mode: 'Markdown' });
                clearInterval(timer);
            }
        } catch {}
    }, 5000);
    setTimeout(() => clearInterval(timer), 600000);
}
