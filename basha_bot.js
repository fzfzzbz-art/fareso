'use strict';

const fs = require('fs');
const fsp = require('fs/promises');
const path = require('path');
const http = require('http');
const crypto = require('crypto');
const dotenv = require('dotenv');
const axiosLib = require('axios');
const { wrapper } = require('axios-cookiejar-support');
const { CookieJar } = require('tough-cookie');
const cheerio = require('cheerio');
const TelegramBot = require('node-telegram-bot-api');

dotenv.config();

const Environment = {
  BOT_TOKEN: process.env.BOT_TOKEN || '8674488533:AAGAg2PBEOmrCs00cxMdBeGNZp00a1z0Xb8',
  ADMIN_ID: Number(process.env.ADMIN_ID || '7231690686'),
  SITE_BASE_URL: process.env.SITE_BASE_URL || 'https://basha.cc',
  SITE_LOGIN_URL: process.env.SITE_LOGIN_URL || 'https://basha.cc/login',
  SITE_HOME_URL: process.env.SITE_HOME_URL || 'https://basha.cc/home',
  SITE_NUMBERS_PAGE: process.env.SITE_NUMBERS_PAGE || 'https://basha.cc/test/numbers',
  SITE_NUMBERS_DATA_URL: process.env.SITE_NUMBERS_DATA_URL || 'https://basha.cc/test/numbers/data',
  SITE_EMAIL: process.env.SITE_EMAIL || 'ftatty88@gmail.com',
  SITE_PASS: process.env.SITE_PASS || '123456789ff',
  AUTO_SYNC_SECONDS: Math.max(60, Number(process.env.AUTO_SYNC_SECONDS || '300')),
  HOST: process.env.HOST || '0.0.0.0',
  PORT: Number(process.env.PORT || '8080'),
  REQUEST_TIMEOUT_MS: Math.max(10000, Number(process.env.REQUEST_TIMEOUT_MS || '45000')),
  MAX_PAGE_SIZE: Math.max(100, Number(process.env.MAX_PAGE_SIZE || '500')),
  MAX_ROWS: Math.max(100, Number(process.env.MAX_ROWS || '5000')),
  SELF_TEST: String(process.env.SELF_TEST || '').trim() === '1',
  TZ: process.env.TZ || 'UTC',
};

