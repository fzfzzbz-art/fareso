// plugins/mylid.js
let handler = async (m, { conn }) => {
    let sender = m.sender;
    let imageUrl = 'https://file.garden/aauvg01sjleV_ic1/2cfe027e0a045daa76a551309a8040df.jpg';
    
    await conn.sendButton(m.chat, sender, '', imageUrl, null, [['📋 نسخ LID', sender]], null, null, m);
};

handler.command = /^lid$/i;
handler.group = true;
export default handler;