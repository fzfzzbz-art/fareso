// أضف هذا الرابط في قسم Environment في بداية الكود
Environment.SITE_MESSAGES_URL = 'https://basha.cc/my/messages';

/**
 * وظيفة حجز الرقم ومتابعة وصول الكود من الجدول
 */
async function handleReserve(bot, query, reserveUrl) {
  const chatId = query.message.chat.id;
  const messageId = query.message.message_id;

  try {
    const { client } = await buildSiteSession();

    // 1. تنفيذ طلب الحجز
    await bot.editMessageText('⏳ جاري حجز الرقم...', { chat_id: chatId, message_id: messageId });
    const reserveResp = await client.get(reserveUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });

    if (reserveResp.status >= 400) throw new Error('فشل الحجز، تأكد من وجود رصيد.');

    // 2. المراقبة: البحث عن الرقم في صفحة الرسائل
    let attempts = 0;
    const maxAttempts = 30; // مراقبة لمدة دقيقتين ونصف
    let lastFoundCode = null;

    await bot.editMessageText('✅ تم الحجز. بانتظار ظهور الرقم والكود في الجدول...', { chat_id: chatId, message_id: messageId });

    const pollInterval = setInterval(async () => {
      attempts++;
      try {
        const msgPage = await client.get(Environment.SITE_MESSAGES_URL);
        const $ = cheerio.load(msgPage.data);
        
        // استهداف أول صف في الجدول (أحدث رسالة)
        const firstRow = $('table tbody tr').first();
        const number = firstRow.find('td:nth-child(2)').text().trim(); // عمود Destination Number
        const messageText = firstRow.find('td:nth-child(4)').text().trim(); // عمود Message Text

        if (!number || number === "") {
            if (attempts >= maxAttempts) {
                clearInterval(pollInterval);
                await bot.sendMessage(chatId, "⚠️ انتهى الوقت ولم يظهر أي رقم جديد في الجدول.");
            }
            return; 
        }

        // استخراج الكود من النص (غالباً يكون أرقام)
        const codeMatch = messageText.match(/\d{3}-?\d{3}/); // يبحث عن صيغة 123-456 أو 123456
        const displayCode = codeMatch ? codeMatch[0] : (messageText || "بانتظار الكود...");

        if (codeMatch || (messageText.length > 5 && messageText !== lastFoundCode)) {
          clearInterval(pollInterval);
          await bot.editMessageText(
            `✅ **وصلت الرسالة الجديدة!**\n\n` +
            `📞 الرقم: \`${number}\`\n` +
            `📩 الرسالة: \`${messageText}\`\n\n` +
            `*اضغط على الرقم أو الكود لنسخه*`,
            { chat_id: chatId, message_id: messageId, parse_mode: 'Markdown' }
          );
        } else {
          // تحديث الحالة للمستخدم
          await bot.editMessageText(
            `⏳ جاري المراقبة...\n` +
            `📞 الرقم المحجوز: \`${number}\`\n` +
            `حالة الكود: بانتظار الرسالة (محاولة ${attempts}/${maxAttempts})`,
            { chat_id: chatId, message_id: messageId, parse_mode: 'Markdown' }
          );
        }
      } catch (err) {
        logger.error('Polling error', { error: err.message });
      }

      if (attempts >= maxAttempts) {
        clearInterval(pollInterval);
        await bot.sendMessage(chatId, "❌ توقفت المراقبة. إذا وصل الكود لاحقاً ستجده في الموقع.");
      }
    }, 5000);

  } catch (error) {
    logger.error('Reserve process failed', { error: error.message });
    await bot.sendMessage(chatId, `❌ فشل: ${error.message}`);
  }
}

/**
 * تعديل الأزرار لترسل طلب الحجز للبوت
 */
function buildRangeButtons(item) {
  const buttons = [];
  for (const action of item.actions || []) {
    if (!action.reserveUrl) continue;
    // نقوم بتشفير الرابط ليرسله البوت كـ Callback
    const callbackData = `buy:${Buffer.from(action.reserveUrl).toString('base64').slice(0, 30)}`; 
    // ملاحظة: تليجرام يحدد طول callback_data بـ 64 بت، لذا قد نحتاج لحفظ الرابط في Map
    
    const label = `طلب: ${action.term} | ${action.price}`;
    buttons.push([{ text: label, callback_data: `buy_id:${item.id}:${action.term}` }]);
  }
  buttons.push([{ text: '🔙 رجوع للدولة', callback_data: `country:${encodeURIComponent(item.country)}:0` }]);
  return { inline_keyboard: buttons };
}
