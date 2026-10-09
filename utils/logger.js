// utils/logger.js — لوجر موحّد + حلقة سجلّ (ring buffer) تُقرأ منها لوحة التحكم
// ملاحظة: إن لم يكن pino-pretty مثبّتاً فسنعمل بلوجر عادي بدل أن يفشل التشغيل.
import pino from 'pino';

const level = process.env.LOG_LEVEL || 'info';

const MAX_LOGS = 400;
const ring = [];

/** آخر سطور السجل (الأحدث أولاً) — تُستخدم في لوحة التحكم */
export function recentLogs(limit = 200) {
  return ring.slice(-Math.min(limit, MAX_LOGS)).reverse();
}

export function clearLogs() {
  ring.length = 0;
}

function push(line) {
  const text = String(line || '').replace(/\u001b\[[0-9;]*m/g, '').trimEnd();
  if (!text) return;
  ring.push(text);
  if (ring.length > MAX_LOGS) ring.splice(0, ring.length - MAX_LOGS);
}

const captureStream = {
  write(line) {
    push(line);
  }
};

let pretty = null;
try {
  const { createRequire } = await import('node:module');
  const require = createRequire(import.meta.url);
  require.resolve('pino-pretty');
  pretty = { target: 'pino-pretty', options: { colorize: true, translateTime: 'SYS:HH:MM:ss', ignore: 'pid,hostname' } };
} catch {
  pretty = null;
}

const appName = process.env.ROLE === 'worker' ? 'wa-worker' : 'wa-tg-bot';

export const logger = pretty
  ? pino(
      { level },
      pino.multistream([
        { level, stream: pino.transport(pretty) },
        { level, stream: captureStream }
      ])
    ).child({ app: appName })
  : pino({ level }, pino.multistream([{ level, stream: captureStream }])).child({ app: appName });

export default logger;
