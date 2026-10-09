// core/ytdlp.js
// ✧ 2B - YoRHa Unit No.2 Type B - YT-DLP Auto Manager 🔧

import { exec } from 'child_process'
import { promisify } from 'util'
import { existsSync, chmodSync, writeFileSync, readFileSync, mkdirSync } from 'fs'
import { join } from 'path'
import os from 'os'

const execAsync = promisify(exec)

let ytdlpPath = null
let isInstalling = false
let installPromise = null

const COOKIES_DIR = join(process.cwd(), 'cookies')
try { mkdirSync(COOKIES_DIR, { recursive: true }) } catch {}

const INSTAGRAM_COOKIES = join(COOKIES_DIR, 'instagram.txt')

const INSTAGRAM_COOKIES_DATA = `# Netscape HTTP Cookie File\n`;;

function initCookies() {
    if (!existsSync(INSTAGRAM_COOKIES)) {
        writeFileSync(INSTAGRAM_COOKIES, INSTAGRAM_COOKIES_DATA)
        console.log('[2B] ✅ تم إنشاء ملف كوكيز Instagram المحلي')
    }
}

function detectArchitecture() {
    const arch = os.arch()
    const platform = os.platform()
    
    const archMap = {
        'x64': 'amd64', 'x86_64': 'amd64', 'amd64': 'amd64',
        'arm64': 'arm64', 'aarch64': 'arm64',
        'armv7l': 'armv7l', 'armv6l': 'armv6l',
        'i386': 'i386', 'i686': 'i386', 'x86': 'i386'
    }
    
    return {
        arch: archMap[arch] || arch,
        platform: platform === 'win32' ? 'windows' : platform === 'darwin' ? 'macos' : 'linux'
    }
}

async function downloadYTDLP() {
    const { arch, platform } = detectArchitecture()
    
    try {
        await execAsync('pip install -q yt-dlp', { timeout: 120000 })
        await execAsync('python3 -m yt_dlp --version', { timeout: 10000 })
        return 'python3 -m yt_dlp'
    } catch {}

    try {
        const outputPath = join('/tmp', 'yt-dlp')
        try { await execAsync(`rm -f "${outputPath}"`) } catch {}
        
        await execAsync(`wget -q -O "${outputPath}" "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux"`, { timeout: 120000 })
        
        if (existsSync(outputPath)) {
            chmodSync(outputPath, 0o755)
            return outputPath
        }
    } catch {}

    try {
        const outputPath = join('/tmp', 'yt-dlp')
        try { await execAsync(`rm -f "${outputPath}"`) } catch {}
        await execAsync(`curl -L -o "${outputPath}" "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux"`, { timeout: 120000 })
        
        if (existsSync(outputPath)) {
            chmodSync(outputPath, 0o755)
            return outputPath
        }
    } catch {}

    return null
}

async function checkYTDLP() {
    const paths = [
        join('/tmp', 'yt-dlp'),
        join(process.cwd(), 'yt-dlp'),
        '/usr/local/bin/yt-dlp',
        '/usr/bin/yt-dlp'
    ]
    
    for (const p of paths) {
        if (existsSync(p)) {
            try {
                await execAsync(`"${p}" --version`, { timeout: 5000 })
                return p
            } catch {}
        }
    }
    
    try {
        await execAsync('python3 -m yt_dlp --version', { timeout: 5000 })
        return 'python3 -m yt_dlp'
    } catch {}
    
    try {
        await execAsync('yt-dlp --version', { timeout: 5000 })
        return 'yt-dlp'
    } catch {}
    
    return null
}

async function getYTDLP() {
    initCookies()
    
    if (ytdlpPath) return ytdlpPath
    if (isInstalling && installPromise) return installPromise
    
    const existing = await checkYTDLP()
    if (existing) {
        ytdlpPath = existing
        return existing
    }
    
    isInstalling = true
    installPromise = downloadYTDLP().then(path => {
        ytdlpPath = path
        isInstalling = false
        if (!path) throw new Error('كل طرق التحميل فشلت')
        return path
    })
    
    return installPromise
}

function hasCookies(platform) {
    if (platform === 'instagram') {
        return existsSync(INSTAGRAM_COOKIES)
    }
    return false
}

async function getInfo(url, options = {}) {
    const bin = await getYTDLP()
    if (!bin) throw new Error('yt-dlp غير متوفر')
    
    const { platform } = options
    
    let cookieArg = ''
    if (platform === 'instagram' && existsSync(INSTAGRAM_COOKIES)) {
        cookieArg = `--cookies "${INSTAGRAM_COOKIES}"`
    }
    
    const cmd = `${bin} -j --no-playlist ${cookieArg} "${url}"`.trim()
    
    const { stdout } = await execAsync(cmd, {
        timeout: 30000,
        maxBuffer: 1024 * 1024 * 10
    })
    return JSON.parse(stdout)
}

async function download(url, outputPath, options = {}) {
    const bin = await getYTDLP()
    if (!bin) throw new Error('yt-dlp غير متوفر')
    
    const { format, audioOnly, maxHeight, platform } = options
    
    let formatStr = 'best'
    if (audioOnly) formatStr = 'bestaudio/best'
    else if (maxHeight) formatStr = `bestvideo[height<=${maxHeight}]+bestaudio/best[height<=${maxHeight}]/best`
    else if (format) formatStr = format
    
    let cookieArg = ''
    if (platform === 'instagram' && existsSync(INSTAGRAM_COOKIES)) {
        cookieArg = `--cookies "${INSTAGRAM_COOKIES}"`
    }
    
    const audioArgs = audioOnly ? '-x --audio-format mp3' : ''
    
    const cmd = `${bin} "${url}" -o "${outputPath}" -f "${formatStr}" --no-playlist ${cookieArg} --force-overwrites ${audioArgs}`.trim()
    
    await execAsync(cmd, {
        timeout: 300000,
        maxBuffer: 1024 * 1024 * 10
    })
    
    if (!existsSync(outputPath)) throw new Error('فشل التحميل')
    return outputPath
}

export { getYTDLP, getInfo, download, hasCookies, INSTAGRAM_COOKIES }
export default getYTDLP