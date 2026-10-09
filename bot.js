const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs');
const path = require('path');
const axios = require('axios');
const AdmZip = require('adm-zip');

const TOKEN = '8738377353:AAEOzFJQM-ZD3fnIOPbcS46gmytkodfqPcQ'; // توكن بوت تليجرام
const ADMIN_ID = 7231690686; // آيدي حسابك الشخصي

// إعدادات جيت هاب
// إعدادات جيت هاب تقرأ من متغيرات البيئة في سيرفر Railway
const GITHUB_TOKEN = process.env.GITHUB_TOKEN; 
const GITHUB_OWNER = process.env.GITHUB_OWNER; 
const GITHUB_REPO = process.env.GITHUB_REPO;   
const GITHUB_BRANCH = 'main'; 

const bot = new TelegramBot(TOKEN, { polling: true });
console.log('Bot is running and connected to GitHub...');

bot.on('document', async (msg) => {
    const chatId = msg.chat.id;
    const userId = msg.from.id;

    if (userId !== ADMIN_ID) {
        return bot.sendMessage(chatId, 'عذراً، هذا البوت مخصص للمالك فقط.');
    }

    const document = msg.document;
    const fileName = document.file_name;
    const fileId = document.file_id;

    if (!fileName.endsWith('.zip')) {
        return bot.sendMessage(chatId, '❌ يرجى إرسال ملف مضغوط بصيغة .zip فقط.');
    }

    const tempZipPath = path.join(__dirname, fileName);
    const extractPath = path.join(__dirname, 'extracted_temp');

    try {
        await bot.sendMessage(chatId, `📥 جاري تحميل الملف وتحضيره للرفع إلى GitHub...`);

        // 1. تحميل الملف من تليجرام
        const fileLink = await bot.getFileLink(fileId);
        const response = await axios({ url: fileLink, method: 'GET', responseType: 'stream' });
        const writer = fs.createWriteStream(tempZipPath);
        response.data.pipe(writer);

        await new Promise((resolve, reject) => {
            writer.on('finish', resolve);
            writer.on('error', reject);
        });

        // 2. فك الضغط محلياً مؤقتاً
        if (!fs.existsSync(extractPath)) fs.mkdirSync(extractPath);
        const zip = new AdmZip(tempZipPath);
        zip.extractAllTo(extractPath, true);

        await bot.sendMessage(chatId, `🚀 جاري رفع الملفات مباشرة إلى مستودع GitHub الرئيسي...`);

        // 3. رفع الملفات المستخرجة إلى GitHub تتابعياً
        await uploadFolderToGitHub(extractPath, '');

        // 4. تنظيف الملفات المؤقتة
        fs.unlinkSync(tempZipPath);
        fs.rmSync(extractPath, { recursive: true, force: true });

        await bot.sendMessage(chatId, `✅ تم رفع جميع الملفات وفكها بنجاح إلى المستودع الرئيسي في GitHub!`);

    } catch (error) {
        console.error(error);
        if (fs.existsSync(tempZipPath)) fs.unlinkSync(tempZipPath);
        if (fs.existsSync(extractPath)) fs.rmSync(extractPath, { recursive: true, force: true });
        await bot.sendMessage(chatId, `❌ حدث خطأ: ${error.message}`);
    }
});

// دالة تكرارية لرفع الملفات والمجلدات إلى GitHub
async function uploadFolderToGitHub(localDir, repoDir) {
    const items = fs.readdirSync(localDir);

    for (const item of items) {
        const localPath = path.join(localDir, item);
        const repoPath = repoDir ? `${repoDir}/${item}` : item;
        const stat = fs.statSync(localPath);

        if (stat.isDirectory()) {
            // إذا كان مجلد، ادخل بداخله وارفع محتوياته بشكل متكرر
            await uploadFolderToGitHub(localPath, repoPath);
        } else {
            // إذا كان ملف، قم برفعه
            await uploadFileToGitHub(localPath, repoPath);
        }
    }
}

// دالة رفع ملف فردي باستخدام GitHub Contents API
async function uploadFileToGitHub(localPath, repoPath) {
    const fileContent = fs.readFileSync(localPath);
    const encodedContent = fileContent.toString('base64');
    const apiUrl = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${repoPath}`;

    let sha = undefined;

    // التحقق مما إذا كان الملف موجود مسبقاً لجلب الـ SHA الخاص به (مطلوب للتحديث)
    try {
        const existingFile = await axios.get(apiUrl, {
            headers: { Authorization: `token ${GITHUB_TOKEN}` }
        });
        sha = existingFile.data.sha;
    } catch (err) {
        // الملف غير موجود مسبقاً، لا بأس سيتم إنشاؤه جديداً
    }

    // رفع أو تحديث الملف في المستودع الرئيسي
    await axios.put(apiUrl, {
        message: `Upload ${repoPath} via Telegram Bot`,
        content: encodedContent,
        branch: GITHUB_BRANCH,
        sha: sha
    }, {
        headers: {
            Authorization: `token ${GITHUB_TOKEN}`,
            'Content-Type': 'application/json'
        }
    });
}
