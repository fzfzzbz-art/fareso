// utils/protection.js — ★ v3.12: قلب الحماية الشاملة للمجموعات (مضاد تفجير/سبام/روابط)
// ─────────────────────────────────────────────────────────────────────────────
// يُستدعى من session.js لكل رسالة مجموعة قبل موزّع الأوامر:
//   • مضاد الفلود/التفجير: عدّاد نوافذ زمنية لكل عضو (10 ثوانٍ افتراضياً) →
//     تحذير أول، ثم حذف، ثم طرد حسب الإعداد — بلا أي مهلات اصطناعية.
//   • مضاد الروابط حسب وضع المجموعة (حذف/تحذير/طرد) مع قائمة بيضاء.
//   • قفل أنواع المحتوى (ملصق/صورة/فيديو/صوت/ملف/استبيان/مشاركة جهة).
//   • كتم الأعضاء المكتومين (حذف رسائلهم فوراً).
//   • عدّاد النشاط اليومي (للأوامر المسليّة: أكثر الأعضاء تفاعلاً).
// كل الإعدادات لكل مجموعة تُقرأ/تُحفظ عبر utils/groupStore.js.
// ─────────────────────────────────────────────────────────────────────────────
import logger from './logger.js';
import { gset, gpatch, addWarn, getWarns, isMuted, bumpCount } from './groupStore.js';

const digitsOf = (v) => String(v || '').split('@')[0].split(':')[0].replace(/\D/g, '');

// عدّادات الفلود: chatId -> Map(jid -> { count, windowStart })
const floodWindows = new Map();

function isGroupJid(j) { return String(j || '').endsWith('@g.us'); }

/** فك أغلفة الرسالة (viewOnce/ephemeral/edited) */
function unwrap(c) {
  let m = c?.message || c || {};
  for (let i = 0; i < 8; i += 1) {
    const n = m.ephemeralMessage?.message || m.viewOnceMessage?.message ||
      m.viewOnceMessageV2?.message || m.viewOnceMessageV2Extension?.message ||
      m.documentWithCaptionMessage?.message || m.editedMessage?.message;
    if (!n || n === m) break;
    m = n;
  }
  return m;
}

/** أنواع المحتوى المقفلة */
function lockedTypeOf(content) {
  const map = {
    stickerMessage: 'sticker',
    imageMessage: 'image',
    videoMessage: 'video',
    audioMessage: 'audio',
    documentMessage: 'document',
    pollCreationMessage: 'poll',
    pollCreationMessageV3: 'poll',
    contactMessage: 'contact',
    contactsArrayMessage: 'contact'
  };
  for (const [k, v] of Object.entries(map)) if (content?.[k]) return v;
  return null;
}

function contentText(content) {
  return String(
    content?.conversation ??
    content?.extendedTextMessage?.text ??
    content?.imageMessage?.caption ??
    content?.videoMessage?.caption ??
    content?.documentMessage?.caption ?? ''
  );
}

const LINK_RE = /(https?:\/\/|www\.)[^\s]+|chat\.whatsapp\.com\/[^\s]+|(?:[a-z0-9-]+\.)+(?:com|net|org|info|io|me|co|ly|link|site|online|app|xyz)(?:\/[^\s]*)?/i;

/**
 * المعالج الرئيسي — يُرجع true إذا تُكُفّت الرسالة (حُذفت/عولجت).
 * لا يحجب أحداً بقرارات الحماية إلا في المجموعات وليس للرسائل من الحساب نفسه.
 */
