// utils/queue.js — ★ v3.12: طوابير تنفيذ خفيفة (بلا تبعيات خارجية)
// ─────────────────────────────────────────────────────────────────────────────
// • pLimit(n): يحدّد أقصى عدد مهام متوازية — يمنع انهيار الحدث تحت الضغط العالي
//   (فلود رسائل واتساب / ضغط تيليجرام) بدل تنفيذ آلاف المهام دفعة واحدة.
// • تُستخدم في session.js (طابور الرسائل + طابور أوامر متسلسل) وفي الإذاعات.
// ─────────────────────────────────────────────────────────────────────────────

/**
 * يُنشئ مُحدِّد تزامن بأسلوب p-limit:
 *   const lim = pLimit(4); await lim(() => doWork());
 * المهام الزائدة تنتظر في طابور FIFO بلا استهلاك موارد.
 * @param {number} concurrency أقصى عدد مهام متوازية (>=1)
 */
export function pLimit(concurrency) {
  const limit = Math.max(1, Number(concurrency) || 1);
  let active = 0;
  const queue = [];

  const next = () => {
    if (active >= limit) return;
    const item = queue.shift();
    if (!item) return;
    item.run();
  };

  const schedule = (fn) =>
    new Promise((resolve, reject) => {
      queue.push({
        run: () => {
          active += 1;
          Promise.resolve()
            .then(fn)
            .then(resolve, reject)
            .finally(() => {
              active -= 1;
              next();
            });
        }
      });
      next();
    });

  return schedule;
}

/**
 * طابور مهام دائم بسر موحد — كل دفعة تُنفَّذ بالتتابع بغض النظر عن التزامن.
 * يُستخدم لتنفيذ أوامر الواتساب بالتسلسل لمنع سباق الردود تحت الفلود.
 */
export function createSerialQueue() {
  return pLimit(1);
}

/** مدة انتظار بسيطة */
export const delay = (ms) => new Promise((r) => setTimeout(r, ms));

export default { pLimit, createSerialQueue, delay };
