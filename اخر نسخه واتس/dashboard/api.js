// dashboard/api.js — نقاط لوحة التحكم (واجهة الويب) + الحماية بكلمة مرور
// ─────────────────────────────────────────────────────────────────────────────
// تعمل على السيرفر الرئيسي (تشرف على كل السيرفرات عبر نداءات موقّعة) وعلى العامل
// (تُدير جلساته المحلية). الحماية: تسجيل دخول بكلمة مرور → توكن في الذاكرة بمهلة.
// ─────────────────────────────────────────────────────────────────────────────
import express from 'express';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import config from '../config.js';
import logger, { recentLogs, clearLogs } from '../utils/logger.js';
import {
  listAllSessions, getSession, listServers, systemStats, totalSessionsCapacity,
  localSessionCount, openSessionCount, broadcastWhatsAppAll, applySessionPrefs,
  reconnectSession, reconnectAll, stopSession, unlinkNumber, statusAggregate,
  resetAllStatusStats, clearAllStatusCache, upsertServer, removeServer, ensureLocalServer,
  dashboardUrlOf, dashboardBaseOf
} from '../whatsapp/manager.js';
import {
  settingsStore, usersStore, commandsEnabled, setCommandsEnabled, getStartText, setStartText
} from '../utils/store.js';
import { allPrefs } from '../utils/sessionPrefs.js';
import { commands, categories } from '../whatsapp/commands/index.js';
import {
  probeYtdlp, probeUrl, autoUpdateYtdlp, saveDlSettings,
  dlSettings, sweepTmp, supportedPlatforms, queueInfo, reinstallTools
} from '../whatsapp/downloader.js';
import { workerStatus, workerPrefs, workerReconnect, workerStop, workerUnlink, workerBroadcast, workerCall } from '../whatsapp/relay.js';
import { statusSettings } from '../whatsapp/status.js';
// ★ v3.9: كلمات مرور الأرقام + الإعدادات الشاملة + المزامنة الثنائية الفورية
import {
  findPhoneByPassword, ensurePhonePassword, regeneratePhonePassword,
  verifyPhonePassword, listPhonePasswords, dropPhonePassword, passwordsStore
} from '../utils/passwords.js';
import {
  getPhoneFeatures, setPhoneFeature, patchPhoneFeatures, dropPhoneFeatures,
  featureGroups, totalFeaturesCount, featuresSummary
} from '../utils/features.js';
import { addSseClient, removeSseClient, broadcastToDashboards } from '../utils/sync.js';
import { maskPhone } from '../utils/helpers.js';
// ★ v3.10: تطبيع قائمة الإيموجي (حفظ أكثر من إيموجي للرقم)
import { parseEmojiList } from '../utils/emojis.js';
// ★ v3.14: محرّك الذكاء الاصطناعي (مفتاح لكل رقم + فحص المفتاح + اختبار حقيقي)
import { aiStatus, setPhoneAiKey, clearPhoneAiKey, validateAiKey, safeGeneratePrivateReply } from '../utils/ai.js';
// ★ v3.8: الأوامر المخصّصة + ملفات أوامر الرقم المربوط
import { listCustomCommands, upsertCustomCommand, removeCustomCommand } from '../utils/customCommands.js';
import { listCommandFilesForSession } from '../whatsapp/commandFiles.js';
import { listAutoReplies, replaceAutoReplies } from '../utils/autoReplies.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ─────────── التوكنات النشطة ───────────
// ★ v3.9: token -> { expiresAt, scopePhone } — scopePhone يعني توكن رقم مربوط
//   (دخل بكلمة مرور رقمه) فلا يرى في اللوحة إلا لوحة تحكم رقمه هو فقط.
const tokens = new Map();

function issueToken(scopePhone = null) {
  const t = crypto.randomBytes(24).toString('hex');
  // جلسة لوحة التحكم لا تنتهي بعد ثوانٍ أو أثناء بقاء الصفحة مفتوحة؛
  // ينتهي التوكن فقط عند تسجيل الخروج/إعادة تشغيل العملية.
  tokens.set(t, { expiresAt: 0, scopePhone: scopePhone || null });
  for (const [k, v] of tokens) if (v.expiresAt > 0 && v.expiresAt < Date.now()) tokens.delete(k);
  return t;
}

function validToken(t) {
  const rec = tokens.get(String(t || ''));
  if (!rec) return false;
  if (rec.expiresAt > 0 && rec.expiresAt < Date.now()) { tokens.delete(String(t)); return false; }
  return true;
}

function tokenRecord(t) {
  const rec = tokens.get(String(t || ''));
  if (!rec || (rec.expiresAt > 0 && rec.expiresAt < Date.now())) return null;
  return rec;
}

function auth(req, res, next) {
  const token = req.header('x-dash-token') || req.query.token;
  if (!validToken(token)) return res.status(401).json({ ok: false, error: 'انتهت الجلسة — سجّل الدخول من جديد.' });
  const rec = tokenRecord(token);
  req.dashScopePhone = rec?.scopePhone || null; // نطاق الرقم (إن وُجد)
  req.dashToken = String(token);
  next();
}

// ★ v3.10: حصر الأدوات الخاصة بالمطور — الإذاعة والسيرفرات والنظام والنسخ
//   متاحة فقط لتوكن المدير (غير المرتبط برقم). توكن صاحب رقم لا يُنفّذها.
function adminOnly(req, res, next) {
  if (req.dashScopePhone) {
    return res.status(403).json({ ok: false, error: 'هذه الأداة خاصة بالمطور فقط.' });
  }
  next();
}

