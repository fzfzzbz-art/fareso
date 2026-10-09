// core/theme.js
// ✧ 2B - YoRHa Unit No.2 Type B - Core Theme ✧

export const theme = {
  // الرموز الأساسية (2B Style)
  skull: '❄️',
  blood: '⚔️',
  virus: '🗡️',
  eye: '🔮',
  sword: '🩸',
  target: '✧',
  darkStar: '𓉘᳟ี ⃞̸͢𑁃 ̚𓉝᳟ี',
  lightStar: '❄️ּ۪᪲۫ᮬ',
  
  // فواصل 2B
  divider: '━━━━━━━━━━━━━━━━━━━━',
  smallDivider: '━━━━━━━━━━━━━━━━━━━━',
  endDivider: '━━━━━━━━━━━━━━━━━━━━',
  
  // تنسيق النص
  title: (text) => `❄️ *${text}*`,
  subtitle: (text) => `⚔️ *${text}*`,
  info: (text) => `🔮 *${text}*`,
  warning: (text) => `⚠️ *${text}* ⚠️`,
  success: (text) => `✅ *${text}*`,
  error: (text) => `❌ *${text}*`,
  
  // build full message
  build: (sections) => {
    const lines = ['❄️ 2B - YoRHa Unit']
    for (const section of sections || []) {
      if (section.type === 'title') lines.push(`❄️ *${section.text}*`)
      else if (section.type === 'subtitle') lines.push(`⚔️ *${section.text}*`)
      else if (section.type === 'info') lines.push(`🔮 ${section.label}: ${section.value}`)
      else if (section.type === 'line') lines.push(section.text)
      else if (section.type === 'divider') lines.push(theme.smallDivider)
      else if (section.type === 'spacer') lines.push('')
    }
    lines.push(theme.endDivider)
    return lines.join('\n')
  },
  
  // رسالة الملف الشخصي
  profile: (data) => {
    let msg = `❀⃘⃛͜ ۪۪۪݃𓉘᳟ี ⃞̸͢𑁃 ̚𓉝᳟ี ͟͟͞͞⌒᳝︵໋۪۪۪۪۪᳝֔࣪┄꯭๋━┄꫶︦⡳۪۪۪۪۟︵໋۪۪۪۪۪᳝֔࣪⌒᳝ᦷ࣭࣪❄️ּ۪᪲۫ᮬ ࣭࣪ᦡ ۪ׄ⌒᳝
   ⃝⃘︢︣֟፝ · ͟͟͞͞𝐘𝐨𝐑𝐇𝐚· ͟͟͞͞➳ 𝟐𝐁
${theme.divider}
`
    for (const item of data) {
      if (item.type === 'header') {
        msg += `├ׁ̟̇˚₊· ͟͟͞͞➳❥ ${item.text}\n`
      } else if (item.type === 'info') {
        msg += `├ׁ̟̇˚₊· ͟͟͞͞➳❥ ${item.label}: ${item.value}\n`
      } else if (item.type === 'line') {
        msg += `├ׁ̟̇˚₊· ͟͟͞͞➳❥ ${item.text}\n`
      }
    }
    msg += `${theme.endDivider}`
    return msg
  }
}

export const formatWithTheme = (data) => {
  return theme.build(data)
}