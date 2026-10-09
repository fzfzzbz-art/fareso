'use strict'
const { uploadImage } = require('./uploadImage')
async function TelegraPh(filePath) { return uploadImage(filePath) }
async function UploadFileUgu(filePath) { return uploadImage(filePath) }
module.exports = { TelegraPh, UploadFileUgu }
