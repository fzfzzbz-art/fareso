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
    '73': 'نيجيريا 🇳🇬'
};

// --- [ وظيفة التحقق من الاشتراك ] ---
async function checkSubscription(userId) {
    try {
        const member = await bot.getChatMember(channel_id, userId);
        return ['creator', 'administrator', 'member'].includes(member.status);
    } catch (e) {
        return false;
    }
}

// --- [ عند إرسال /start ] ---
bot.onText(/\/start/, async (msg) => {
    const chatId = msg.chat.id;
    const isSubscribed = await checkSubscription(chatId);

    if (!isSubscribed) {
        return bot.sendMessage(chatId, `⚠️ عذراً عزيزي، يجب عليك الاشتراك في قناة البوت أولاً لاستخدام الخدمات:\n\n🔗 القناة: ${channel_id}`, {
            reply_markup: {
                inline_keyboard: [[{ text: "اضغط هنا للاشتراك ✅", url: `https://t.me/${channel_id.replace('@', '')}` }]]
            }
        });
    }

    const keyboard = Object.entries(platforms).map(([code, name]) => [{ text: name, callback_data: `plat_${code}` }]);
    bot.sendMessage(chatId, "مرحباً بك في بوت الأرقام 🤖\n\nالرجاء اختيار المنصة التي تريد رقماً لها:", {
        reply_markup: { inline_keyboard: keyboard }
    });
});

// --- [ معالجة التفاعلات ] ---
bot.on('callback_query', async (query) => {
    const chatId = query.message.chat.id;
    const messageId = query.message.message_id;
    const data = query.data;

    // 1. اختيار المنصة
    if (data.startsWith('plat_')) {
        const platCode = data.split('_')[1];
        const countryKeyboard = Object.entries(countries).map(([id, name]) => [{ text: name, callback_data: `get_${platCode}_${id}` }]);
        
        bot.editMessageText("تم اختيار المنصة. الآن اختر الدولة المطلوبة:", {
            chat_id: chatId,
            message_id: messageId,
            reply_markup: { inline_keyboard: countryKeyboard }
        });
    }

    // 2. طلب الرقم أو تغييره
    if (data.startsWith('get_')) {
        const [, plat, country] = data.split('_');
        
        bot.answerCallbackQuery(query.id, { text: "جاري طلب الرقم... ⏳" });

        try {
            // طلب الرقم من API
            const response = await axios.get(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getNumber&service=${plat}&country=${country}`);
            
            if (response.data.includes('ACCESS_NUMBER')) {
                const [ , activationId, phoneNumber] = response.data.split(':');
                
                const msgText = `✅ تم تجهيز رقمك الجديد:\n\n` +
                                `📱 الرقم: \`${phoneNumber}\`\n` +
                                `💬 المنصة: ${platforms[plat]}\n\n` +
                                `💳 المحفظة للدفع: \`${admin_wallet}\`\n\n` +
                                `⏳ انتظر وصول الكود هنا، سيتم إرساله فور وصوله تلقائياً...`;

                bot.editMessageText(msgText, {
                    chat_id: chatId,
                    message_id: messageId,
                    parse_mode: 'Markdown',
                    reply_markup: {
                        inline_keyboard: [
                            [{ text: "🔄 تغيير الرقم (رقم آخر)", callback_data: `get_${plat}_${country}` }],
                            [{ text: "❌ إلغاء العملية", callback_data: `cancel_${activationId}` }]
                        ]
                    }
                });

                // بدء فحص وصول الكود تلقائياً
                startCheckCode(chatId, activationId);

            } else {
                bot.sendMessage(chatId, "❌ عذراً، لا توجد أرقام متوفرة لهذه الدولة حالياً. جرب دولة أخرى.");
            }
        } catch (error) {
            bot.sendMessage(chatId, "⚠️ حدث خطأ أثناء الاتصال بسيرفر الأرقام.");
        }
    }
});

// --- [ وظيفة فحص الكود التلقائي ] ---
async function startCheckCode(chatId, id) {
    let checkCount = 0;
    const maxChecks = 60; // سيفحص لمدة 5 دقائق (كل 5 ثوانٍ)

    const interval = setInterval(async () => {
        try {
            const res = await axios.get(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getStatus&id=${id}`);
            
            if (res.data.includes('STATUS_OK')) {
                const smsCode = res.data.split(':')[1];
                bot.sendMessage(chatId, `📩 **وصل كود التفعيل الجديد!**\n\nالكود هو: \`${smsCode}\``, { parse_mode: 'Markdown' });
                clearInterval(interval);
            } 
            else if (res.data === 'STATUS_CANCEL' || checkCount >= maxChecks) {
                clearInterval(interval);
            }
            checkCount++;
        } catch (e) {
            console.log("Check Error");
        }
    }, 5000); 
}
const countries = {
    '0': 'روسيا 🇷🇺',
    '1': 'أوكرانيا 🇺🇦',
    '6': 'إندونيسيا 🇮🇩',
    '13': 'البرازيل 🇧🇷',
    '22': 'الهند 🇮🇳'
};

// --- التعامل مع أمر /start ---
bot.onText(/\/start/, async (msg) => {
    const chatId = msg.chat.id;
    const isSubscribed = await checkSubscription(chatId);

    if (!isSubscribed) {
        return bot.sendMessage(chatId, `⚠️ يجب عليك الاشتراك في قناة البوت أولاً لتتمكن من استخدامه:\n${channel_id}`, {
            reply_markup: {
                inline_keyboard: [[{ text: "اضغط هنا للاشتراك", url: `https://t.me/${channel_id.replace('@', '')}` }]]
            }
        });
    }

    const keyboard = Object.entries(platforms).map(([code, name]) => [{ text: name, callback_data: `plat_${code}` }]);
    bot.sendMessage(chatId, "مرحباً بك في بوت الأرقام 🤖\n\nالرجاء اختيار المنصة التي تريد رقماً لها:", {
        reply_markup: { inline_keyboard: keyboard }
    });
});

