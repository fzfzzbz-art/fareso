'use strict'
const messages = new Map()
function setMessage(key, value) { messages.set(String(key), value) }
function getMessage(key) { return messages.get(String(key)) || null }
function deleteMessage(key) { return messages.delete(String(key)) }
function findMessage(predicate) { return Array.from(messages.values()).find(predicate) || null }
module.exports = { setMessage, getMessage, deleteMessage, findMessage, messages }
