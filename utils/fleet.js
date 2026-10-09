// utils/fleet.js — ★ v3.12: نظام المزامنة التلقائية بين السيرفرات (Master → Slaves)
// ─────────────────────────────────────────────────────────────────────────────
// الفكرة كاملة:
//   • السيرفر الأول (الرئيسي) هو «مصدر الحقيقة» لملفات الكود.
//   • عند إقلاع أي سيرفر عامل يطلب «بيان الملفات» (manifest) من الرئيسي:
//       GET /api/fleet/manifest → { <مسار نسبي>: { hash(sha256), size } }
//     ويقارنه بنسخته المحلية، ثم ينزّل الملفات المتغيّرة/الجديدة فقط
//     (GET /api/fleet/file?path=…) ويكتبها كتابة آمنة (tmp ثم rename).
//   • عند إعادة تشغيل السيرفر الأول يُحسب «عصر إقلاع» جديد (BOOT_EPOCH):
//       - يدفع الرئيسي إشارة إعادة تشغيل فورية لكل العمال (POST /api/fleet/restart)
//         في مسار الإيقاف النظيف (SIGINT/SIGTERM) — فتُعيد العمال تشغيلها تلقائياً.
//       - ويستقصي كل عامل /api/fleet/check كل 30 ثانية (احتياط إن فشل الدفع) —
//         فإذا تغيّر العصر: مزامنة ملفات ثم إعادة تشغيل ذاتي (تحت pm2/systemd).
//   • البيانات (data/) والجلسات وnode_modules و.env لا تُزامَن أبداً —
//     كل سيرفر يحتفظ ببياناته الخاصة.
//   • إن تغيّر package.json في المزامنة → يُطلق npm install تلقائياً في الخلفية.
// ─────────────────────────────────────────────────────────────────────────────
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import config from '../config.js';
import logger from './logger.js';
import { httpJson } from './http.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const PROJECT_ROOT = path.resolve(__dirname, '..');

// عصر إقلاع هذا السيرفر — عند إعادة تشغيل الرئيسي تتغير القيمة فيتعرّف العمال
export const BOOT_EPOCH = Date.now();

const STATE_FILE = path.join(config.dataDir, 'fleet-state.json');

// مجلدات/ملفات الكود التي تُزامَن (نسبياً عن جذر المشروع)
const SYNC_ROOTS = [
  'index.js', 'server.js', 'worker.js', 'worker-core.js', 'force-worker.js',
  'bootstrap.js', 'env-check.js', 'config.js', 'package.json', 'package-lock.json',
  'Dockerfile', 'README.md',
  'whatsapp', 'utils', 'telegram', 'dashboard', 'assets', 'scripts'
];

// أنماط مستثناة نهائياً من المزامنة (بيانات محلية/مكتبات/أسرار)
const EXCLUDE_RE = [
  /(^|\/)node_modules(\/|$)/,
  /(^|\/)data(\/|$)/,            // بيانات كل سيرفر خاصة به
  /(^|\/)\.env(\..+)?$/,         // الأسرار لا تُزامَن
  /(^|\/)bin(\/|$)/,             // أدوات yt-dlp/ffmpeg المحلية
  /(^|\/)sessions(\/|$)/,
  /(^|\/)tmp(\/|$)/,
  /\.tmp$|\.corrupt-|\.log$|\.bak$/
];

const isExcluded = (rel) => EXCLUDE_RE.some((re) => re.test(rel));

function walkDir(absDir, out = []) {
  let entries = [];
  try { entries = fs.readdirSync(absDir, { withFileTypes: true }); } catch { return out; }
  for (const e of entries) {
    const abs = path.join(absDir, e.name);
    if (e.isDirectory()) walkDir(abs, out);
    else if (e.isFile()) out.push(abs);
  }
  return out;
}

/** بيان الملفات المحلي: { <مسار نسبي بفواصل يونكس>: { hash, size } } */
export function computeManifest() {
  const manifest = {};
  for (const root of SYNC_ROOTS) {
    const abs = path.join(PROJECT_ROOT, root);
    if (!fs.existsSync(abs)) continue;
    const st = fs.statSync(abs);
    if (st.isDirectory()) {
      for (const absFile of walkDir(abs)) {
        const rel = path.relative(PROJECT_ROOT, absFile).split(path.sep).join('/');
        if (isExcluded(rel)) continue;
        try {
          const buf = fs.readFileSync(absFile);
          manifest[rel] = { hash: sha256(buf), size: buf.length };
        } catch { /* تجاهل ملف مقفول */ }
      }
    } else {
      const rel = root;
      if (isExcluded(rel)) continue;
      try {
        const buf = fs.readFileSync(abs);
        manifest[rel] = { hash: sha256(buf), size: buf.length };
      } catch { /* تجاهل */ }
    }
  }
  return manifest;
}