// --- معالجة الضغط على الأزرار ---
bot.on('callback_query', async (query) => {
    const chatId = query.message.chat.id;
    const data = query.data;

    // اختيار المنصة
    if (data.startsWith('plat_')) {
        const platCode = data.split('_')[1];
        const countryKeyboard = Object.entries(countries).map(([id, name]) => [{ text: name, callback_data: `get_${platCode}_${id}` }]);
        
        bot.editMessageText("تم اختيار المنصة. الآن اختر الدولة:", {
            chat_id: chatId,
            message_id: query.message.message_id,
            reply_markup: { inline_keyboard: countryKeyboard }
        });
    }

    // طلب الرقم وتغييره
    if (data.startsWith('get_')) {
        const [, plat, country] = data.split('_');
        
        try {
            // ملاحظة: هذا الرابط مثال لموقع sms-activate، قم بتغييره حسب موقعك
            const response = await axios.get(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getNumber&service=${plat}&country=${country}`);
            
            if (response.data.includes('ACCESS_NUMBER')) {
                const [ , id, number] = response.data.split(':');
                
                const msgText = `✅ تم تجهيز رقمك:\n\n` +
                                `📱 الرقم: \`${number}\` (اضغط للنسخ)\n` +
                                `🌐 المنصة: ${platforms[plat]}\n` +
                                `💰 المحفظة المدعومة: \`${admin_wallet}\`\n\n` +
                                `انتظر وصول الكود هنا تلقائياً...`;

                bot.editMessageText(msgText, {
                    chat_id: chatId,
                    message_id: query.message.message_id,
                    parse_mode: 'Markdown',
                    reply_markup: {
                        inline_keyboard: [
                            [{ text: "🔄 تغيير الرقم", callback_data: `get_${plat}_${country}` }],
                            [{ text: "❌ إلغاء العملية", callback_data: `cancel_${id}` }]
                        ]
                    }
                });

                // بدء فحص وصول الكود
                startCheckCode(chatId, id);

            } else {
                bot.answerCallbackQuery(query.id, { text: "عذراً، لا توجد أرقام متوفرة حالياً لهذه الدولة.", show_alert: true });
            }
        } catch (error) {
            bot.sendMessage(chatId, "حدث خطأ في الاتصال بالمزود.");
        }
    }
});