const EMBEDDED_SITE_COOKIES = [
  { name: '_ga', value: 'GA1.1.785430697.1779376070', domain: '.basha.cc', path: '/', expires: 1813936084.045453, httpOnly: false, secure: false, sameSite: 'unspecified' },
  { name: '_ga_H66ED8VJ3T', value: 'GS2.1.s1779376070$o1$g1$t1779376084$j46$l0$h0', domain: '.basha.cc', path: '/', expires: 1813936084.099334, httpOnly: false, secure: false, sameSite: 'unspecified' },
  { name: 'basha_iprn_vas_session', value: 'eyJpdiI6IjRnYy9nWk5qcHVxZmhEMU9jZERvalE9PSIsInZhbHVlIjoiaXloTys5dkpPQUpNa0VXYTAxQUVXeDBCMnl4QU1iSlZqK0tYd3hXd3ExdUNmVVpyK2VkWG1iRmVQWWwzVVN6d0xBNFhkTEZJNXF3dlR5K1lWeXlPS0VlSHU1Y2tKLytnUFk4dFNMbVVkbmIxR0p0VjdXcDhFVjBOY3B2dWNKKzciLCJtYWMiOiI5NWI1MDJiODcwYzY0YzcwMGFlNWE1NjdjZjU0YjQ5OWM3ODdlNWY0NjIxOTMxOGNhYzUzNDA3YzczNTc1NjM4IiwidGFnIjoiIn0%3D', domain: 'basha.cc', path: '/', expires: 1779462485.135137, httpOnly: true, secure: false, sameSite: 'lax' },
  { name: 'cf_clearance', value: 'Bg9EW7bGK15Z1kyJWcBl8YQYMWDlS98w7r0rVY1FAf4-1779376070-1.2.1.1-OQNsc3yhbPltEZObGQIcV8Aayp_BllfZEWsrelwxzjqVX8M9GXc3PQO.PNfHo4cD_jCVwiSjlr0tq8RQERQ1N7vuYryfs21562yXRGqFYvYZ6daXLaSYkc.t.ypbBdGpBfBjZQpFMR9RiPupw1go1Nq1GC20EFYYgKmxrebUuijSoJ.8xplMYJnS2KdPCbVcNPjk49Rkr8cnHq8ZmreXXHf0JdkpJW67Qgjk3wOeByH7QOKATGWGWl3l7JotBrLDdZ1oDJJBHQrx.Sgyorzw_dtA54Sm1E84NMRqB8gzHV7cMcwiXhjapdKGoMvv1S5D7PzDuc0uHyWnBVKe8NcBCg', domain: '.basha.cc', path: '/', expires: 1810912070.443684, httpOnly: true, secure: true, sameSite: 'no_restriction' },
  { name: 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d', value: 'eyJpdiI6Ii95enZ2VkRqRlhVUGdIQ0Z4SFlBVVE9PSIsInZhbHVlIjoiajVaWHdLaWEzdzRkajNhL2ZwUUMwQXVCaGMwK0R3dUd5bEQ4Z2tsOWNaUWdwNTh4Njk3NWE4RWQ2eHE2ak80SFVTVU94M3lFRWNuNjVrNkFURklGQXpFc3poc0cxS1pHUXRtVHRsdzRaQXEzMkhCWEZJb2NOWjFsTjRlYXUzaGRic3cwSzZId3V5Z2lkQ29xVko0NnRxbDNITEpqeDdFVTB0REFFTldHNkpWSWVWRFZHeXQwKy9WOWVXYUVsVGg4VlVkdE1qTDNGalQxSVhxQ09VVW1heHhHdWNRUVFUc0xlbk1Ob3FJTWdKND0iLCJtYWMiOiIwOTYzZWVjMjEwMDgzOTNiZDRhOTNmMDFkNTUyMzM5YzdlOTdlZjU3Njg4YTkwZDgzNGNkZTFmNTM1N2E2NzdiIiwidGFnIjoiIn0%3D', domain: 'basha.cc', path: '/', expires: 1813936083.281991, httpOnly: true, secure: true, sameSite: 'lax' },
  { name: 'XSRF-TOKEN', value: 'eyJpdiI6IjJCT2VNSzJZRWlSQUg5RC9sdktTWUE9PSIsInZhbHVlIjoidFpEWjN5NFpkU1ZpTVZSUkFEZDYrUDFQcithSGkzbGtudS9FTHdxc0VHQXBtV2VJZmorSWp2N0dIbzRNakNFQjd1KzhVTVVyR0hoWFc4blBZRHQ2ZENTdndRUFdxZ2lWV1cvYXdMVG5JOFkvb0w0eTA5c3Vpc3JOYUVURU1qaEkiLCJtYWMiOiI5NmE3YWIzOTdkYjAzMjE0Njk1ZDA4NDY5OWEyNjE2YjdhY2NkM2NmZTQwMDY3YjY2MWQ2OWUwMzYwZmY1ODlkIiwidGFnIjoiIn0%3D', domain: 'basha.cc', path: '/', expires: 1779462485.134856, httpOnly: false, secure: true, sameSite: 'lax' },
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

const logger = {
  info: (msg, extra) => console.log(`[INFO] ${msg}`, extra || ''),
  warn: (msg, extra) => console.log(`[WARN] ${msg}`, extra || ''),
  error: (msg, extra) => console.log(`[ERROR] ${msg}`, extra || ''),
};

function loadJson(filePath, fallback) {
  try {
    if (!fs.existsSync(filePath)) return fallback;
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (error) {
    return fallback;
  }
}

function saveJson(filePath, data) {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
}

function nowIso() { return new Date().toISOString(); }
function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

async function applyCookiesToJar(jar, items) {
  for (const item of items) {
    const domain = item.domain.startsWith('.') ? item.domain.slice(1) : item.domain;
    const protocol = item.secure ? 'https' : 'http';
    const cookieParts = [`${item.name}=${item.value}`, `Domain=${domain}`, `Path=${item.path}`];
    await jar.setCookie(cookieParts.join('; '), `${protocol}://${domain}${item.path}`);
  }
}

function createHttpClient(jar) {
  return wrapper(axiosLib.create({
    jar, withCredentials: true, timeout: Environment.REQUEST_TIMEOUT_MS,
    headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36' },
    validateStatus: () => true,
  }));
}

function extractCsrfToken(html) {
  const meta = String(html).match(/<meta\s+name=["']csrf-token["']\s+content=["']([^"']+)["']/i);
  return meta?.[1] || '';
}

async function buildSiteSession() {
  const jar = new CookieJar();
  const client = createHttpClient(jar);
  const runtimeCookies = loadJson(RUNTIME_COOKIES_FILE, []);
  await applyCookiesToJar(jar, EMBEDDED_SITE_COOKIES);
  await applyCookiesToJar(jar, runtimeCookies);
  const response = await client.get(Environment.SITE_NUMBERS_PAGE);
  return { jar, client, pageHtml: response.data, csrf: extractCsrfToken(response.data) };
}

function guessCountry(rangeName) {
  const cleaned = String(rangeName).replace(/[_/]+/g, ' ').trim();
  return cleaned.split(/[-|]/)[0]?.trim() || 'Unknown';
}

function guessPlatform(rangeName) {
  const cleaned = String(rangeName).toLowerCase();
  if (cleaned.includes('whatsapp')) return 'WhatsApp';
  if (cleaned.includes('telegram')) return 'Telegram';
  if (cleaned.includes('facebook')) return 'Facebook';
  if (cleaned.includes('google')) return 'Google';
  if (cleaned.includes('instagram')) return 'Instagram';
  if (cleaned.includes('tiktok')) return 'TikTok';
  return 'Other';
}

async function syncNumbers() {
  const { client, pageHtml, csrf } = await buildSiteSession();
  const response = await client.get(Environment.SITE_NUMBERS_DATA_URL, {
    params: { draw: '1', start: '0', length: '5000' },
    headers: { 'X-CSRF-TOKEN': csrf, 'X-Requested-With': 'XMLHttpRequest' }
  });
  const rows = response.data?.data || [];
  const items = rows.map(row => {
    const $ = cheerio.load(row.action);
    const actions = [];
    $('button').each((_, el) => {
      const b = $(el);
      actions.push({
        term: b.attr('data-term-label') || b.text().trim(),
        price: b.attr('data-price'),
        reserveUrl: b.attr('data-reserve-url'),
        id: b.attr('data-id')
      });
    });
    return {
      id: row.id,
      rangeName: row.range_name,
      availableNumbers: row.available_numbers,
      country: guessCountry(row.range_name),
      platform: guessPlatform(row.range_name),
      actions
    };
  });
  const dataset = { syncedAt: nowIso(), items };
  saveJson(NUMBERS_FILE, dataset);
  return dataset;
}

function getDataset() { return loadJson(NUMBERS_FILE, { items: [] }); }

// Keyboard Builders
function platformKeyboard() {
  const dataset = getDataset();
  const platforms = [...new Set(dataset.items.map(i => i.platform))];
  const rows = [];
  for (let i = 0; i < platforms.length; i += 2) {
    rows.push(platforms.slice(i, i + 2).map(p => ({ text: p, callback_data: `p:${p}` })));
  }
  return { inline_keyboard: rows };
}

function countryKeyboard(platform, page = 0) {
  const dataset = getDataset();
  const countries = [...new Set(dataset.items.filter(i => i.platform === platform).map(i => i.country))];
  const pageSize = 12;
  const slice = countries.slice(page * pageSize, (page + 1) * pageSize);
  const rows = [];
  for (let i = 0; i < slice.length; i += 2) {
    rows.push(slice.slice(i, i + 2).map(c => ({ text: c, callback_data: `c:${platform}:${c}` })));
  }
  const nav = [];
  if (page > 0) nav.push({ text: '⬅️', callback_data: `p:${platform}:${page - 1}` });
  if ((page + 1) * pageSize < countries.length) nav.push({ text: '➡️', callback_data: `p:${platform}:${page + 1}` });
  if (nav.length) rows.push(nav);
  rows.push([{ text: '🔙 رجوع', callback_data: 'start' }]);
  return { inline_keyboard: rows };
}

function rangeKeyboard(platform, country) {
  const dataset = getDataset();
  const items = dataset.items.filter(i => i.platform === platform && i.country === country);
  const rows = items.map(item => [{
    text: `${item.rangeName} (${item.availableNumbers})`,
    callback_data: `r:${item.id}`
  }]);
  rows.push([{ text: '🔙 رجوع', callback_data: `p:${platform}` }]);
  return { inline_keyboard: rows };
}

const activeReservations = new Map();

async function handleReservation(bot, chatId, action) {
  const { client, csrf } = await buildSiteSession();
  const resp = await client.post(action.reserveUrl, {}, { headers: { 'X-CSRF-TOKEN': csrf, 'X-Requested-With': 'XMLHttpRequest' } });
  
  if (resp.data?.status === 'success' || resp.data?.number) {
    const number = resp.data.number || 'جاري جلب الرقم...';
    const reservationId = resp.data.id;
    activeReservations.set(chatId, { id: reservationId, number, action, lastCode: null });
    
    const text = `✅ تم حجز الرقم بنجاح!\n\nالرقم: \`${number}\`\nالمنصة: ${action.term}\n\nسأقوم بإرسال الكود هنا فور وصوله تلقائياً.`;
    const keyboard = { inline_keyboard: [
      [{ text: '🔄 تغيير الرقم', callback_data: `change:${action.id}` }],
      [{ text: '🔙 القائمة الرئيسية', callback_data: 'start' }]
    ]};
    
    await bot.sendMessage(chatId, text, { parse_mode: 'Markdown', reply_markup: keyboard });
    startCodePolling(bot, chatId, reservationId);
  } else {
    await bot.sendMessage(chatId, `❌ فشل حجز الرقم: ${resp.data?.message || 'سبب غير معروف'}`);
  }
}

async function startCodePolling(bot, chatId, reservationId) {
  let attempts = 0;
  const maxAttempts = 60; // 10 minutes (10s interval)
  
  const poll = async () => {
    const res = activeReservations.get(chatId);
    if (!res || res.id !== reservationId) return;
    
    try {
      const { client } = await buildSiteSession();
      const resp = await client.get(`${Environment.SITE_BASE_URL}/test/numbers/reservations/${reservationId}`);
      const $ = cheerio.load(resp.data);
      const code = $('.code-display').text().trim() || null; // This selector might need adjustment based on site HTML
      
      if (code && code !== res.lastCode) {
        res.lastCode = code;
        await bot.sendMessage(chatId, `📩 وصل كود التحقق للرقم \`${res.number}\`:\n\n*${code}*`, { parse_mode: 'Markdown' });
        // We don't stop polling yet in case there are multiple codes
      }
    } catch (e) {}
    
    attempts++;
    if (attempts < maxAttempts) setTimeout(poll, 10000);
    else activeReservations.delete(chatId);
  };
  poll();
}

const bot = new TelegramBot(Environment.BOT_TOKEN, { polling: true });

bot.onText(/\/start/, (msg) => {
  bot.sendMessage(msg.chat.id, 'مرحباً بك! اختر القسم المطلوب:', { reply_markup: platformKeyboard() });
});

bot.on('callback_query', async (query) => {
  const chatId = query.message.chat.id;
  const data = query.data;

  if (data === 'start') {
    await bot.editMessageText('اختر القسم المطلوب:', { chat_id: chatId, message_id: query.message.message_id, reply_markup: platformKeyboard() });
  } else if (data.startsWith('p:')) {
    const [, platform, page] = data.split(':');
    await bot.editMessageText(`اختر الدولة لـ ${platform}:`, { chat_id: chatId, message_id: query.message.message_id, reply_markup: countryKeyboard(platform, Number(page || 0)) });
  } else if (data.startsWith('c:')) {
    const [, platform, country] = data.split(':');
    await bot.editMessageText(`اختر النوع لـ ${country} (${platform}):`, { chat_id: chatId, message_id: query.message.message_id, reply_markup: rangeKeyboard(platform, country) });
  } else if (data.startsWith('r:')) {
    const id = Number(data.split(':')[1]);
    const item = getDataset().items.find(i => i.id === id);
    if (item && item.actions.length > 0) {
      await handleReservation(bot, chatId, item.actions[0]);
    }
  } else if (data.startsWith('change:')) {
    const actionId = data.split(':')[1];
    const dataset = getDataset();
    let foundAction = null;
    for (const item of dataset.items) {
      foundAction = item.actions.find(a => a.id == actionId);
      if (foundAction) break;
    }
    if (foundAction) await handleReservation(bot, chatId, foundAction);
  }
  bot.answerCallbackQuery(query.id);
});

syncNumbers().then(() => logger.info('Initial sync completed')).catch(e => logger.error('Initial sync failed', e));
setInterval(syncNumbers, Environment.AUTO_SYNC_SECONDS * 1000);

console.log('Bot is running...');
