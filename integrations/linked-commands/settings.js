'use strict'
// إعدادات أوامر الرقم المربوط (يقرأها مجلد source-commands عبر require('../settings'))
const env = process.env || {}
const ownerList = String(env.LINKED_OWNER_NUMBERS || env.OWNER_NUMBERS || '')
  .split(/[,\s]+/)
  .map((v) => v.replace(/\D/g, ''))
  .filter(Boolean)

module.exports = {
  version: '3.15.0',
  packname: '2B - YoRHa Unit No.2 Type B',
  author: 'YoRHa No.2 Type B',
  botName: '✧ 𝟐𝐁 - YoRHa Unit No.2 Type B ✧',
  watermark: '✧ 2B - YoRHa Unit No.2 Type B ✧',
  prefix: '.',
  owner: ownerList,
  ownerNumber: ownerList[0] || '',
  ownerNumbers: ownerList,
  sudo: ownerList,
}