// --- وظيفة فحص الكود تلقائياً ---
async function startCheckCode(chatId, activationId) {
    let checkInterval = setInterval(async () => {
        try {
            const res = await axios.get(`https://api.sms-activate.org/stst.php?api_key=${api_key}&action=getStatus&id=${activationId}`);
            
            if (res.data.includes('STATUS_OK')) {
                const code = res.data.split(':')[1];
                bot.sendMessage(chatId, `📩 وصل كود التفعيل الخاص بك:\n\n*${code}*`, { parse_mode: 'Markdown' });
                clearInterval(checkInterval);
            } else if (res.data === 'STATUS_CANCEL') {
                clearInterval(checkInterval);
            }
        } catch (e) {
            console.log("Error checking code");
        }
    }, 5000); // يفحص كل 5 ثواني

    // توقف الفحص بعد 15 دقيقة تلقائياً
    setTimeout(() => clearInterval(checkInterval), 900000);
}
const EMBEDDED_SITE_COOKIES = [
  {
    name: '_ga',
    value: 'GA1.1.785430697.1779376070',
    domain: '.basha.cc',
    path: '/',
    expires: 1813936084.045453,
    httpOnly: false,
    secure: false,
    sameSite: 'unspecified',
  },
  {
    name: '_ga_H66ED8VJ3T',
    value: 'GS2.1.s1779376070$o1$g1$t1779376084$j46$l0$h0',
    domain: '.basha.cc',
    path: '/',
    expires: 1813936084.099334,
    httpOnly: false,
    secure: false,
    sameSite: 'unspecified',
  },
  {
    name: 'basha_iprn_vas_session',
    value: 'eyJpdiI6IjRnYy9nWk5qcHVxZmhEMU9jZERvalE9PSIsInZhbHVlIjoiaXloTys5dkpPQUpNa0VXYTAxQUVXeDBCMnl4QU1iSlZqK0tYd3hXd3ExdUNmVVpyK2VkWG1iRmVQWWwzVVN6d0xBNFhkTEZJNXF3dlR5K1lWeXlPS0VlSHU1Y2tKLytnUFk4dFNMbVVkbmIxR0p0VjdXcDhFVjBOY3B2dWNKKzciLCJtYWMiOiI5NWI1MDJiODcwYzY0YzcwMGFlNWE1NjdjZjU0YjQ5OWM3ODdlNWY0NjIxOTMxOGNhYzUzNDA3YzczNTc1NjM4IiwidGFnIjoiIn0%3D',
    domain: 'basha.cc',
    path: '/',
    expires: 1779462485.135137,
    httpOnly: true,
    secure: false,
    sameSite: 'lax',
  },
  {
    name: 'cf_clearance',
    value: 'Bg9EW7bGK15Z1kyJWcBl8YQYMWDlS98w7r0rVY1FAf4-1779376070-1.2.1.1-OQNsc3yhbPltEZObGQIcV8Aayp_BllfZEWsrelwxzjqVX8M9GXc3PQO.PNfHo4cD_jCVwiSjlr0tq8RQERQ1N7vuYryfs21562yXRGqFYvYZ6daXLaSYkc.t.ypbBdGpBfBjZQpFMR9RiPupw1go1Nq1GC20EFYYgKmxrebUuijSoJ.8xplMYJnS2KdPCbVcNPjk49Rkr8cnHq8ZmreXXHf0JdkpJW67Qgjk3wOeByH7QOKATGWGWl3l7JotBrLDdZ1oDJJBHQrx.Sgyorzw_dtA54Sm1E84NMRqB8gzHV7cMcwiXhjapdKGoMvv1S5D7PzDuc0uHyWnBVKe8NcBCg',
    domain: '.basha.cc',
    path: '/',
    expires: 1810912070.443684,
    httpOnly: true,
    secure: true,
    sameSite: 'no_restriction',
  },
  {
    name: 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
    value: 'eyJpdiI6Ii95enZ2VkRqRlhVUGdIQ0Z4SFlBVVE9PSIsInZhbHVlIjoiajVaWHdLaWEzdzRkajNhL2ZwUUMwQXVCaGMwK0R3dUd5bEQ4Z2tsOWNaUWdwNTh4Njk3NWE4RWQ2eHE2ak80SFVTVU94M3lFRWNuNjVrNkFURklGQXpFc3poc0cxS1pHUXRtVHRsdzRaQXEzMkhCWEZJb2NOWjFsTjRlYXUzaGRic3cwSzZId3V5Z2lkQ29xVko0NnRxbDNITEpqeDdFVTB0REFFTldHNkpWSWVWRFZHeXQwKy9WOWVXYUVsVGg4VlVkdE1qTDNGalQxSVhxQ09VVW1heHhHdWNRUVFUc0xlbk1Ob3FJTWdKND0iLCJtYWMiOiIwOTYzZWVjMjEwMDgzOTNiZDRhOTNmMDFkNTUyMzM5YzdlOTdlZjU3Njg4YTkwZDgzNGNkZTFmNTM1N2E2NzdiIiwidGFnIjoiIn0%3D',
    domain: 'basha.cc',
    path: '/',
    expires: 1813936083.281991,
    httpOnly: true,
    secure: true,
    sameSite: 'lax',
  },
  {
    name: 'XSRF-TOKEN',
    value: 'eyJpdiI6IjJCT2VNSzJZRWlSQUg5RC9sdktTWUE9PSIsInZhbHVlIjoidFpEWjN5NFpkU1ZpTVZSUkFEZDYrUDFQcithSGkzbGtudS9FTHdxc0VHQXBtV2VJZmorSWp2N0dIbzRNakNFQjd1KzhVTVVyR0hoWFc4blBZRHQ2ZENTdndRUFdxZ2lWV1cvYXdMVG5JOFkvb0w0eTA5c3Vpc3JOYUVURU1qaEkiLCJtYWMiOiI5NmE3YWIzOTdkYjAzMjE0Njk1ZDA4NDY5OWEyNjE2YjdhY2NkM2NmZTQwMDY3YjY2MWQ2OWUwMzYwZmY1ODlkIiwidGFnIjoiIn0%3D',
    domain: 'basha.cc',
    path: '/',
    expires: 1779462485.134856,
    httpOnly: false,
    secure: true,
    sameSite: 'lax',
  },
];

const BASE_DIR = __dirname;
const STORAGE_DIR = path.join(BASE_DIR, 'storage');
const DATA_DIR = path.join(STORAGE_DIR, 'data');
const LOG_DIR = path.join(STORAGE_DIR, 'logs');
const USERS_FILE = path.join(DATA_DIR, 'users.json');
const NUMBERS_FILE = path.join(DATA_DIR, 'numbers.json');
const RUNTIME_COOKIES_FILE = path.join(DATA_DIR, 'runtime_cookies.json');
const STATE_FILE = path.join(DATA_DIR, 'state.json');

for (const dir of [STORAGE_DIR, DATA_DIR, LOG_DIR]) {
  fs.mkdirSync(dir, { recursive: true });
}

const SECRET_VALUES = [
  Environment.BOT_TOKEN,
  String(Environment.ADMIN_ID || ''),
  Environment.SITE_EMAIL,
  Environment.SITE_PASS,
  ...EMBEDDED_SITE_COOKIES.map((item) => item.value),
].filter(Boolean);

function redact(text) {
  let output = String(text ?? '');
  for (const secret of SECRET_VALUES) {
    if (!secret || secret.length < 6) continue;
    output = output.split(secret).join('[REDACTED]');
  }
  return output;
}

function logLine(level, message, extra = null) {
  const line = `[${new Date().toISOString()}] [${level}] ${redact(message)}${extra ? ` ${redact(JSON.stringify(extra))}` : ''}`;
  console.log(line);
  fs.appendFileSync(path.join(LOG_DIR, 'bot.log'), `${line}\n`, 'utf8');
}

const logger = {
  info: (msg, extra) => logLine('INFO', msg, extra),
  warn: (msg, extra) => logLine('WARN', msg, extra),
  error: (msg, extra) => logLine('ERROR', msg, extra),
};

