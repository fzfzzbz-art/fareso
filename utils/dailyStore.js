// utils/dailyStore.js — ★ v3.12: مخزن الأدوات اليومية (مهام، مصروفات، تذكيرات، تسبيح)
// ─────────────────────────────────────────────────────────────────────────────
// مفتاح التخزين هو المحادثة (خاص أو مجموعة) — كل محادثة لها قوائمها الخاصة:
//   tasks     : [{ id, text, done, at }]
//   expenses  : [{ id, label, amount, at }]
//   counters  : { <اسم>: n }        (عدّادات مثل التسبيح)
// ─────────────────────────────────────────────────────────────────────────────
import path from 'node:path';
import { JsonStore } from './store.js';
import config from '../config.js';

export const dailyStore = new JsonStore(path.join(config.dataDir, 'daily-store.json'), { chats: {} });

function chatKey(chatId) {
  return String(chatId || '').split('@')[0];
}

/** بيانات محادثة مع إنشائها */
export function cset(chatId) {
  const chats = dailyStore.get('chats') || {};
  const key = chatKey(chatId);
  if (!chats[key]) {
    chats[key] = { tasks: [], expenses: [], counters: {} };
    dailyStore.set('chats', chats);
  }
  return chats[key];
}

function save(chatId, data) {
  const chats = dailyStore.get('chats') || {};
  chats[chatKey(chatId)] = data;
  dailyStore.set('chats', chats);
}

// ─────────── المهام ───────────
export function listTasks(chatId) {
  return cset(chatId).tasks;
}

export function addTask(chatId, text) {
  const c = cset(chatId);
  const id = (c.tasks.reduce((m, t) => Math.max(m, t.id || 0), 0) || 0) + 1;
  c.tasks.push({ id, text: String(text).slice(0, 300), done: false, at: Date.now() });
  save(chatId, c);
  return c.tasks[c.tasks.length - 1];
}

export function doneTask(chatId, id) {
  const c = cset(chatId);
  const t = c.tasks.find((x) => x.id === Number(id));
  if (t) { t.done = true; save(chatId, c); }
  return t || null;
}

export function clearTasks(chatId, onlyDone = false) {
  const c = cset(chatId);
  const before = c.tasks.length;
  c.tasks = onlyDone ? c.tasks.filter((t) => !t.done) : [];
  save(chatId, c);
  return before - c.tasks.length;
}

// ─────────── المصروفات ───────────
export function listExpenses(chatId) {
  return cset(chatId).expenses;
}

export function addExpense(chatId, label, amount) {
  const c = cset(chatId);
  const amt = Number(String(amount).replace(/[^\d.]/g, ''));
  if (!Number.isFinite(amt) || amt <= 0) return null;
  const id = (c.expenses.reduce((m, e) => Math.max(m, e.id || 0), 0) || 0) + 1;
  const rec = { id, label: String(label).slice(0, 120), amount: amt, at: Date.now() };
  c.expenses.push(rec);
  save(chatId, c);
  return rec;
}

export function expenseTotal(chatId) {
  return listExpenses(chatId).reduce((s, e) => s + e.amount, 0);
}

export function clearExpenses(chatId) {
  const c = cset(chatId);
  const n = c.expenses.length;
  c.expenses = [];
  save(chatId, c);
  return n;
}

// ─────────── العدّادات (تسبيح وغيره) ───────────
export function bumpCounter(chatId, name, add = 1) {
  const c = cset(chatId);
  c.counters[name] = (c.counters[name] || 0) + add;
  save(chatId, c);
  return c.counters[name];
}

export function getCounter(chatId, name) {
  return cset(chatId).counters[name] || 0;
}

export function resetCounter(chatId, name) {
  const c = cset(chatId);
  delete c.counters[name];
  save(chatId, c);
}
