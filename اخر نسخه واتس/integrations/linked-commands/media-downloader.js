'use strict'

// جسر CommonJS لأوامر silana-lite إلى محرك التحميل الموحد في المشروع.
const path = require('node:path')
const fs = require('node:fs')

let downloaderPromise
const trackedDownloads = new Map()

function downloader() {
  if (!downloaderPromise) {
    downloaderPromise = import('../../whatsapp/downloader.js').then((mod) => mod.default || mod)
  }
  return downloaderPromise
}

function extractFirstSupportedUrl(text, platformHint = '') {
  const value = String(text || '')
  const urls = [...new Set((value.match(/https?:\/\/[^\s<>"']+/gi) || [])
    .map((url) => url.replace(/[)\]}.,،؛;!]+$/, '')))]
  const platform = String(platformHint || '').toLowerCase()
  const patterns = {
    tiktok: /(?:tiktok\.com|douyin\.com|vt\.tiktok|v\.douyin)/i,
    instagram: /(?:instagram\.com|instagr\.am)/i,
  }
  return urls.find((url) => patterns[platform]?.test(url)) || null
}

async function downloadSocialVideo(url, { platformHint = '' } = {}) {
  const api = await downloader()
  const detected = api.detectPlatform(url)
  if (platformHint && detected && detected !== platformHint) {
    throw new Error(`الرابط ليس رابط ${platformHint === 'tiktok' ? 'تيك توك' : 'إنستغرام'}.`)
  }
  const result = await api.downloadMedia(url, { quality: 'auto' })
  if (!result?.ok || !result.file) {
    throw new Error(result?.error || 'تعذر تنزيل الوسائط من الرابط.')
  }
  const filePath = result.file
  trackedDownloads.set(path.resolve(filePath), result.dir || path.dirname(filePath))
  return {
    filePath,
    fileSizeBytes: Number(result.sizeBytes || fs.statSync(filePath).size),
    metadata: {
      title: result.title || (platformHint === 'tiktok' ? 'فيديو تيك توك' : 'فيديو إنستغرام'),
      platform: result.platform || detected || platformHint,
      durationSec: result.durationSec || null,
    },
  }
}

async function cleanupDownloadedFile(filePath) {
  if (!filePath) return true
  const resolved = path.resolve(String(filePath))
  const dir = trackedDownloads.get(resolved)
  trackedDownloads.delete(resolved)
  if (dir) {
    try {
      const api = await downloader()
      return await api.cleanupDownload(dir)
    } catch { /* نتبع بحذف الملف الفردي أدناه */ }
  }
  try { await fs.promises.rm(resolved, { force: true }); return true } catch { return false }
}

module.exports = {
  extractFirstSupportedUrl,
  downloadSocialVideo,
  cleanupDownloadedFile,
}