const ok = (res, data = {}) => res.json({ ok: true, ...data });
const bad = (res, error, code = 400) => res.status(code).json({ ok: false, error });

/** نداء موثوق: يُنفَّذ محلياً إن كانت الجلسة هنا، وإلا يُمرَّر لسيرفرها */
async function onSession(userId, phone, localFn, remotePath, body = {}) {
  const local = getSession(userId, phone);
  if (local) return { ok: true, local: true, result: await localFn(local) };
  const srv = listServers().find((s) => !s.isLocal && s.alive && s.manual !== false && s.url);
  if (!srv) return { ok: false, error: 'الجلسة ليست على هذا السيرفر.' };
  const r = await workerCall(srv, remotePath, { userId, phone, ...body });
  return { ok: r.ok, local: false, server: srv.name, result: r.data };
}

/** توجيه الأمر للسيرفر المالك للجلسة: نجرّب المحلي أولاً ثم كل السيرفرات الحيّة */
async function routeToOwner(userId, phone, remotePath, body = {}) {
  if (getSession(userId, phone)) return { ok: true, handledLocally: true };
  for (const srv of listServers().filter((s) => !s.isLocal && s.alive)) {
    const r = await workerCall(srv, remotePath, { userId, phone, ...body }, 30000);
    if (r.ok && r.data?.ok !== false) return { ok: true, handledLocally: false, server: srv.name, data: r.data };
  }
  return { ok: false, error: 'لم يُعثر على الجلسة على أي سيرفر متصل.' };
}

// ★ v3.9: تحويل خيار شامل إلى patch يفهمه applyPrefs داخل الجلسة الحيّة
function featurePatchForKey(key, value) {
  const map = {
    status_auto_view: { autoView: !!value },
    status_auto_react: { reactEnabled: !!value },
    status_auto_like: { autoLike: !!value },
    status_auto_archive: { statusArchive: !!value },
    status_read_receipts: { statusReadReceipts: !!value }
    // باقي الخيارات تُقرأ من الأوامر الداخلية عبر isEnabled(phone, key) مباشرة
  };
  return map[key] || {};
}

/**
 * ★ v3.11: إيجاد المستخدم المالك للرقم.
 * كان الكود يُمرّر '' كمعرّف مستخدم إلى pushPrefsToSession فلا تُوجَد الجلسة
 * ولا يُطبَّق التغيير على الرقم الحيّ إطلاقاً — وهذا سبب «الميزة مفعّلة في
 * الموقع ولا تعمل على الرقم».
 */
function ownerUserIdOfPhone(phone) {
  const ph = String(phone || '').replace(/\D/g, '');
  if (!ph) return '';
  const live = listAllSessions().find((s) => String(s.phone) === ph);
  if (live) return String(live.userId);
  for (const u of Object.values(usersStore.all() || {})) {
    if (!u || !u.id) continue;
    if ((u.numbers || []).some((n) => String(n.phone) === ph)) return String(u.id);
  }
  return '';
}

/** ★ v3.11: تطبيق كل خيارات الرقم فوراً على الجلسة الحيّة على هذا السيرفر */
async function applyRuntimeForPhone(phone) {
  try {
    const { getSession } = await import('../whatsapp/manager.js');
    const { applyFeatureRuntime } = await import('../whatsapp/commands/settings.js');
    const uid = ownerUserIdOfPhone(phone);
    const s = (uid && getSession(uid, phone)) || listAllSessions().find((x) => String(x.phone) === String(phone).replace(/\D/g, ''));
    if (!s) return false;
    applyFeatureRuntime(s);
    return true;
  } catch { return false; }
}
function featurePatchObject(patch) {
  const out = {};
  for (const [k, v] of Object.entries(patch || {})) {
    Object.assign(out, featurePatchForKey(k, v));
  }
  return out;
}

/** ★ v3.9: دفع تغيير إعدادات شاملة لكل السيرفرات العاملة الحيّة */
async function pushFeatureToWorkers(phone, patch) {
  let ok = 0;
  for (const srv of listServers().filter((s) => !s.isLocal && s.alive)) {
    const r = await workerCall(srv, '/api/features-sync', { phone, patch }, 15000).catch(() => ({ ok: false }));
    if (r?.ok) ok += 1;
  }
  return ok;
}

