'use strict'

const fs = require('node:fs')
const path = require('node:path')

// نسخة JPEG صغيرة من صورة لوفي لتقليل حجم رأس البطاقة التفاعلية.
const menuLuffy = fs.readFileSync(path.join(__dirname, 'assets', 'menu-luffy.jpg'))
module.exports = { menuLuffy }
