// utils/events.js — ناقل أحداث عام بسيط (بلا تبعيات)
// الهدف: يبلّغ كل الأطراف عند إبطال جلسة واتساب من الهاتف (loggedOut)
// دون خلق استيراد دائري بين session.js و manager.js و index.js/worker-core.js.
const loggedOutHandlers = [];

export function onLoggedOut(fn) {
  if (typeof fn === 'function') loggedOutHandlers.push(fn);
  return loggedOutHandlers.length;
}

export function emitLoggedOut(payload) {
  for (const h of [...loggedOutHandlers]) {
    try {
      const r = h(payload);
      if (r && typeof r.catch === 'function') r.catch(() => {});
    } catch { /* معالج واحد لا يجب أن يُسقط البقية */ }
  }
}

export default { onLoggedOut, emitLoggedOut };
