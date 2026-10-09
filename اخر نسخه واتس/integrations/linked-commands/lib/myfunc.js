'use strict'
const axios = require('axios')
async function sleep(ms = 1000) { return new Promise((resolve) => setTimeout(resolve, Number(ms) || 0)) }
async function fetchBuffer(url, options = {}) {
  const response = await axios.get(url, { responseType: 'arraybuffer', timeout: options.timeout || 60000, headers: options.headers || { 'User-Agent': 'Mozilla/5.0' } })
  return Buffer.from(response.data || [])
}
module.exports = { sleep, fetchBuffer }
