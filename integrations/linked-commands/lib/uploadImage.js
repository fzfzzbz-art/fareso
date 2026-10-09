'use strict'
const fs = require('fs')
const path = require('path')
const axios = require('axios')
const FormData = require('form-data')
async function uploadImage(input) {
  let filePath = input
  if (Buffer.isBuffer(input)) {
    const tmpDir = path.join(process.cwd(), 'tmp')
    fs.mkdirSync(tmpDir, { recursive: true })
    filePath = path.join(tmpDir, `upload_${Date.now()}.jpg`)
    fs.writeFileSync(filePath, input)
  }
  const form = new FormData()
  form.append('file', fs.createReadStream(filePath))
  const res = await axios.post('https://telegra.ph/upload', form, { headers: form.getHeaders(), timeout: 60000 })
  const first = Array.isArray(res.data) ? res.data[0] : null
  if (!first?.src) throw new Error('telegra.ph upload failed')
  return `https://telegra.ph${first.src}`
}
module.exports = { uploadImage }