/** بصمة إجمالية للبيان (لتصغير حجم المقارنة) */
export function manifestFingerprint(manifest) {
  const compact = Object.entries(manifest || {})
    .map(([p, v]) => `${p}:${v.hash}`)
    .sort()
    .join('|');
  return sha256(Buffer.from(compact));
}

function sha256(buf) {
  return crypto.createHash('sha256').update(buf).digest('hex');
}

// ═══════════════ حالة المزامنة المحلية (على العامل) ═══════════════

export function loadFleetState() {
  try {
    return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
  } catch {
    return { epoch: null, lastSyncAt: 0, lastChanged: [] };
  }
}

export function saveFleetState(state) {
  try {
    fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true });
    const tmp = `${STATE_FILE}.${process.pid}.tmp`;
    fs.writeFileSync(tmp, JSON.stringify(state, null, 2), 'utf8');
    fs.renameSync(tmp, STATE_FILE);
  } catch (err) {
    logger.warn({ err: err?.message || err }, 'فشل حفظ حالة المزامنة');
  }
}

// ═══════════════ العامل: المزامنة عند الإقلاع ═══════════════

/**
 * مزامنة كاملة من الرئيسي عند إقلاع العامل.
 * @returns {Promise<{ ok: boolean, changed: string[], npmInstalled: boolean, error?: string }>}
 */
export async function fleetSyncOnBoot() {
  if (config.isMain || !config.fleet?.enabled) return { ok: true, changed: [], npmInstalled: false };
  return syncFromMaster();
}

export async function syncFromMaster() {
  const base = String(config.mainApiUrl || '').replace(/\/+$/, '');
  // 1) جلب البيان
  const res = await httpJson(`${base}/api/fleet/manifest`, { method: 'GET', timeoutMs: 20000 });
  if (!res.ok || !res.data?.ok || !res.data?.manifest) {
    return { ok: false, changed: [], npmInstalled: false, error: res.error || 'تعذّر جلب بيان الملفات' };
  }
  const remote = res.data.manifest;
  const masterEpoch = res.data.epoch || null;
  const local = computeManifest();

  // 2) المقارنة: الجديد/المتغيّر ينزَّل، المحذوف على الرئيسي يُحذف محلياً
  const changed = [];
  const removed = [];
  for (const [rel, meta] of Object.entries(remote)) {
    if (isExcluded(rel)) continue;
    const mine = local[rel];
    if (!mine || mine.hash !== meta.hash) changed.push(rel);
  }
  for (const rel of Object.keys(local)) {
    if (!remote[rel]) removed.push(rel);
  }

  if (changed.length) {
    fs.mkdirSync(path.join(PROJECT_ROOT, 'data'), { recursive: true });
    for (const rel of changed) {
      try {
        const url = `${base}/api/fleet/file?path=${encodeURIComponent(rel)}`;
        const r = await fetch(url, { headers: { 'x-api-secret': config.main.apiSecret } });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const buf = Buffer.from(await r.arrayBuffer());
        // التحقق من السلامة قبل الكتابة
        if (sha256(buf) !== remote[rel].hash) throw new Error('فحص الهاش فشل');
        const abs = path.join(PROJECT_ROOT, ...rel.split('/'));
        fs.mkdirSync(path.dirname(abs), { recursive: true });
        const tmp = `${abs}.fleet-${process.pid}.tmp`;
        fs.writeFileSync(tmp, buf);
        fs.renameSync(tmp, abs);
        logger.info({ file: rel, bytes: buf.length }, '⬇️ مزامنة: تحديث ملف من السيرفر الرئيسي');
      } catch (err) {
        logger.warn({ err: err?.message || err, file: rel }, 'فشل تنزيل ملف من الرئيسي — سيُعاد في الاستقصاء القادم');
      }
    }
  }

  for (const rel of removed) {
    // لا نحذف إلا ملفات كود معروفة (وليس مجلدات بيانات)
    if (isExcluded(rel)) continue;
    try { fs.rmSync(path.join(PROJECT_ROOT, ...rel.split('/')), { force: true }); } catch { /* تجاهل */ }
  }

  // 3) إن تغيّر package.json → تثبيت التبعيات في الخلفية بلا حجب الإقلاع
  let npmInstalled = false;
  if (changed.includes('package.json')) {
    try {
      const child = spawn('npm', ['install', '--omit=dev', '--no-audit', '--no-fund'], {
        cwd: PROJECT_ROOT, detached: true, stdio: 'ignore'
      });
      child.on('error', () => {});
      child.unref();
      npmInstalled = true;
      logger.info('📦 تغيّر package.json — جارٍ تثبيت التبعيات في الخلفية');
    } catch { /* تجاهل */ }
  }

  // 4) حفظ عصر الرئيسي الحالي (يُقارن به لاحقاً لاكتشاف إعادة تشغيل الرئيسي)
  if (masterEpoch) saveFleetState({ epoch: masterEpoch, lastSyncAt: Date.now(), lastChanged: changed });

  return { ok: true, changed, removed, npmInstalled, epoch: masterEpoch };
}

