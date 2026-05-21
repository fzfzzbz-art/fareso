const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const http = require('http');

// --- [ الإعدادات ] ---
const token = 'YOUR_TELEGRAM_BOT_TOKEN'; 
const api_key = 'YOUR_SMS_SERVICE_API_KEY'; 
const channel_id = '@fz_z_Z'; 
const admin_wallet = 'THxRZPDScimXo7F3Cmsg2uyEp2saCF4Afc';

const bot = new TelegramBot(token, { polling: true });

// --- [ منع توقف البوت - Render Keep Alive ] ---
const port = process.env.PORT || 8080;
http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.write("Bot is running dynamically!");
    res.end();
}).listen(port);

// --- [ أسماء الخدمات والدول بالعربي ] ---
const serviceNames = {
    'wa': 'واتساب ✅', 'tg': 'تلجرام ✈️', 'ig': 'إنستقرام 📸', 
    'fb': 'فيسبوك 👤', 'go': 'جوجل 📧', 'vi': 'فايبر 📞'
};

const countryNames = {
    '0': 'روسيا 🇷🇺', '1': 'أوكرانيا 🇺🇦', '6': 'إندونيسيا 🇮🇩', 
    '13': 'البرازيل 🇧🇷', '22': 'الهند 🇮🇳', '73': 'نيجيريا 🇳🇬', '15': 'بولندا 🇵🇱'
};

// --- [ التحقق من الاشتراك ] ---
async function checkSub(userId) {
    try {
        const member = await bot.getChatMember(channel_id, userId);
        return ['creator', 'administrator', 'member'].includes(member.status);
    } catch { return false; }
}

// --- [ أمر البداية /start ] ---
bot.onText(/\/start/, async (msg) => {
    const chatId = msg.chat.id;
    if (!(await checkSub(chatId))) {
        return bot.sendMessage(chatId, `⚠️ اشترك في القناة أولاً لتشغيل البوت:\n${channel_id}`, {
            reply_markup: { inline_keyboard: [[{ text: "اضغط هنا للاشتراك", url: `https://t.me/${channel_id.replace('@','')}` }]] }
        });
    }

    bot.sendMessage(chatId, "⏳ جاري فحص الأقسام المتوفرة حالياً بالرصيد...");

    try {
        // جلب الخدمات التي تتوفر فيها أرقام فقط (Inventory)
        const res = await axios.get(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getNumbersStatus`);
        const availableServices = res.data;
        
        let keyboard = [];
        for (let code in serviceNames) {
            // التحقق إذا كان القسم يحتوي على أرقام (أكثر من 0)
            if (availableServices[code + "_0"] > 0) {
                keyboard.push([{ text: `${serviceNames[code]} (${availableServices[code + "_0"]})`, callback_data: `p_${code}` }]);
            }
        }

        if (keyboard.length === 0) {
            return bot.sendMessage(chatId, "❌ عذراً، لا توجد أرقام متوفرة في الموقع حالياً.");
        }

        bot.sendMessage(chatId, "✅ الأقسام المتوفرة حالياً:\nاختر المنصة التي تريدها:", {
            reply_markup: { inline_keyboard: keyboard }
        });
    } catch (e) {
        bot.sendMessage(chatId, "⚠️ خطأ في جلب البيانات من الموقع.");
    }
});

// --- [ معالجة الاختيارات ] ---
bot.on('callback_query', async (query) => {
    const chatId = query.message.chat.id;
    const msgId = query.message.message_id;
    const data = query.data;

    // عند اختيار منصة (تظهر الدول التي تتوفر فيها أرقام لهذه المنصة فقط)
    if (data.startsWith('p_')) {
        const service = data.split('_')[1];
        let countryKeys = [];
        
        try {
            const res = await axios.get(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getNumbersStatus`);
            for (let cID in countryNames) {
                if (res.data[service + "_" + cID] > 0) {
                    countryKeys.push([{ text: `${countryNames[cID]} - ${res.data[service + "_" + cID]} رقم`, callback_data: `g_${service}_${cID}` }]);
                }
            }
            
            bot.editMessageText("🌍 اختر الدولة المتوفرة:", {
                chat_id: chatId, message_id: msgId,
                reply_markup: { inline_keyboard: countryKeys }
            });
        } catch (e) { bot.answerCallbackQuery(query.id, { text: "خطأ في التحديث" }); }
    }

    // عند اختيار دولة (طلب الرقم)
    if (data.startsWith('g_')) {
        const [, service, country] = data.split('_');
        bot.answerCallbackQuery(query.id, { text: "جاري استخراج الرقم... 🚀" });

        try {
            const res = await axios.get(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getNumber&service=${service}&country=${country}`);
            if (res.data.includes('ACCESS_NUMBER')) {
                const [, activationId, number] = res.data.split(':');
                
                bot.editMessageText(`✅ تم حجز الرقم بنجاح\n\n📱 الرقم: \`${number}\`\n💬 القسم: ${serviceNames[service]}\n💳 المحفظة: \`${admin_wallet}\`\n\n🔔 **سيتم إرسال الكود هنا تلقائياً فور وصوله...**`, {
                    chat_id: chatId, message_id: msgId, parse_mode: 'Markdown',
                    reply_markup: {
                        inline_keyboard: [[{ text: "🔄 تغيير الرقم (رقم آخر)", callback_data: `g_${service}_${country}` }]]
                    }
                });

                startSmsCheck(chatId, activationId);
            } else {
                bot.sendMessage(chatId, "❌ انتهت الأرقام لهذه الدولة، اختر دولة أخرى.");
            }
        } catch (e) { bot.sendMessage(chatId, "⚠️ حدث خطأ في الطلب."); }
    }
});

// --- [ وظيفة فحص الكود التلقائي ] ---
async function startSmsCheck(chatId, id) {
    let checkInterval = setInterval(async () => {
        try {
            const res = await axios.get(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getStatus&id=${id}`);
            if (res.data.includes('STATUS_OK')) {
                const code = res.data.split(':')[1];
                bot.sendMessage(chatId, `📩 **وصل كود التفعيل الجديد:**\n\n\`${code}\``, { parse_mode: 'Markdown' });
                clearInterval(checkInterval);
            } else if (res.data === 'STATUS_CANCEL') {
                clearInterval(checkInterval);
            }
        } catch (e) { /* استمرار الفحص */ }
    }, 5000);
    
    // توقف الفحص بعد 10 دقائق إذا لم يصل شيء
    setTimeout(() => clearInterval(checkInterval), 600000);
}
