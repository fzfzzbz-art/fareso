const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const AdmZip = require('adm-zip');

// توكن بوت التليجرام الخاص بك (ضع توكن بوتك هنا أو اجعله كمتغير بيئة)
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || 'YOUR_TELEGRAM_BOT_TOKEN';

// إعدادات جيت هاب تقرأ من متغيرات البيئة في Railway
const GITHUB_TOKEN = process.env.GITHUB_TOKEN; 
const GITHUB_OWNER = process.env.GITHUB_OWNER; 
const GITHUB_REPO = process.env.GITHUB_REPO;   
const GITHUB_BRANCH = 'main'; 

// استبدل هذا بـ معرف تيليجرام الخاص بك ليكون البوت مخصصاً لك وحدك
const ADMIN_ID = process.env.ADMIN_ID ? Number(process.env.ADMIN_ID) : null;

const bot = new TelegramBot(TELEGRAM_BOT_TOKEN, { polling: true });
console.log('Bot is running and connected to GitHub...');

bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const userId = msg.from.id;

    // التحقق من أن المستخدم هو المالك (اختياري للأمان)
    if (ADMIN_ID && userId !== ADMIN_ID) {
        return bot.sendMessage(chatId, 'عذراً، هذا البوت مخصص للمالك فقط.');
    }

    const document = msg.document;
    if (!document) return;

    const fileName = document.file_name;
    if (!fileName.endsWith('.zip')) {
        return bot.sendMessage(chatId, 'يرجى إرسال ملف بصيغة .zip فقط.');
    }

    try {
        bot.sendMessage(chatId, 'جاري تحميل وفك الملف، ثم رفع المحتويات إلى GitHub...');

        // 1. تحميل الملف من تيليجرام
        const fileLink = await bot.getFileLink(document.file_id);
        const responseFile = await axios.get(fileLink, { responseType: 'arraybuffer' });
        const zipPath = path.join(__dirname, fileName);
        fs.writeFileSync(zipPath, responseFile.data);

        // 2. فك الـ ZIP
        const zip = new AdmZip(zipPath);
        const extractDir = path.join(__dirname, 'extracted_files');
        zip.extractAllTo(extractDir, true);

        // دالة لرفع الملفات بشكل تداخلي (Recursive)
        async function uploadDirectory(dirPath, repoPath = '') {
            const files = fs.readdirSync(dirPath);

            for (const file of files) {
                const fullPath = path.join(dirPath, file);
                const currentRepoPath = repoPath ? `${repoPath}/${file}` : file;

                if (fs.statSync(fullPath).isDirectory()) {
                    await uploadDirectory(fullPath, currentRepoPath);
                } else {
                    const fileContent = fs.readFileSync(fullPath);
                    const base64Content = fileContent.toString('base64');

                    let sha = undefined;
                    try {
                        const existingFile = await axios.get(
                            `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${currentRepoPath}`,
                            {
                                headers: {
                                    'Authorization': `token ${GITHUB_TOKEN}`,
                                    'Accept': 'application/vnd.github.v3+json'
                                }
                            }
                        );
                        sha = existingFile.data.sha;
                    } catch (e) {
                        // الملف غير موجود مسبقاً، لا بأس سيتم إنشاؤه جديداً
                    }

                    // رفع الملف إلى GitHub
                    await axios.put(
                        `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${currentRepoPath}`,
                        {
                            message: `Auto-upload: ${currentRepoPath} via Telegram Bot`,
                            content: base64Content,
                            branch: GITHUB_BRANCH,
                            ...(sha && { sha })
                        },
                        {
                            headers: {
                                'Authorization': `token ${GITHUB_TOKEN}`,
                                'Accept': 'application/vnd.github.v3+json',
                                'User-Agent': 'Telegram-Bot'
                            }
                        }
                    );
                }
            }
        }

        await uploadDirectory(extractDir);

        // تنظيف الملفات المؤقتة
        fs.rmSync(zipPath, { force: true });
        fs.rmSync(extractDir, { recursive: true, force: true });

        bot.sendMessage(chatId, 'تم فك الرفع وجميع الملفات بنجاح إلى مستودع GitHub!');

    } catch (error) {
        console.error(error.response?.data || error.message);
        bot.sendMessage(chatId, `حدث خطأ أثناء الرفع: ${error.response?.data?.message || error.message}`);
    }
});