export async function processGroupProtection(session, msg, type) {
  try {
    if (!msg?.key || !session?.sock || type !== 'notify') return false;
    const chat = String(msg.key.remoteJid || '');
    if (!isGroupJid(chat)) return false;

    const content = unwrap(msg);
    const senderJid = msg.key.participant || msg.key.remoteJid || '';
    const senderD = digitsOf(senderJid);
    const ownD = digitsOf(session.phone);
    if (!senderD || senderD === ownD || msg.key.fromMe) return false;

    const g = gset(chat);
    const meta = await safeMeta(session, chat);

    const senderIsAdmin = isAdminOf(meta, senderD);
    const botIsAdmin = isBotAdmin(session, meta);
    // المشرفون وقائمة البياض فوق القانون
    if (senderIsAdmin || (g.whitelist || []).includes(senderD)) {
      bumpCount(chat, senderJid);
      return false;
    }

    // ── 1) الكتم ──
    if (isMuted(chat, senderJid)) {
      await del(session, chat, msg, `🔇 @${senderD} أنت مكتوم في هذه المجموعة.`, [`${senderD}@s.whatsapp.net`]);
      return true;
    }

    // ── 2) قفل أنواع المحتوى ──
    const locked = lockedTypeOf(content);
    if (locked && g.locks?.[locked]) {
      const labels = { sticker: 'الملصقات', image: 'الصور', video: 'الفيديو', audio: 'الرسائل الصوتية', document: 'الملفات', poll: 'الاستبيانات', contact: 'جهات الاتصال' };
      await del(session, chat, msg, `🚫 ${labels[locked]} غير مسموح بها في هذه المجموعة.\n◈ العضو: @${senderD}`, [`${senderD}@s.whatsapp.net`]);
      return true;
    }

    // ── 3) مضاد الروابط ──
    const text = contentText(content);
    if (g.antilink && g.antilink !== 'off' && LINK_RE.test(text)) {
      const wl = (g.linkWhitelist || []);
      const hit = wl.find((w) => w && text.toLowerCase().includes(w.toLowerCase()));
      if (!hit) {
        if (g.antilink === 'delete') {
          await del(session, chat, msg, `🚫 *مضاد الروابط*\nالروابط ممنوعة هنا.\n◈ العضو: @${senderD}`, [`${senderD}@s.whatsapp.net`]);
          return true;
        }
        if (g.antilink === 'warn') {
          await warnFlow(session, chat, msg, senderD, botIsAdmin, 'إرسال رابط');
          return true;
        }
        if (g.antilink === 'kick' && botIsAdmin) {
          await del(session, chat, msg, null, []);
          await kick(session, chat, senderD, '🚪 طُرد لأنه أرسل رابطاً والمجموعة محمية من الروابط.');
          return true;
        }
      }
    }

    // ── 4) مضاد الفلود/التفجير ──
    if (g.antiflood?.on) {
      if (checkFlood(chat, senderD, g.antiflood)) {
        const action = g.antiflood.action || 'delete';
        if (action === 'delete') {
          await del(session, chat, msg, `🌊 *مضاد التفجير*\nتهدأ يا @${senderD} — الرسائل المتراصة محذوفة تلقائياً.`, [`${senderD}@s.whatsapp.net`]);
          return true;
        }
        if (action === 'warn') {
          await warnFlow(session, chat, msg, senderD, botIsAdmin, 'تفجير/سبام');
          return true;
        }
        if (action === 'kick' && botIsAdmin) {
          await kick(session, chat, senderD, '🚪 طُرد لسبام المجموعة.');
          return true;
        }
      }
    }

    // ── 5) عدّاد النشاط ──
    bumpCount(chat, senderJid);
    return false;
  } catch (err) {
    logger.debug({ err: err?.message || err }, 'processGroupProtection خطأ متجاهل');
    return false;
  }
}

// ─────────── عناصر مساعدة ───────────
function checkFlood(chatId, senderD, cfg) {
  const max = Math.max(3, Number(cfg.max) || 6);
  const win = Math.max(3, Number(cfg.windowSec) || 10) * 1000;
  if (!floodWindows.has(chatId)) floodWindows.set(chatId, new Map());
  const members = floodWindows.get(chatId);
  const now = Date.now();
  const rec = members.get(senderD) || { count: 0, windowStart: now };
  if (now - rec.windowStart > win) { rec.count = 0; rec.windowStart = now; }
  rec.count += 1;
  members.set(senderD, rec);
  // نظافة دورية
  if (members.size > 500) {
    for (const [k, v] of members) if (now - v.windowStart > 5 * 60_000) members.delete(k);
  }
  return rec.count > max;
}

async function warnFlow(session, chat, msg, senderD, botIsAdmin, reason) {
  const rec = addWarn(chat, senderD, reason);
  const g = gset(chat);
  const limit = Number(g.warnLimit) || 5;
  if (rec.count >= limit && botIsAdmin) {
    await kick(session, chat, senderD, `🚪 بلغت ${limit} تحذيرات — تم طردك. السبب الأخير: ${reason}.`);
    return;
  }
  await del(session, chat, msg,
    `⚠️ *تحذير ${rec.count}/${limit}*\n◈ العضو: @${senderD}\n◈ السبب: ${reason}`,
    [`${senderD}@s.whatsapp.net`]);
}

async function kick(session, chat, senderD, note) {
  try {
    await session.sock.groupParticipantsUpdate(chat, [`${senderD}@s.whatsapp.net`], 'remove');
    if (note) await session.sendText(chat, note).catch(() => {});
    // صفّر تحذيراته بعد الطرد
    const { resetWarns } = await import('./groupStore.js');
    resetWarns(chat, `${senderD}@s.whatsapp.net`);
    return true;
  } catch (err) {
    logger.debug({ err: err?.message || err }, 'فشل طرد عضو');
    return false;
  }
}

async function del(session, chat, msg, note, mentions) {
  try { await session.sock.sendMessage(chat, { delete: msg.key }); } catch { /* تجاهل */ }
  if (note) {
    try {
      await session.sock.sendMessage(chat, { text: note, mentions: mentions || [] });
    } catch { /* تجاهل */ }
  }
  return true;
}

function isAdminOf(meta, digits) {
  if (!meta) return false;
  return meta.participants.some((p) => (p.admin === 'admin' || p.admin === 'superadmin') && digitsOf(p.id) === digits);
}

function isBotAdmin(session, meta) {
  return isAdminOf(meta, digitsOf(session.selfJid() || session.phone));
}

async function safeMeta(session, chat) {
  try { return await session.sock.groupMetadata(chat); } catch { return null; }
}

export default processGroupProtection;
