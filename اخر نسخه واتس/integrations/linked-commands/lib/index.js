'use strict'
const fs = require('fs')
const path = require('path')
const settings = require('../settings')
const isOwner = require('./isOwner')
const dataFile = path.join(__dirname, '..', 'data', 'userGroupData.json')
const sudoFile = path.join(__dirname, '..', 'data', 'sudo.json')
function ensureDir() { fs.mkdirSync(path.dirname(dataFile), { recursive: true }) }
function readJson(file, fallback) { try { return JSON.parse(fs.readFileSync(file, 'utf8')) } catch { return fallback } }
function writeJson(file, data) { ensureDir(); fs.writeFileSync(file, JSON.stringify(data, null, 2)) }
function loadGroupData() {
  return readJson(dataFile, { antilink: {}, antibadword: {}, welcome: {}, goodbye: {}, chatbot: {}, antitag: {}, autoReaction: false })
}
function saveGroupData(data) { writeJson(dataFile, data) }
function loadSudo() { return readJson(sudoFile, { numbers: [] }) }
function saveSudo(data) { writeJson(sudoFile, data) }
function normalize(value) { return String(value || '').replace(/\D/g, '') }
async function isSudo(senderId) {
  const sudo = loadSudo().numbers || []
  const sender = normalize(senderId)
  if ((settings.ownerNumbers || []).map(normalize).includes(sender)) return true
  if (normalize(settings.ownerNumber) === sender) return true
  return sudo.map(normalize).includes(sender)
}
function addSudo(number) {
  const state = loadSudo(); const n = normalize(number)
  if (!n) return false
  if (!Array.isArray(state.numbers)) state.numbers = []
  if (!state.numbers.includes(n)) state.numbers.push(n)
  saveSudo(state); return true
}
function removeSudo(number) {
  const state = loadSudo(); const n = normalize(number)
  state.numbers = (state.numbers || []).filter((x) => normalize(x) !== n)
  saveSudo(state); return true
}
function getSudoList() { return loadSudo().numbers || [] }
function setCfg(section, groupId, cfg) { const data = loadGroupData(); data[section] = data[section] || {}; data[section][groupId] = cfg; saveGroupData(data); return true }
function getCfg(section, groupId) { const data = loadGroupData(); return data[section]?.[groupId] || null }
function removeCfg(section, groupId) { const data = loadGroupData(); if (data[section]) delete data[section][groupId]; saveGroupData(data); return true }
function setAntilink(groupId, enabled = 'on', action = 'delete') { return setCfg('antilink', groupId, { enabled: enabled === 'on' || enabled === true, action }) }
function getAntilink(groupId) { return getCfg('antilink', groupId) }
function removeAntilink(groupId) { return removeCfg('antilink', groupId) }
function setAntitag(groupId, enabled = 'on', action = 'delete') { return setCfg('antitag', groupId, { enabled: enabled === 'on' || enabled === true, action }) }
function getAntitag(groupId) { return getCfg('antitag', groupId) }
function removeAntitag(groupId) { return removeCfg('antitag', groupId) }
function isWelcomeOn(groupId) { return !!getCfg('welcome', groupId)?.enabled }
function getWelcome(groupId) { return getCfg('welcome', groupId)?.message || '' }
function isGoodByeOn(groupId) { return !!getCfg('goodbye', groupId)?.enabled }
function getGoodbye(groupId) { return getCfg('goodbye', groupId)?.message || '' }
module.exports = {
  isSudo, addSudo, removeSudo, getSudoList,
  setAntilink, getAntilink, removeAntilink,
  setAntitag, getAntitag, removeAntitag,
  isWelcomeOn, getWelcome, isGoodByeOn, getGoodbye,
  loadGroupData, saveGroupData,
}