/**
 * الاستقصاء الدوري (على العامل): هل أعاد الرئيسي التشغيل؟
 * إذا تغيّر العصر → مزامنة ثم إعادة تشغيل ذاتية (تحت pm2/systemd).
 */
export async function fleetPollCheck() {
  if (config.isMain || !config.fleet?.enabled) return;
  try {
    const base = String(config.mainApiUrl || '').replace(/\/+$/, '');
    const res = await httpJson(`${base}/api/fleet/check`, { method: 'GET', timeoutMs: 10000 });
    if (!res.ok || !res.data?.ok) return;
    const epoch = res.data.epoch;
    const state = loadFleetState();

    if (state.epoch && epoch && state.epoch !== epoch) {
      logger.info({ from: state.epoch, to: epoch }, '🔔 السيرفر الرئيسي أُعيد تشغيله — مزامنة وإعادة تشغيل متزامنة');
      const out = await syncFromMaster();
      saveFleetState({ epoch, lastSyncAt: Date.now(), lastChanged: out.changed || [] });
      if (config.fleet?.autoRestart) {
        logger.warn('♻️ إعادة تشغيل العامل لمزامنة الكود الجديد (pm2/systemd سيعيد تشغيله تلقائياً)…');
        setTimeout(() => process.exit(0), 1200);
      }
      return out;
    }
  } catch (err) {
    logger.debug({ err: err?.message || err }, 'فشل استقصاء المزامنة');
  }
  return null;
}

// ═══════════════ الرئيسي: إشعار العمال عند إعادة التشغيل ═══════════════

/**
 * يدفع أمر إعادة تشغيل لكل السيرفرات الفرعية (يُستدعى من مسار الإيقاف النظيف
 * للسيرفر الرئيسي — SIGINT/SIGTERM — وإن فشل الدفع فالاستقصاء الدوري يلحقها).
 */
export async function notifyFleetRestart(reason = 'master-restart') {
  if (config.isMain || !config.fleet?.enabled) return;
  return; // لا يُنفّذ إلا على الرئيسي (حماية من الاستدعاء الخطأ)
}

export async function notifyWorkersRestart(reason = 'master-restart') {
  if (!config.isMain || !config.fleet?.enabled) return { notified: 0 };
  let servers = {};
  try {
    const { serversStore } = await import('./store.js');
    servers = serversStore.get('servers') || {};
  } catch { return { notified: 0 }; }

  const targets = Object.values(servers).filter((s) => s && !s.isLocal && s.url);
  let notified = 0;
  await Promise.all(
    targets.map(async (srv) => {
      try {
        const res = await httpJson(`${srv.url}/api/fleet/restart`, {
          body: { epoch: BOOT_EPOCH, reason }, timeoutMs: 6000
        });
        if (res.ok) notified += 1;
      } catch { /* الاستقصاء سيلحق العامل */ }
    })
  );
  logger.info({ notified, total: targets.length }, '📣 أُرسلت إشارة إعادة التشغيل للسيرفرات الفرعية');
  return { notified, total: targets.length };
}

/** قراءة ملف للنقل (على الرئيسي) — يُقبل فقط ما هو موجود في البيان (حماية مسارات) */
export function readSyncedFile(rel) {
  const clean = String(rel || '').replace(/\\/g, '/').replace(/\.\.+/g, '');
  if (!clean || isExcluded(clean)) return null;
  const manifest = computeManifest();
  if (!manifest[clean]) return null;
  try {
    return fs.readFileSync(path.join(PROJECT_ROOT, ...clean.split('/')));
  } catch {
    return null;
  }
}

export default {
  computeManifest, manifestFingerprint, fleetSyncOnBoot, fleetPollCheck,
  notifyWorkersRestart, readSyncedFile, syncFromMaster, BOOT_EPOCH, loadFleetState, saveFleetState
};