export function createDashboardRouter({ broadcastTelegram = null } = {}) {
  const r = express.Router();
  const api = express.Router();

  // ─────────── صفحة الواجهة ───────────
  r.get('/', (_req, res) => {
    try {
      const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
      res.setHeader('content-type', 'text/html; charset=utf-8');
      res.setHeader('cache-control', 'no-store');
      res.send(html);
    } catch (err) {
      res.status(500).send(`تعذّر تحميل الواجهة: ${err.message}`);
    }
  });

  // ─────────── ★ v3.8: صفحة دليل السيرفرات (تُخدَم كصفحة مستقلة) ───────────
  r.get('/servers', (_req, res) => {
    try {
      const html = fs.readFileSync(path.join(__dirname, 'servers.html'), 'utf8');
      res.setHeader('content-type', 'text/html; charset=utf-8');
      res.setHeader('cache-control', 'no-store');
      res.send(html);
    } catch (err) {
      res.status(500).send(`تعذّر تحميل صفحة السيرفرات: ${err.message}`);
    }
  });

  // ─────────── الدخول ───────────
  api.post('/login', (req, res) => {
    const pass = String(req.body?.password || '');
    if (!pass) return bad(res, 'أدخل كلمة المرور.');
    const activePass = String(settingsStore.get('dashboardPassword') || config.dashboard.password);

    // 1) دخول المدير (كلمة المرور العامة)
    if (pass === activePass) {
      const token = issueToken(null);
      return ok(res, { token, ttlMs: 0, role: config.role, scope: { scoped: false } });
    }

    // 2) ★ v3.9: دخول صاحب رقم مربوط بكلمة مروره الخاصة → لوحة رقمه فقط
    const phone = findPhoneByPassword(pass);
    if (phone) {
      const token = issueToken(phone);
      logger.info({ ip: req.ip, phone }, 'دخول صاحب رقم بكلمة مروره الخاصة (نطاق الرقم فقط)');
      return ok(res, { token, ttlMs: 0, role: config.role, scope: { scoped: true, phone } });
    }

    logger.warn({ ip: req.ip }, 'محاولة دخول فاشلة للوحة التحكم');
    return bad(res, 'كلمة المرور غير صحيحة.', 401);
  });

  api.post('/logout', (req, res) => {
    const t = req.header('x-dash-token');
    if (t) tokens.delete(t);
    return ok(res);
  });

  // ─────────── ★ v3.14: الذكاء الاصطناعي — مفتاح لكل رقم مربوط ───────────
  api.get('/ai/status', auth, (req, res) => {
    const phone = String(req.dashScopePhone || req.query?.phone || '').replace(/\D/g, '');
    return ok(res, { phone: phone || null, status: aiStatus(phone) });
  });

  api.post('/ai/key', auth, (req, res) => {
    const phone = String(req.dashScopePhone || req.body?.phone || '').replace(/\D/g, '');
    if (!phone) return bad(res, 'حدّد الرقم المربوط أولاً.');
    const r = setPhoneAiKey(phone, req.body?.key, {
      provider: String(req.body?.provider || 'auto').toLowerCase(),
      model: String(req.body?.model || '').trim() || undefined,
      baseUrl: String(req.body?.baseUrl || '').trim() || undefined
    });
    if (!r.ok) return bad(res, r.error);
    logger.info({ phone, key: r.masked }, 'لوحة التحكم: تم تعيين مفتاح ذكاء اصطناعي');
    return ok(res, { saved: true, masked: r.masked, status: aiStatus(phone) });
  });

  api.post('/ai/key/clear', auth, (req, res) => {
    const phone = String(req.dashScopePhone || req.body?.phone || '').replace(/\D/g, '');
    if (!phone) return bad(res, 'حدّد الرقم المربوط أولاً.');
    const r = clearPhoneAiKey(phone);
    return ok(res, { cleared: r.had, status: aiStatus(phone) });
  });

  api.post('/ai/test', auth, async (req, res) => {
    const phone = String(req.dashScopePhone || req.body?.phone || '').replace(/\D/g, '');
    const chk = validateAiKey(phone);
    if (!chk.ok) return bad(res, chk.error);
    const r = await safeGeneratePrivateReply('اكتب: اختبار ناجح', { phone, useMemory: false });
    return ok(res, r.ok ? { ok: true, reply: r.text } : { ok: false, error: r.error });
  });

  // ─────────── نظرة شاملة (تُستخدم لتحديث الواجهة كل ثانية) ───────────
  api.get('/overview', auth, async (req, res) => {
    try {
      const scopePhone = req.dashScopePhone || null;
      let local = listAllSessions().map((s) => s.toJSON());
      if (scopePhone) local = local.filter((s) => String(s.phone) === String(scopePhone));
      const remote = [];
      if (config.isMain) {
        for (const srv of listServers().filter((s) => !s.isLocal && s.alive)) {
          const r2 = await workerStatus(srv);
          if (r2.ok && Array.isArray(r2.data?.sessions)) {
            for (const s of r2.data.sessions) {
              if (scopePhone && String(s.phone) !== String(scopePhone)) continue;
              remote.push({ ...s, server: srv.name, remote: true });
            }
          }
        }
      }
      // ★ v3.9: صاحب الرقم لا يرى سيرفرات النظام ولا بيانات الآخرين إطلاقاً
      const scopeServers = scopePhone
        ? listServers().filter((s) => s.isLocal).map((s) => ({ ...s, sessionCount: local.length }))
        : listServers();
      const cfg = statusSettings();
      const dls = dlSettings();
      return ok(res, {
        role: config.role,
        serverName: config.localServer.name,
        version: config.version,
        dev: config.dev,
        system: systemStats(),
        capacity: totalSessionsCapacity(),
        localSessions: local,
        remoteSessions: remote,
        openCount: openSessionCount(),
        localCount: localSessionCount(),
        scope: scopePhone ? { scoped: true, phone: scopePhone } : { scoped: false },
        servers: scopeServers,
        // ★ v3.9: الإعدادات الشاملة — للرقم المحدّد (أو رقم النطاق تلقائياً)
        featureInfo: featuresSummary(),
        featureGroups: featureGroups(),
        status: { settings: cfg, aggregate: statusAggregate() },
        downloader: {
          settings: dls,
          cookies: !!(dls.cookiesFile || dls.cookiesFromBrowser),
          cookiesPath: null,
          queue: queueInfo(),
          supported: supportedPlatforms()
        },
        flags: {
          commandsEnabled: commandsEnabled(),
          startText: getStartText(),
          autoFollowChannel: config.autoFollowChannel
        },
        counts: {
          commands: commands.length,
          categories: categories.size,
          users: Object.keys(usersStore.all() || {}).length,
          savedPrefs: Object.keys(allPrefs()).length
        },
        lastEvents: recentLogs(30)
      });
    } catch (err) {
      logger.error({ err }, 'overview failed');
      return bad(res, err?.message || 'خطأ في جمع البيانات.', 500);
    }
  });

  api.get('/healthcheck', auth, async (_req, res) => ok(res, { ytdlp: await probeYtdlp() }));

  api.get('/logs', auth, (req, res) => ok(res, { lines: recentLogs(Number(req.query.limit) || 200) }));
  api.post('/logs/clear', auth, (_req, res) => { clearLogs(); return ok(res); });

  // ─────────── إعدادات محرّك الحالات (عامة) ───────────
  api.post('/status-settings', auth, (req, res) => {
    const b = req.body || {};
    const patch = {};
    if (b.concurrency !== undefined) patch.statusConcurrency = Math.max(1, Math.min(64, Number(b.concurrency) || 8));
    if (b.fastMode !== undefined) patch.statusFastMode = !!b.fastMode;
    if (b.markRead !== undefined) patch.statusMarkRead = !!b.markRead;
    // ★ v3.10: لا نقصّ الإيموجي — ندعم عدة إيموجي معاً
    if (b.likeEmoji !== undefined) patch.statusLikeEmoji = parseEmojiList(b.likeEmoji, ['❤️']).join(' ') || '❤️';
    if (b.likeEmojis !== undefined) patch.statusLikeEmoji = parseEmojiList(b.likeEmojis, ['❤️']).join(' ') || '❤️';
    if (b.reactDelayMs !== undefined) patch.statusReactDelayMs = Math.max(0, Number(b.reactDelayMs) || 0);
    if (b.maxDelayMs !== undefined) patch.statusMaxDelayMs = Math.max(0, Number(b.maxDelayMs) || 0);
    settingsStore.set('statusSettings', { ...(settingsStore.get('statusSettings') || {}), ...patch });
    for (const k of Object.keys(patch)) settingsStore.set(k, patch[k]);
    logger.info({ patch }, 'تحديث إعدادات محرّك الحالات من لوحة التحكم');
    return ok(res, { settings: statusSettings() });
  });

  // ─────────── إعدادات رقم واحد ───────────
  api.post('/session/prefs', auth, async (req, res) => {
    const body = req.body || {};
    let userId = String(body.userId || '').trim();
    const phone = String(body.phone || '').replace(/\D/g, '');
    let patch = { ...(body.patch || {}) };
    if (!phone) return bad(res, 'phone مطلوب.');
    // ★ v3.9: نطاق الرقم — صاحب كلمة مرور رقم لا يُعدَّل إلا إعدادات رقمه
    if (req.dashScopePhone && String(req.dashScopePhone) !== phone) {
      return bad(res, 'هذه اللوحة خاصة برقمك المربوط فقط.', 403);
    }
    // ★ v3.10: إن لم يُرسل userId صحيح (أو كان '0' من الواجهة) نستنتجه من الرقم
    //   حتى تُطبَّق الإعدادات على الجلسة الحيّة الصحيحة لا على مفتاح وهمي.
    if (!userId || userId === '0' || !getSession(userId, phone)) {
      const hit = listAllSessions().find((s) => String(s.phone) === phone);
      if (hit) userId = String(hit.userId);
    }
    // ★ v3.10: تطبيع الإيموجي — نحفظ القائمة كاملة (إيموجي واحد أو أكثر) بلا قصّ
    if (patch.emojis || patch.emoji) {
      const list = parseEmojiList(patch.emojis || patch.emoji, [config.defaultStatusEmoji]);
      patch = { ...patch, emojis: list, emoji: list[0] };
    }
    const saved = applySessionPrefs(userId || '0', phone, patch);
    // تطبيق فوري على الجلسة الحيّة محلياً (المشاهدة/التفاعل/الإيموجي)
    const { pushPrefsToSession: pushOnce } = await import('../utils/sync.js');
    await pushOnce(getSession, userId, phone, patch);
    // وإن كانت الجلسة على سيرفر عامل نُمرّر الإعداد إليه فوراً
    const routed = await routeToOwner(userId, phone, '/api/prefs', { patch });
    broadcastToDashboards('prefs-applied', { userId, phone, patch, source: 'dashboard' });
    return ok(res, { saved, routed, userId, emojis: patch.emojis || null });
  });

  // ─────────── إجراء على رقم واحد ───────────
  api.post('/session/action', auth, async (req, res) => {
    const { userId, phone, action } = req.body || {};
    if (!userId || !phone || !action) return bad(res, 'userId و phone و action مطلوبة.');
    const s = getSession(userId, phone);

    switch (action) {
      case 'reconnect':
        if (s) return ok(res, { result: await reconnectSession(userId, phone) });
        return ok(res, { result: await routeToOwner(userId, phone, '/api/reconnect') });
      case 'stop':
        if (s) return ok(res, { result: await stopSession(userId, phone) });
        return ok(res, { result: await routeToOwner(userId, phone, '/api/stop') });
      case 'logout':
      case 'unlink':
        if (s) return ok(res, { result: await unlinkNumber(userId, phone) });
        return ok(res, { result: await routeToOwner(userId, phone, '/api/unlink') });
      case 'clearCache':
        if (s) { s.statusEngine.clearCache(); return ok(res); }
        return ok(res, { result: await routeToOwner(userId, phone, '/api/status-stats', { action: 'clearCache' }) });
      case 'resetStats':
        if (s) { s.statusEngine.resetStats(); return ok(res); }
        return ok(res, { result: await routeToOwner(userId, phone, '/api/status-stats', { action: 'resetStats' }) });
      case 'ping':
        return ok(res, { status: s ? s.status : 'unknown' });
      default:
        return bad(res, `إجراء غير معروف: ${action}`);
    }
  });

  // ─────────── إجراءات جماعية على كل الأرقام ───────────
  api.post('/bulk', auth, adminOnly, async (req, res) => {
    const { action, patch } = req.body || {};
    const localList = listAllSessions();
    const targets = localList.map((s) => ({ userId: s.userId, phone: s.phone }));

    // 1) حفظ الإعدادات لكل الأرقام المعروفة (محلياً + الممرَّرة)
    if (action === 'setPrefs') {
      let applied = 0;
      for (const s of localList) { applySessionPrefs(s.userId, s.phone, patch || {}); applied++; }
      for (const [k, v] of Object.entries(allPrefs())) {
        const [uid, ph] = k.split(':');
        if (!listAllSessions().some((s) => s.userId === uid && s.phone === ph)) {
          applySessionPrefs(uid, ph, patch || {});
          applied++;
        }
      }
      for (const srv of listServers().filter((s) => !s.isLocal && s.alive)) {
        await workerCall(srv, '/api/bulk-prefs', { patch: patch || {} }, 30000);
      }
      return ok(res, { applied, patch });
    }

    // 2) إعادة تشغيل كل الجلسات
    if (action === 'reconnectAll') {
      const localRes = await reconnectAll();
      for (const srv of listServers().filter((s) => !s.isLocal && s.alive)) {
        await workerCall(srv, '/api/reconnect-all', {}, 300000);
      }
      return ok(res, { local: localRes, total: targets.length });
    }

    // 3) تصفير الإحصاءات / الكاش
    if (action === 'resetStats') {
      resetAllStatusStats();
      for (const srv of listServers().filter((s) => !s.isLocal && s.alive)) {
        await workerCall(srv, '/api/status-stats', { action: 'resetStats' }, 20000);
      }
      return ok(res);
    }
    if (action === 'clearCache') {
      clearAllStatusCache();
      for (const srv of listServers().filter((s) => !s.isLocal && s.alive)) {
        await workerCall(srv, '/api/status-stats', { action: 'clearCache' }, 20000);
      }
      return ok(res);
    }

    // 4) إعادة ربط كل جلسة (تصفير الأكواد المعلّقة)
    if (action === 'resendCodes') {
      let n = 0;
      for (const s of localList) {
        if (s.hasPendingCode()) { s.emit({ event: 'pairing_code', code: s.pairingCode, reused: true }); n++; }
      }
      return ok(res, { resent: n });
    }

    return bad(res, `إجراء جماعي غير معروف: ${action}`);
  });

  // ─────────── الإذاعة ───────────
  api.post('/broadcast/whatsapp', auth, adminOnly, async (req, res) => {
    const { text, imageUrl, caption, targets, sourcePhone } = req.body || {};
    if (!text && !imageUrl) return bad(res, 'النص أو رابط الصورة مطلوب.');
    if (!String(sourcePhone || '').replace(/\D/g, '')) return bad(res, 'رقم الإرسال مطلوب حتى لا تُرسل من بقية الأرقام.');
    const local = await broadcastWhatsAppAll({ text, imageUrl, caption: caption || '', targets: Array.isArray(targets) ? targets : null, sourcePhone });
    return ok(res, { local, error: local?.error || null });
  });

  api.post('/broadcast/telegram', auth, adminOnly, async (req, res) => {
    const { text } = req.body || {};
    if (!text) return bad(res, 'أدخل نص الرسالة.');
    if (typeof broadcastTelegram !== 'function') return bad(res, 'إذاعة تيليجرام متاحة على السيرفر الرئيسي فقط.');
    const out = await broadcastTelegram(text);
    return ok(res, out);
  });

  // ─────────── محرّك التحميل ───────────
  api.get('/downloader', auth, async (_req, res) => ok(res, { probe: await probeYtdlp({ fresh: true }), settings: dlSettings(), queue: queueInfo() }));

  api.post('/downloader/settings', auth, (req, res) => {
    const b = req.body || {};
    const patch = {};
    if (b.enabled !== undefined) patch.enabled = !!b.enabled;
    if (b.bin !== undefined) patch.bin = String(b.bin || 'yt-dlp').slice(0, 200);
    if (b.maxFilesizeMb !== undefined) patch.maxFilesizeMb = Math.max(5, Math.min(1500, Number(b.maxFilesizeMb) || 60));
    if (b.timeoutMs !== undefined) patch.timeoutMs = Math.max(15000, Math.min(1800000, Number(b.timeoutMs) || 180000));
    if (b.concurrency !== undefined) patch.concurrency = Math.max(1, Math.min(8, Number(b.concurrency) || 2));
    if (b.autoCompress !== undefined) patch.autoCompress = !!b.autoCompress;
    if (b.proxy !== undefined) patch.proxy = String(b.proxy || '').slice(0, 300);
    // ★ v3.13: أُزيلت useCookies وبيانات الاعتماد (igUsername/igPassword/ytUsername/ytPassword)
    if (b.autoUpdate !== undefined) patch.autoUpdate = !!b.autoUpdate;
    const saved = saveDlSettings(patch);
    logger.info({ patch }, 'تحديث إعدادات التحميل من لوحة التحكم');
    return ok(res, { settings: saved });
  });

  // ★ v3.13: تحديث yt-dlp فوراً بضغطة واحدة من اللوحة (بلا كوكيز)
  api.post('/downloader/update', auth, async (_req, res) => {
    const out = await autoUpdateYtdlp({ force: true });
    logger.info({ out }, 'تحديث yt-dlp من لوحة التحكم');
    return ok(res, { update: out, probe: await probeYtdlp({ fresh: true }) });
  });

  // إعادة تثبيت/تحديث أدوات التحميل (yt-dlp + ffmpeg) بضغطة واحدة من اللوحة
  api.post('/downloader/reinstall', auth, async (_req, res) => {
    const out = await reinstallTools({ force: true });
    return ok(res, { tools: out, probe: await probeYtdlp({ fresh: true }) });
  });

  api.post('/downloader/sweep', auth, async (_req, res) => ok(res, { removed: await sweepTmp(0) }));

  api.post('/downloader/test', auth, async (req, res) => {
    const url = String(req.body?.url || '').trim();
    if (!/^https?:\/\//i.test(url)) return bad(res, 'أدخل رابطاً صحيحاً يبدأ بـ http.');
    const info = await probeUrl(url);
    return info.ok ? ok(res, { info }) : bad(res, info.error);
  });

  // تنزيل تجريبي (بلا إرسال لواتساب) للتأكد من عمل المنصة
  api.post('/downloader/fetch-test', auth, async (req, res) => {
    const url = String(req.body?.url || '').trim();
    if (!/^https?:\/\//i.test(url)) return bad(res, 'أدخل رابطاً صحيحاً.');
    const { downloadMedia, cleanupDownload } = await import('../whatsapp/downloader.js');
    const d = await downloadMedia(url, {});
    if (!d.ok) return bad(res, d.error);
    await cleanupDownload(d.dir);
    return ok(res, { result: { platform: d.platformLabel, sizeMb: d.sizeMb, elapsedMs: d.elapsedMs, mimetype: d.mimetype, title: d.title } });
  });

  // ─────────── السيرفرات ───────────
  api.get('/servers', auth, (_req, res) => ok(res, { servers: listServers(), capacity: totalSessionsCapacity() }));

  // ★ v3.8: كل سيرفر مع رابط لوحة التحكم الخاصة به — يُفتح مباشرة عند الضغط على رابط السيرفر
  api.get('/servers/dashboards', auth, (_req, res) => {
    const localDash = dashboardUrlOf({ url: config.localServer.url });
    return ok(res, {
      servers: listServers().map((s) => ({ ...s, dashboardUrl: dashboardUrlOf(s) })),
      capacity: totalSessionsCapacity(),
      guideUrl: config.dashboard.enabled ? `${localDash}/servers` : null,
      localBase: config.localServer.url,
      dashboardBase: dashboardBaseOf(config.localServer.url)
    });
  });

  api.post('/servers/add', auth, adminOnly, (req, res) => {
    const { name, url, maxSessions } = req.body || {};
    if (!/^https?:\/\//i.test(String(url || ''))) return bad(res, 'رابط السيرفر يجب أن يبدأ بـ http.');
    const out = upsertServer({ name, url, maxSessions });
    if (!out.ok) return bad(res, out.error);
    logger.info({ name, url }, 'إضافة/تحديث سيرفر من لوحة التحكم');
    return ok(res, { server: out.server, servers: listServers() });
  });

  api.post('/servers/remove', auth, adminOnly, (req, res) => {
    const out = removeServer(String(req.body?.name || ''));
    if (!out.ok) return bad(res, out.error);
    return ok(res, { servers: listServers() });
  });

  api.post('/servers/ping', auth, adminOnly, async (req, res) => {
    const name = String(req.body?.name || '');
    const srv = listServers().find((s) => s.name === name);
    if (!srv) return bad(res, 'السيرفر غير موجود.');
    if (srv.isLocal) return ok(res, { local: true, alive: true, sessions: localSessionCount() });
    const r2 = await workerStatus(srv);
    return ok(res, { alive: r2.ok, status: r2.data, error: r2.error || null });
  });

  // ─────────── إعدادات عامة ───────────
  api.post('/settings/commands', auth, adminOnly, (req, res) => {
    setCommandsEnabled(!!req.body?.on);
    return ok(res, { commandsEnabled: commandsEnabled() });
  });

  api.post('/settings/start-text', auth, adminOnly, (req, res) => {
    setStartText(String(req.body?.text || ''));
    return ok(res, { startText: getStartText() });
  });

  api.post('/settings/follow-channel', auth, adminOnly, (req, res) => {
    const on = !!req.body?.on;
    settingsStore.set('autoFollowChannel', on);
    return ok(res, { autoFollowChannel: on });
  });

  api.post('/settings/password', auth, adminOnly, (req, res) => {
    const next = String(req.body?.password || '');
    if (next.length < 6) return bad(res, 'كلمة المرور يجب أن تكون 6 أحرف على الأقل.');
    settingsStore.set('dashboardPassword', next);
    for (const k of tokens.keys()) tokens.delete(k);
    logger.warn('تم تغيير كلمة مرور لوحة التحكم — كل الجلسات أُنهيت');
    return ok(res, { changed: true });
  });

  // ─────────── الأوامر والأرشفة ───────────
  api.get('/commands', auth, (_req, res) =>
    ok(res, {
      total: commands.length,
      categories: [...categories.values()],
      commands: commands.map((c) => ({
        name: c.name, aliases: c.aliases, category: c.category, desc: c.desc,
        owner: c.owner, admin: c.admin
      }))
    })
  );

  api.get('/backup', auth, adminOnly, (_req, res) => {
    const payload = {
      exportedAt: new Date().toISOString(),
      role: config.role,
      server: config.localServer.name,
      settings: settingsStore.all(),
      users: usersStore.all(),
      prefs: allPrefs(),
      servers: listServers()
    };
    res.setHeader('content-type', 'application/json; charset=utf-8');
    res.setHeader('content-disposition', `attachment; filename="wa-tg-backup-${Date.now()}.json"`);
    res.send(JSON.stringify(payload, null, 2));
  });

  api.get('/export/prefs', auth, (_req, res) =>
    ok(res, {
      count: Object.keys(allPrefs()).length,
      prefs: allPrefs(),
      masked: Object.fromEntries(Object.entries(allPrefs()).map(([k, v]) => {
        const [uid, ph] = k.split(':');
        return `${uid}:${maskPhone(ph)}` === k ? [k, v] : [`${uid}:${maskPhone(ph)}`, v];
      }))
    })
  );

  // ─────────── ★ v3.8: الأوامر المخصّصة (النصية) ───────────
  api.get('/custom-commands', auth, async (_req, res) => ok(res, { commands: listCustomCommands() }));

  api.post('/custom-commands/add', auth, adminOnly, async (req, res) => {
    const { name, text } = req.body || {};
    const out = await upsertCustomCommand(name, text, { addedVia: 'dashboard' });
    if (!out.ok) return bad(res, out.error);
    let pushed = 0;
    for (const srv of listServers().filter((s) => !s.isLocal && s.alive)) {
      const r2 = await workerCall(srv, '/api/custom-commands/upsert', { name, text }, 20000).catch(() => ({ ok: false }));
      if (r2?.ok) pushed += 1;
    }
    logger.info({ name, pushed }, 'إضافة أمر مخصّص من لوحة التحكم');
    return ok(res, { command: out.command, replaced: out.replaced, pushed });
  });

  api.post('/custom-commands/remove', auth, adminOnly, async (req, res) => {
    const name = String(req.body?.name || '');
    const out = await removeCustomCommand(name);
    if (!out.ok) return bad(res, out.error);
    let pushed = 0;
    for (const srv of listServers().filter((s) => !s.isLocal && s.alive)) {
      const r2 = await workerCall(srv, '/api/custom-commands/remove', { name }, 20000).catch(() => ({ ok: false }));
      if (r2?.ok) pushed += 1;
    }
    return ok(res, { removed: out.command, pushed });
  });

  // ─────────── ★ v3.8: ملفات أوامر الرقم المربوط ───────────
  api.get('/command-files', auth, (req, res) => {
    const { userId, phone } = req.query || {};
    if (!userId || !phone) return bad(res, 'userId و phone مطلوبان.');
    return ok(res, { files: listCommandFilesForSession(userId, phone) });
  });

  // ═══════════ ★ v3.9: الإعدادات الشاملة (100+ خيار لكل رقم) ═══════════
  // قراءة إعدادات رقم — لصاحب النطاق تُجبر على رقمه هو
  api.get('/features', auth, (req, res) => {
    const phone = req.dashScopePhone || String(req.query?.phone || '').replace(/\D/g, '');
    if (!phone) return bad(res, 'phone مطلوب.');
    return ok(res, { phone, features: getPhoneFeatures(phone), total: totalFeaturesCount(), groups: featureGroups() });
  });

  // ─────────── الردود التلقائية النصية (الخاص فقط) ───────────
  api.get('/auto-replies', auth, async (req, res) => {
    const phone = req.dashScopePhone || String(req.query?.phone || '').replace(/\D/g, '');
    if (!phone) return bad(res, 'phone مطلوب.');
    const local = getSession(ownerUserIdOfPhone(phone), phone);
    if (!local) {
      const rec = Object.values(usersStore.all() || {}).flatMap((u) => u?.numbers || [])
        .find((n) => String(n.phone).replace(/\D/g, '') === phone);
      const srv = listServers().find((s) => !s.isLocal && s.alive && s.name === rec?.server);
      if (srv) {
        const remote = await workerCall(srv, '/api/auto-replies', { phone }, 15000);
        if (remote.ok && remote.data?.ok) return ok(res, { phone, replies: remote.data.replies || [] });
      }
    }
    return ok(res, { phone, replies: listAutoReplies(phone) });
  });

  api.post('/auto-replies', auth, async (req, res) => {
    const phone = req.dashScopePhone || String(req.body?.phone || '').replace(/\D/g, '');
    if (!phone) return bad(res, 'phone مطلوب.');
    const out = replaceAutoReplies(phone, req.body?.replies || []);
    if (!out.ok) return bad(res, out.error);
    setPhoneFeature(phone, 'msg_auto_reply', out.replies.length > 0);
    const live = await applyRuntimeForPhone(phone);
    const pushed = await pushFeatureToWorkers(phone, { msg_auto_reply: out.replies.length > 0 });
    const routed = await routeToOwner(ownerUserIdOfPhone(phone), phone, '/api/auto-replies', { replies: out.replies });
    broadcastToDashboards('auto-replies-changed', { phone, count: out.replies.length });
    return ok(res, { ...out, live, pushed, routed });
  });

  // تفعيل/تعطيل خيار واحد → حفظ فوري + تطبيق فوري على الجلسة + بث SSE للواجهات
  api.post('/features/set', auth, async (req, res) => {
    const phone = req.dashScopePhone || String(req.body?.phone || '').replace(/\D/g, '');
    const { key, value } = req.body || {};
    if (!phone) return bad(res, 'phone مطلوب.');
    const out = await setPhoneFeature(phone, String(key || ''), value);
    if (!out.ok) return bad(res, out.error);
    const { getSession } = await import('../whatsapp/manager.js');
    const { pushPrefsToSession } = await import('../utils/sync.js');
    // ★ v3.11: نُمرّر المستخدم المالك الحقيقي (كان '' فيضيع التطبيق الفوري)
    const uid = ownerUserIdOfPhone(phone);
    const live = await pushPrefsToSession(getSession, uid, phone, featurePatchForKey(key, value));
    // ★ v3.11: نُطبّق *كل* الخيارات (لا الحالات فقط) على الجلسة الحيّة فوراً
    const runtime = await applyRuntimeForPhone(phone);
    await pushFeatureToWorkers(phone, { [String(key)]: !!value });
    broadcastToDashboards('feature-changed', { phone, key, value: !!value });
    return ok(res, { ...out, live: live.live || runtime, runtime, userId: uid || null });
  });

  // حفظ مجموعة خيارات دفعة واحدة (يستخدمها حفظ النموذج الكامل في الموقع)
  api.post('/features/patch', auth, async (req, res) => {
    const phone = req.dashScopePhone || String(req.body?.phone || '').replace(/\D/g, '');
    const patch = req.body?.patch || {};
    if (!phone) return bad(res, 'phone مطلوب.');
    const out = patchPhoneFeatures(phone, patch);
    const { getSession } = await import('../whatsapp/manager.js');
    const { pushPrefsToSession } = await import('../utils/sync.js');
    // ★ v3.11: المستخدم المالك الحقيقي + تطبيق كامل للخيارات على الرقم الحيّ
    const uid = ownerUserIdOfPhone(phone);
    const live = await pushPrefsToSession(getSession, uid, phone, featurePatchObject(patch));
    const runtime = await applyRuntimeForPhone(phone);
    await pushFeatureToWorkers(phone, patch || {});
    broadcastToDashboards('features-patched', { phone, count: out.applied });
    return ok(res, { ...out, live: live.live || runtime, runtime, userId: uid || null });
  });

  // ★ v3.11: إعادة تطبيق كل خيارات الرقم فوراً على الجلسة الحيّة (زر «تطبيق الآن»)
  api.post('/features/apply', auth, async (req, res) => {
    const phone = req.dashScopePhone || String(req.body?.phone || '').replace(/\D/g, '');
    if (!phone) return bad(res, 'phone مطلوب.');
    const runtime = await applyRuntimeForPhone(phone);
    const pushed = await pushFeatureToWorkers(phone, getPhoneFeatures(phone));
    const uid = ownerUserIdOfPhone(phone);
    broadcastToDashboards('features-applied', { phone });
    return ok(res, { phone, userId: uid || null, live: runtime, pushed });
  });

  // ═══════════ ★ v3.9: كلمات مرور الأرقام (لوحة المدير فقط — بلا نطاق) ═══════════
  // جلب/توليد كلمة مرور رقم (تُستخدم من بوت تيليجرام أيضاً عبر manager hook)
  api.post('/features/phone-password', auth, (req, res) => {
    if (req.dashScopePhone) return bad(res, 'غير متاح لنطاق الرقم — للمدير فقط.', 403);
    const phone = String(req.body?.phone || '').replace(/\D/g, '');
    if (!phone) return bad(res, 'phone مطلوب.');
    const out = req.body?.regenerate ? regeneratePhonePassword(phone) : ensurePhonePassword(phone);
    if (!out.ok) return bad(res, out.error);
    return ok(res, { phone, password: out.password, created: !!out.created });
  });

  api.get('/features/passwords', auth, (req, res) => {
    if (req.dashScopePhone) return bad(res, 'غير متاح لنطاق الرقم — للمدير فقط.', 403);
    return ok(res, { list: listPhonePasswords({ mask: false }) });
  });

  api.post('/features/passwords/drop', auth, (req, res) => {
    if (req.dashScopePhone) return bad(res, 'غير متاح لنطاق الرقم — للمدير فقط.', 403);
    const phone = String(req.body?.phone || '').replace(/\D/g, '');
    const done = dropPhonePassword(phone);
    return done ? ok(res) : bad(res, 'لا توجد كلمة مرور لهذا الرقم.');
  });

  // ═══════════ ★ v3.9: المزامنة الثنائية الفورية (SSE) ═══════════
  // يفتح الموقع قناة هذه النقطة ويستقبل كل تغييرات البوت فوراً
  // (إيموجي/تفاعل/حالة/خيار/ربط/فك ربط) — والموقع يحدّث واجهته لحظياً.
  api.get('/events', (req, res) => {
    const token = req.header('x-dash-token') || req.query.token;
    if (!validToken(token)) return res.status(401).json({ ok: false, error: 'انتهت الجلسة.' });
    const rec = tokenRecord(token);
    res.setHeader('content-type', 'text/event-stream');
    res.setHeader('cache-control', 'no-cache');
    res.setHeader('connection', 'keep-alive');
    res.setHeader('x-accel-buffering', 'no');
    res.flushHeaders?.();
    res.write(`data: ${JSON.stringify({ event: 'connected', data: { scope: rec?.scopePhone || null } })}\n\n`);
    const id = addSseClient(res, { userId: rec?.scopePhone || null });
    req.on('close', () => removeSseClient(id));
  });

  r.use('/api', api);
  return r;
}

export default createDashboardRouter;