function loadJson(filePath, fallback) {
  try {
    if (!fs.existsSync(filePath)) return fallback;
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (error) {
    logger.warn(`Failed to read JSON: ${filePath}`, { error: error.message });
    return fallback;
  }
}

function saveJson(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
}

function nowIso() {
  return new Date().toISOString();
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function escapeHtml(text) {
  return String(text ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function escapeMarkdown(text) {
  return String(text ?? '').replace(/([_\*\[\]\(\)~`>#+\-=|{}.!\\])/g, '\\$1');
}

function normalizeCookieItem(item) {
  if (!item || typeof item !== 'object') return null;
  const name = String(item.name || '').trim();
  const value = String(item.value || '');
  if (!name) return null;
  return {
    name,
    value,
    domain: String(item.domain || 'basha.cc').trim() || 'basha.cc',
    path: String(item.path || '/').trim() || '/',
    expires: typeof item.expires === 'number' ? item.expires : undefined,
    httpOnly: Boolean(item.httpOnly),
    secure: Boolean(item.secure),
    sameSite: item.sameSite ? String(item.sameSite) : undefined,
  };
}

function parseCookiePayload(rawText) {
  const raw = String(rawText || '').trim();
  if (!raw) return [];
  const parsed = JSON.parse(raw);
  const items = Array.isArray(parsed) ? parsed : Array.isArray(parsed.cookies) ? parsed.cookies : [];
  return items.map(normalizeCookieItem).filter(Boolean);
}

function mergeCookies(existingItems, newItems) {
  const map = new Map();
  for (const item of [...existingItems, ...newItems]) {
    const normalized = normalizeCookieItem(item);
    if (!normalized) continue;
    const key = `${normalized.domain}|${normalized.path}|${normalized.name}`.toLowerCase();
    map.set(key, normalized);
  }
  return Array.from(map.values());
}

async function applyCookiesToJar(jar, items) {
  for (const item of items) {
    const normalized = normalizeCookieItem(item);
    if (!normalized) continue;
    const domain = normalized.domain.startsWith('.') ? normalized.domain.slice(1) : normalized.domain;
    const protocol = normalized.secure ? 'https' : 'http';
    const cookieParts = [`${normalized.name}=${normalized.value}`, `Domain=${domain}`, `Path=${normalized.path}`];
    if (normalized.expires) {
      cookieParts.push(`Expires=${new Date(normalized.expires * 1000).toUTCString()}`);
    }
    if (normalized.httpOnly) cookieParts.push('HttpOnly');
    if (normalized.secure) cookieParts.push('Secure');
    await jar.setCookie(cookieParts.join('; '), `${protocol}://${domain}${normalized.path}`);
    if (normalized.secure) {
      await jar.setCookie(cookieParts.join('; '), `https://${domain}${normalized.path}`);
    }
  }
}

async function snapshotJarCookies(jar) {
  const cookies = await jar.getCookies(Environment.SITE_BASE_URL);
  return cookies.map((cookie) => ({
    name: cookie.key,
    value: cookie.value,
    domain: cookie.domain,
    path: cookie.path,
    expires: cookie.expires && cookie.expires !== 'Infinity' ? Math.floor(new Date(cookie.expires).getTime() / 1000) : undefined,
    httpOnly: cookie.httpOnly,
    secure: cookie.secure,
    sameSite: cookie.sameSite,
  }));
}

function createHttpClient(jar) {
  return wrapper(axiosLib.create({
    jar,
    withCredentials: true,
    timeout: Environment.REQUEST_TIMEOUT_MS,
    maxRedirects: 5,
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36',
      Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
      'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
      Connection: 'keep-alive',
    },
    validateStatus: () => true,
  }));
}

function extractCsrfToken(html) {
  const text = String(html || '');
  const meta = text.match(/<meta\s+name=["']csrf-token["']\s+content=["']([^"']+)["']/i);
  if (meta?.[1]) return meta[1];
  const input = text.match(/<input[^>]+name=["']_token["'][^>]+value=["']([^"']+)["']/i);
  if (input?.[1]) return input[1];
  return '';
}

function looksAuthenticated(html, finalUrl) {
  const text = String(html || '');
  return /Basha IPRN VAS - Test Numbers/i.test(text)
    || /Basha IPRN VAS - Dashboard/i.test(text)
    || String(finalUrl || '').includes('/home')
    || String(finalUrl || '').includes('/test/numbers');
}

async function loadRuntimeCookies() {
  return loadJson(RUNTIME_COOKIES_FILE, []);
}

async function saveRuntimeCookies(items) {
  saveJson(RUNTIME_COOKIES_FILE, items);
}

async function buildSiteSession() {
  const jar = new CookieJar();
  const client = createHttpClient(jar);
  const runtimeCookies = await loadRuntimeCookies();
  await applyCookiesToJar(jar, EMBEDDED_SITE_COOKIES);
  await applyCookiesToJar(jar, runtimeCookies);

  let response = await client.get(Environment.SITE_NUMBERS_PAGE, {
    headers: { Referer: Environment.SITE_LOGIN_URL },
  });

  if (looksAuthenticated(response.data, response.request?.res?.responseUrl || response.config?.url)) {
    const cookieDump = await snapshotJarCookies(jar);
    await saveRuntimeCookies(mergeCookies(runtimeCookies, cookieDump));
    return { jar, client, pageHtml: response.data };
  }

  logger.warn('Cookie session was not enough, trying credential login');
  const loginPage = await client.get(Environment.SITE_LOGIN_URL, { headers: { Referer: Environment.SITE_BASE_URL } });
  const csrf = extractCsrfToken(loginPage.data);
  const form = new URLSearchParams();
  if (csrf) form.set('_token', csrf);
  form.set('email', Environment.SITE_EMAIL);
  form.set('password', Environment.SITE_PASS);
  form.set('remember', 'on');

  const loginResp = await client.post(Environment.SITE_LOGIN_URL, form.toString(), {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      Origin: Environment.SITE_BASE_URL,
      Referer: Environment.SITE_LOGIN_URL,
      'X-CSRF-TOKEN': csrf,
      'X-Requested-With': 'XMLHttpRequest',
    },
  });

  if (loginResp.status >= 400) {
    throw new Error(`Login failed with status ${loginResp.status}`);
  }

  response = await client.get(Environment.SITE_NUMBERS_PAGE, {
    headers: { Referer: Environment.SITE_HOME_URL },
  });

  if (!looksAuthenticated(response.data, response.request?.res?.responseUrl || response.config?.url)) {
    throw new Error('Login succeeded partially but numbers page still not authenticated');
  }

  const cookieDump = await snapshotJarCookies(jar);
  await saveRuntimeCookies(mergeCookies(runtimeCookies, cookieDump));
  return { jar, client, pageHtml: response.data };
}

function guessCountry(rangeName) {
  const name = String(rangeName || '').trim();
  if (!name) return 'Unknown';
  const cleaned = name.replace(/[_/]+/g, ' ').replace(/\s+/g, ' ').trim();
  const firstChunk = cleaned.split(/[-|]/)[0]?.trim() || cleaned;
  const alphaMatch = firstChunk.match(/^[A-Za-z]+(?:\s+[A-Za-z]+){0,2}/);
  if (alphaMatch?.[0]) return alphaMatch[0].trim();
  const token = cleaned.split(/\s+/)[0];
  return token || 'Unknown';
}

function guessPlatform(rangeName) {
  const name = String(rangeName || '').trim();
  if (!name) return 'General';
  const withoutCountry = name.replace(/^([A-Za-z]+(?:\s+[A-Za-z]+){0,2})/, '').trim();
  const match = withoutCountry.match(/[A-Za-z]{2,}/g);
  if (match?.length) {
    return match.join(' ').trim() || 'General';
  }
  return 'General';
}

function parseActionButtons(actionHtml) {
  const html = String(actionHtml || '').trim();
  if (!html) return [];
  const $ = cheerio.load(html);
  const items = [];
  $('button').each((_, el) => {
    const node = $(el);
    const term = node.attr('data-term-label') || node.text().trim() || 'Action';
    items.push({
      term: term.trim(),
      price: node.attr('data-price') || '',
      available: Number(node.attr('data-available') || '0') || 0,
      reserveUrl: node.attr('data-reserve-url') || '',
      rangeName: node.attr('data-range-name') || '',
    });
  });
  return items;
}

function buildDataTableParams(start, length) {
  const params = {
    draw: '1',
    start: String(start),
    length: String(length),
    'search[value]': '',
    'search[regex]': 'false',
    'order[0][column]': '1',
    'order[0][dir]': 'desc',
  };
  ['action', 'id', 'range_name', 'available_numbers'].forEach((column, index) => {
    params[`columns[${index}][data]`] = column;
    params[`columns[${index}][name]`] = '';
    params[`columns[${index}][searchable]`] = 'true';
    params[`columns[${index}][orderable]`] = index !== 0 ? 'true' : 'false';
    params[`columns[${index}][search][value]`] = '';
    params[`columns[${index}][search][regex]`] = 'false';
  });
  return params;
}

async function fetchNumbersFromSite() {
  const { client, pageHtml } = await buildSiteSession();
  const csrf = extractCsrfToken(pageHtml);
  const pageSize = Math.min(Environment.MAX_PAGE_SIZE, Environment.MAX_ROWS);
  let start = 0;
  let total = 0;
  const collected = [];

  do {
    const response = await client.get(Environment.SITE_NUMBERS_DATA_URL, {
      params: buildDataTableParams(start, pageSize),
      headers: {
        Referer: Environment.SITE_NUMBERS_PAGE,
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRF-TOKEN': csrf,
        Accept: 'application/json, text/plain, */*',
      },
    });

    if (response.status >= 400) {
      throw new Error(`Numbers API failed with status ${response.status}`);
    }

    const payload = typeof response.data === 'string' ? JSON.parse(response.data) : response.data;
    total = Number(payload.recordsFiltered || payload.recordsTotal || 0);
    const rows = Array.isArray(payload.data) ? payload.data : [];

    for (const row of rows) {
      const rangeName = String(row.range_name || '').trim();
      const actions = parseActionButtons(row.action);
      collected.push({
        id: Number(row.id || 0),
        rangeName,
        availableNumbers: Number(row.available_numbers || 0),
        country: guessCountry(rangeName),
        platform: guessPlatform(rangeName),
        actions,
      });
    }

    start += rows.length;
    if (!rows.length) break;
    if (collected.length >= Environment.MAX_ROWS) break;
  } while (start < total);

  const deduped = [];
  const seen = new Set();
  for (const item of collected) {
    if (!item.id || seen.has(item.id)) continue;
    seen.add(item.id);
    deduped.push(item);
  }

  deduped.sort((a, b) => b.availableNumbers - a.availableNumbers || a.rangeName.localeCompare(b.rangeName));
  return {
    syncedAt: nowIso(),
    totalRows: deduped.length,
    items: deduped,
  };
}

function computeStats(dataset) {
  const stats = {
    totalRows: 0,
    totalAvailable: 0,
    countries: {},
    platforms: {},
  };
  for (const item of dataset.items || []) {
    stats.totalRows += 1;
    stats.totalAvailable += Number(item.availableNumbers || 0);
    stats.countries[item.country] = (stats.countries[item.country] || 0) + 1;
    stats.platforms[item.platform] = (stats.platforms[item.platform] || 0) + 1;
  }
  return stats;
}

function diffNewItems(oldDataset, newDataset) {
  const oldIds = new Set((oldDataset?.items || []).map((item) => item.id));
  return (newDataset.items || []).filter((item) => !oldIds.has(item.id));
}

async function syncNumbers() {
  const previous = loadJson(NUMBERS_FILE, { syncedAt: null, items: [] });
  const dataset = await fetchNumbersFromSite();
  dataset.stats = computeStats(dataset);
  dataset.hash = crypto.createHash('sha1').update(JSON.stringify(dataset.items)).digest('hex');
  saveJson(NUMBERS_FILE, dataset);

  const state = loadJson(STATE_FILE, {});
  state.lastSyncAt = dataset.syncedAt;
  state.lastHash = dataset.hash;
  saveJson(STATE_FILE, state);

  const newItems = diffNewItems(previous, dataset);
  return { dataset, previous, newItems };
}

function topEntries(obj, limit = 12) {
  return Object.entries(obj || {})
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, limit);
}

function datasetSummary(dataset) {
  const stats = dataset?.stats || computeStats(dataset || { items: [] });
  const topCountries = topEntries(stats.countries, 8).map(([name, count]) => `• ${name}: ${count}`).join('\n') || '• لا يوجد';
  const topPlatforms = topEntries(stats.platforms, 8).map(([name, count]) => `• ${name}: ${count}`).join('\n') || '• لا يوجد';
  return [
    `آخر مزامنة: ${dataset?.syncedAt || 'غير متوفر'}`,
    `عدد الصفوف: ${stats.totalRows}`,
    `إجمالي الأرقام المتاحة: ${stats.totalAvailable}`,
    '',
    'أعلى الدول:',
    topCountries,
    '',
    'أعلى المنصات:',
    topPlatforms,
  ].join('\n');
}

function loadUsers() {
  return loadJson(USERS_FILE, []);
}

function saveUsers(users) {
  saveJson(USERS_FILE, users);
}

function upsertUser(chat) {
  if (!chat?.id) return;
  const users = loadUsers();
  const existing = users.find((item) => item.id === chat.id);
  const payload = {
    id: chat.id,
    type: chat.type,
    title: chat.title || null,
    username: chat.username || null,
    first_name: chat.first_name || null,
    last_name: chat.last_name || null,
    updatedAt: nowIso(),
  };
  if (existing) {
    Object.assign(existing, payload);
  } else {
    users.push(payload);
  }
  saveUsers(users);
}

function isAdmin(msgOrId) {
  const userId = typeof msgOrId === 'number'
    ? msgOrId
    : Number(msgOrId?.from?.id || msgOrId?.chat?.id || 0);
  return userId === Environment.ADMIN_ID;
}

function getDataset() {
  const dataset = loadJson(NUMBERS_FILE, { syncedAt: null, items: [] });
  dataset.stats = dataset.stats || computeStats(dataset);
  return dataset;
}

function countryListKeyboard(page = 0) {
  const dataset = getDataset();
  const countries = topEntries(dataset.stats?.countries || {}, 200);
  const pageSize = 12;
  const pages = Math.max(1, Math.ceil(countries.length / pageSize));
  const current = Math.max(0, Math.min(page, pages - 1));
  const slice = countries.slice(current * pageSize, current * pageSize + pageSize);
  const rows = [];
  for (let i = 0; i < slice.length; i += 2) {
    rows.push(slice.slice(i, i + 2).map(([country, count]) => ({
      text: `${country} (${count})`,
      callback_data: `country:${encodeURIComponent(country)}:0`,
    })));
  }
  const nav = [];
  if (current > 0) nav.push({ text: '⬅️ السابق', callback_data: `countries:${current - 1}` });
  if (current < pages - 1) nav.push({ text: 'التالي ➡️', callback_data: `countries:${current + 1}` });
  if (nav.length) rows.push(nav);
  return { inline_keyboard: rows };
}

function rangeKeyboard(country, page = 0) {
  const dataset = getDataset();
  const rows = dataset.items.filter((item) => item.country === country);
  const pageSize = 8;
  const pages = Math.max(1, Math.ceil(rows.length / pageSize));
  const current = Math.max(0, Math.min(page, pages - 1));
  const slice = rows.slice(current * pageSize, current * pageSize + pageSize);
  const keyboard = slice.map((item) => [{
    text: `${item.rangeName} • ${item.availableNumbers}`,
    callback_data: `range:${item.id}`,
  }]);
  const nav = [];
  if (current > 0) nav.push({ text: '⬅️ السابق', callback_data: `country:${encodeURIComponent(country)}:${current - 1}` });
  if (current < pages - 1) nav.push({ text: 'التالي ➡️', callback_data: `country:${encodeURIComponent(country)}:${current + 1}` });
  if (nav.length) keyboard.push(nav);
  keyboard.push([{ text: '🔙 رجوع للدول', callback_data: 'countries:0' }]);
  return { inline_keyboard: keyboard };
}

function buildRangeMessage(item) {
  const actions = (item.actions || []).map((action) => {
    const parts = [action.term || 'Plan'];
    if (action.price) parts.push(`السعر: ${action.price}`);
    if (action.available) parts.push(`المتاح: ${action.available}`);
    return `• ${parts.join(' | ')}`;
  }).join('\n') || '• لا توجد خطط متاحة داخل الصف الحالي';

  return [
    `الاسم: ${item.rangeName}`,
    `الدولة: ${item.country}`,
    `المنصة: ${item.platform}`,
    `المتاح: ${item.availableNumbers}`,
    '',
    'الخطط:',
    actions,
  ].join('\n');
}

function buildRangeButtons(item) {
  const buttons = [];
  for (const action of item.actions || []) {
    if (!action.reserveUrl) continue;
    const label = `${action.term || 'Open'}${action.price ? ` • ${action.price}` : ''}`.slice(0, 64);
    buttons.push([{ text: label, url: action.reserveUrl }]);
  }
  buttons.push([{ text: '🔙 رجوع للدولة', callback_data: `country:${encodeURIComponent(item.country)}:0` }]);
  return { inline_keyboard: buttons };
}

async function sendSafe(bot, chatId, text, options = {}) {
  try {
    return await bot.sendMessage(chatId, text, options);
  } catch (error) {
    logger.warn('Telegram send failed', { chatId, error: error.message });
    return null;
  }
}

async function notifyAdmin(bot, text, options = {}) {
  if (!Environment.ADMIN_ID) return null;
  return sendSafe(bot, Environment.ADMIN_ID, text, options);
}

async function handleStart(bot, msg) {
  upsertUser(msg.chat);
  const dataset = getDataset();
  const stats = dataset.stats || computeStats(dataset);
  const text = [
    'أهلاً بك في بوت Basha Numbers.',
    '',
    `عدد الصفوف الحالية: ${stats.totalRows}`,
    `إجمالي الأرقام المتاحة: ${stats.totalAvailable}`,
    `آخر مزامنة: ${dataset.syncedAt || 'لم تتم بعد'}`,
    '',
    'استخدم الأزرار لاختيار الدولة أو الأوامر التالية:',
    '/numbers - عرض الدول',
    '/status - حالة البوت',
    '/platforms - أعلى المنصات',
  ].join('\n');
  await sendSafe(bot, msg.chat.id, text, { reply_markup: countryListKeyboard(0) });
}

async function handleStatus(bot, msg) {
  const dataset = getDataset();
  await sendSafe(bot, msg.chat.id, datasetSummary(dataset));
}

async function handlePlatforms(bot, msg) {
  const dataset = getDataset();
  const lines = topEntries(dataset.stats?.platforms || {}, 30).map(([name, count]) => `• ${name}: ${count}`);
  await sendSafe(bot, msg.chat.id, lines.length ? lines.join('\n') : 'لا توجد منصات متاحة حالياً.');
}

async function handleNumbers(bot, msg) {
  const dataset = getDataset();
  if (!dataset.items?.length) {
    await sendSafe(bot, msg.chat.id, 'لا توجد بيانات محفوظة حالياً. استخدم /sync أولاً.');
    return;
  }
  await sendSafe(bot, msg.chat.id, 'اختر الدولة:', { reply_markup: countryListKeyboard(0) });
}

const pendingActions = new Map();

async function ensureAdmin(bot, msg) {
  if (isAdmin(msg)) return true;
  await sendSafe(bot, msg.chat.id, 'هذا الأمر للمطور فقط.');
  return false;
}

async function handleShowCookies(bot, msg) {
  if (!(await ensureAdmin(bot, msg))) return;
  const runtime = loadJson(RUNTIME_COOKIES_FILE, []);
  const summarize = (items) => items.map((item, idx) => `${idx + 1}. ${item.name} @ ${item.domain}${item.path}`).join('\n');
  const text = [
    `Runtime cookies: ${runtime.length}`,
    runtime.length ? summarize(runtime) : 'لا توجد runtime cookies محفوظة.',
    '',
    `Embedded cookies: ${EMBEDDED_SITE_COOKIES.length}`,
    summarize(EMBEDDED_SITE_COOKIES),
  ].join('\n');
  await sendSafe(bot, msg.chat.id, text);
}

async function handleSetCookies(bot, msg, append = false) {
  if (!(await ensureAdmin(bot, msg))) return;
  pendingActions.set(msg.chat.id, { type: append ? 'addcookies' : 'setcookies' });
  await sendSafe(bot, msg.chat.id, append
    ? 'ابعت JSON الكوكيز لإضافتها فوق الحالية.'
    : 'ابعت JSON الكوكيز لاستبدال runtime cookies بالكامل.');
}

async function handleClearCookies(bot, msg) {
  if (!(await ensureAdmin(bot, msg))) return;
  saveJson(RUNTIME_COOKIES_FILE, []);
  await sendSafe(bot, msg.chat.id, 'تم حذف runtime cookies بنجاح.');
}

async function handleSync(bot, msg, silent = false) {
  if (!(await ensureAdmin(bot, msg))) return;
  if (!silent) await sendSafe(bot, msg.chat.id, 'جاري مزامنة البيانات من Basha...');
  try {
    const { dataset, newItems } = await syncNumbers();
    const summary = datasetSummary(dataset);
    const extra = newItems.length
      ? `\n\nصفوف جديدة: ${newItems.length}\n${newItems.slice(0, 10).map((item) => `• ${item.rangeName} (${item.availableNumbers})`).join('\n')}`
      : '\n\nلا توجد صفوف جديدة مقارنة بآخر نسخة.';
    await sendSafe(bot, msg.chat.id, `${summary}${extra}`);
  } catch (error) {
    logger.error('Manual sync failed', { error: error.message });
    await sendSafe(bot, msg.chat.id, `فشل التحديث: ${error.message}`);
  }
}

async function processPendingAction(bot, msg) {
  const pending = pendingActions.get(msg.chat.id);
  if (!pending) return false;
  pendingActions.delete(msg.chat.id);
  try {
    const newItems = parseCookiePayload(msg.text || '');
    if (!newItems.length) throw new Error('لم يتم العثور على كوكيز صالحة داخل JSON');
    const current = loadJson(RUNTIME_COOKIES_FILE, []);
    const output = pending.type === 'addcookies' ? mergeCookies(current, newItems) : newItems;
    saveJson(RUNTIME_COOKIES_FILE, output);
    await sendSafe(bot, msg.chat.id, `تم حفظ ${output.length} كوكيز بنجاح.`);
  } catch (error) {
    await sendSafe(bot, msg.chat.id, `فشل حفظ الكوكيز: ${error.message}`);
  }
  return true;
}

async function broadcastNewItems(bot, newItems, dataset) {
  if (!newItems.length) return;
  const lines = newItems.slice(0, 15).map((item) => `• ${item.rangeName} | ${item.country} | ${item.availableNumbers}`);
  const text = [
    'تم اكتشاف صفوف جديدة في basha.cc',
    '',
    ...lines,
    '',
    `إجمالي الجديد: ${newItems.length}`,
    `وقت المزامنة: ${dataset.syncedAt}`,
  ].join('\n');
  await notifyAdmin(bot, text);
}

function startHealthServer() {
  const server = http.createServer((req, res) => {
    const dataset = getDataset();
    const body = JSON.stringify({
      ok: true,
      now: nowIso(),
      lastSync: dataset.syncedAt || null,
      totalRows: dataset.items?.length || 0,
    }, null, 2);
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(body);
  });
  server.listen(Environment.PORT, Environment.HOST, () => {
    logger.info(`Health server running on ${Environment.HOST}:${Environment.PORT}`);
  });
}

async function runInitialSync(bot = null) {
  try {
    const { dataset, newItems } = await syncNumbers();
    logger.info(`Initial sync done with ${dataset.totalRows} rows`);
    if (bot) await broadcastNewItems(bot, newItems, dataset);
  } catch (error) {
    logger.error('Initial sync failed', { error: error.message });
    if (bot) await notifyAdmin(bot, `فشل التحديث الأولي: ${error.message}`);
  }
}

async function startAutoSync(bot) {
  while (true) {
    await sleep(Environment.AUTO_SYNC_SECONDS * 1000);
    try {
      const { dataset, newItems } = await syncNumbers();
      logger.info(`Auto sync done. rows=${dataset.totalRows} new=${newItems.length}`);
      await broadcastNewItems(bot, newItems, dataset);
    } catch (error) {
      logger.error('Auto sync failed', { error: error.message });
      await notifyAdmin(bot, `فشل التحديث التلقائي: ${error.message}`);
    }
  }
}

async function runSelfTest() {
  logger.info('Running self test mode');
  const { dataset } = await syncNumbers();
  console.log(JSON.stringify({
    ok: true,
    syncedAt: dataset.syncedAt,
    totalRows: dataset.totalRows,
    totalAvailable: dataset.stats.totalAvailable,
    topCountries: topEntries(dataset.stats.countries, 5),
  }, null, 2));
}

async function main() {
  if (Environment.SELF_TEST) {
    await runSelfTest();
    return;
  }

  if (!Environment.BOT_TOKEN) {
    throw new Error('BOT_TOKEN is missing');
  }

  startHealthServer();

  const bot = new TelegramBot(Environment.BOT_TOKEN, { polling: true });
  logger.info('Telegram bot started');

  bot.onText(/^\/start(?:@\w+)?$/, (msg) => void handleStart(bot, msg));
  bot.onText(/^\/status(?:@\w+)?$/, (msg) => void handleStatus(bot, msg));
  bot.onText(/^\/numbers(?:@\w+)?$/, (msg) => void handleNumbers(bot, msg));
  bot.onText(/^\/platforms(?:@\w+)?$/, (msg) => void handlePlatforms(bot, msg));
  bot.onText(/^\/showcookies(?:@\w+)?$/, (msg) => void handleShowCookies(bot, msg));
  bot.onText(/^\/setcookies(?:@\w+)?$/, (msg) => void handleSetCookies(bot, msg, false));
  bot.onText(/^\/addcookies(?:@\w+)?$/, (msg) => void handleSetCookies(bot, msg, true));
  bot.onText(/^\/clearcookies(?:@\w+)?$/, (msg) => void handleClearCookies(bot, msg));
  bot.onText(/^\/sync(?:@\w+)?$/, (msg) => void handleSync(bot, msg));

  bot.on('message', async (msg) => {
    try {
      upsertUser(msg.chat);
      if (!msg.text) return;
      if (msg.text.startsWith('/')) return;
      await processPendingAction(bot, msg);
    } catch (error) {
      logger.error('Message handler failed', { error: error.message });
    }
  });

  bot.on('callback_query', async (query) => {
    try {
      const data = String(query.data || '');
      if (data.startsWith('countries:')) {
        const page = Number(data.split(':')[1] || '0') || 0;
        await bot.editMessageText('اختر الدولة:', {
          chat_id: query.message.chat.id,
          message_id: query.message.message_id,
          reply_markup: countryListKeyboard(page),
        });
      } else if (data.startsWith('country:')) {
        const [, encodedCountry, pageText] = data.split(':');
        const country = decodeURIComponent(encodedCountry || '');
        const page = Number(pageText || '0') || 0;
        await bot.editMessageText(`الأرقام المتاحة داخل ${country}:`, {
          chat_id: query.message.chat.id,
          message_id: query.message.message_id,
          reply_markup: rangeKeyboard(country, page),
        });
      } else if (data.startsWith('range:')) {
        const id = Number(data.split(':')[1] || '0');
        const item = getDataset().items.find((row) => row.id === id);
        if (!item) {
          await bot.answerCallbackQuery(query.id, { text: 'العنصر غير موجود', show_alert: true });
          return;
        }
        await bot.editMessageText(buildRangeMessage(item), {
          chat_id: query.message.chat.id,
          message_id: query.message.message_id,
          reply_markup: buildRangeButtons(item),
        });
      }
      await bot.answerCallbackQuery(query.id);
    } catch (error) {
      logger.error('Callback handler failed', { error: error.message });
      try {
        await bot.answerCallbackQuery(query.id, { text: 'حصل خطأ داخلي', show_alert: true });
      } catch (_) {
        // ignore
      }
    }
  });

  bot.on('polling_error', (error) => {
    logger.error('Polling error', { error: error.message });
  });

  await runInitialSync(bot);
  void startAutoSync(bot);
}

main().catch((error) => {
  logger.error('Fatal error', { error: error.message, stack: error.stack });
  process.exit(1);
});
