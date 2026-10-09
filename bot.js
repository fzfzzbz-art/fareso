const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs');
const path = require('path');
const axios = require('axios');
const AdmZip = require('adm-zip');

// استبدل التوكن بالتوكن الخاص بوتك
const token = '8738377353:AAEOzFJQM-ZD3fnIOPbcS46gmytkodfqPcQ';
const bot = new TelegramBot(token, { polling: true });

// استبدل هذا الرقم بآيدي حسابك الشخصي لتسمح لنفسك فقط برفع الملفات (حماية للبوت)
const ADMIN_ID = 7231690686; 

console.log('Bot is running...');

bot.on('document', async (msg) => {
    const chatId = msg.chat.id;
    const userId = msg.from.id;

    // التحقق من أن المستخدم هو المالك
    if (userId !== ADMIN_ID) {
        return bot.sendMessage(chatId, 'عذراً، هذا البوت مخصص للمالك فقط.');
    }

    const document = msg.document;
    const fileName = document.file_name;
    const fileId = document.file_id;

    // التحقق أن الملف بصيغة zip
    if (!fileName.endsWith('.zip')) {
        return bot.sendMessage(chatId, '❌ يرجى إرسال ملف مضغوط بصيغة .zip فقط.');
    }

    try {
        await bot.sendMessage(chatId, `📥 جاري تحميل الملف: ${fileName}...`);

        // الحصول على رابط التحميل من تليجرام
        const fileLink = await bot.getFileLink(fileId);
        
        // مسار حفظ الملف المؤقت
        const downloadPath = path.join(__dirname, fileName);
        
        // تحميل الملف إلى مجلد المشروع
        const response = await axios({
            url: fileLink,
            method: 'GET',
            responseType: 'stream'
        });

        const writer = fs.createWriteStream(downloadPath);
        response.data.pipe(writer);

        await new Promise((resolve, reject) => {
            writer.on('finish', resolve);
            writer.on('error', reject);
        });

        await bot.sendMessage(chatId, `📦 جاري فك ضغط الملف ${fileName}...`);

        // فك الضغط في مجلد المشروع الحالي
        const zip = new AdmZip(downloadPath);
        zip.extractAllTo(__dirname, true); // true تعني استبدال الملفات الموجودة مسبقاً إذا لزم الأمر

        // حذف الملف المضغوط بعد الانتهاء من فك الضغط
        fs.unlinkSync(downloadPath);

        await bot.sendMessage(chatId, `✅ تم رفع الملف وفك ضغطه بنجاح داخل المشروع!`);

    } catch (error) {
        console.error(error);
        await bot.sendMessage(chatId, `❌ حدث خطأ أثناء تحميل أو فك ضغط الملف: ${error.message}`);
    }
});
