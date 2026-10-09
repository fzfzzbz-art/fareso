// utils/features.js — ★ v3.11: نظام الإعدادات الشاملة (أكثر من 100 خيار تحكم لكل رقم)
// ─────────────────────────────────────────────────────────────────────────────
// • كل رقم مربوط له كائن إعدادات خاص به يُحفظ في data/features.json.
// • أي تفعيل/تعطيل من الموقع يُحفظ فوراً ويُطبَّق فوراً على الجلسة الحيّة
//   (عبر المزامنة الثنائية في utils/sync.js) دون إعادة تشغيل.
// • ★ v3.11 (الإصلاح الجذري لمزامنة الموقع مع الرقم المربوط):
//   صار المخزّن يعيد القراءة من القرص تلقائياً عند تغيّر بصمة الملف (mtime+size)،
//   ويلتقط أيضاً تعديلات السيرفر الرئيسي (features-sync) التي قد لا تمرّ بنفس
//   العملية، فيقرأ كل أمر داخل الواتساب القيمة الحقيقية *الآن* لا قيمة قديمة
//   مخزّنة في الذاكرة. (هذا هو سبب أن بعض الخيارات كانت مفعّلة في الموقع
//   ومعطّلة فعلياً داخل الرقم المربوط.)
// • الأوامر الداخلية داخل الواتساب تستعلم عن هذه الخيارات عبر isEnabled(phone, key).
// • القوائم مبنية من GROUPS: كل مجموعة تجمع خيارات مترابطة لتسهيل العرض في الموقع.
// ─────────────────────────────────────────────────────────────────────────────
import fs from 'node:fs';
import { JsonStore } from './store.js';
import config from '../config.js';
import logger from './logger.js';

// ─────────── مخزّن مُتساهل مع التعديل الخارجي (External-Aware Store) ───────────
/**
 * يمتد من JsonStore ويضيف: إن تغيّر ملف features.json على القرص (من أي عملية
 * أخرى — العامل، الرئيسي، أو تحرير يدوي) تُعاد قراءته فوراً قبل أي قراءة/كتابة.
 */
class LiveJsonStore extends JsonStore {
  constructor(filePath, defaultValue = {}) {
    super(filePath, defaultValue);
    this._sig = null;
  }

  /** بصمة الملف: وقت التعديل + الحجم (رخيصة جداً — استدعاء stat واحد) */
  _signature() {
    try {
      const st = fs.statSync(this.filePath);
      return `${st.mtimeMs}:${st.size}`;
    } catch {
      return 'missing';
    }
  }

  /** أعِد القراءة من القرص إن تغيّر الملف، أو إن لم تُقرأ بعد */
  refresh({ force = false } = {}) {
    const sig = this._signature();
    if (force || !this._loaded || sig !== this._sig) {
      // مهم: لا نستدعي load() إن كان الملف غير موجود حتى لا يُنشئه في كل فحص
      if (sig === 'missing' && !this._loaded) {
        this._loaded = true;
        this.data = structuredClone(this.defaultValue);
        this._sig = sig;
        return this.data;
      }
      this.load();
      this._sig = this._signature();
    }
    return this.data;
  }

  /** ★ v3.11: كتابة فورية مضمونة على القرص قبل أن يُرسَل أي رد للواجهة */
  setSync(key, value) {
    this.refresh();
    this.data[key] = value;
    this.saveSync();
    this._sig = this._signature();
    return value;
  }

  get(key) { this.refresh(); return super.get(key); }
  set(key, value) { this.refresh(); const r = super.set(key, value); this._sig = this._signature(); return r; }
  delete(key) { this.refresh(); const r = super.delete(key); this._sig = this._signature(); return r; }
  has(key) { this.refresh(); return super.has(key); }
  all() { this.refresh(); return super.all(); }
  saveSync() { const r = super.saveSync(); this._sig = this._signature(); return r; }
  async save() { const r = await super.save(); this._sig = this._signature(); return r; }
}

export const featuresStore = new LiveJsonStore(config.featuresFile, { phones: {} });

// ─────────── تعريف مجموعات الخيارات (أكثر من 100 خيار) ───────────
// [key, الاسم بالعربية, الافتراضي true/false]
export const FEATURE_GROUPS = [
  {
    key: 'commands', name: 'الأوامر الداخلية', icon: '⌨️',
    features: [
      ['cmds_general', 'الأوامر العامة (الاوامر، البنك…)', true],
      ['cmds_groups', 'أوامر المجموعات', true],
      ['cmds_media', 'أوامر الوسائط', true],
      ['cmds_download', 'أوامر التحميل من المنصات', true],
      ['cmds_tools', 'أوامر الأدوات', true],
      ['cmds_fun', 'أوامر الترفيه', true],
      ['cmds_ai', 'أوامر الذكاء الاصطناعي', true],
      ['cmds_extra', 'الأوامر الإضافية', true],
      ['cmds_custom', 'الأوامر المخصّصة النصية', true],
      ['cmds_custom_files', 'أوامر الملفات المرفوعة', true],
      ['cmds_owner_only', 'أوامر المالك فقط (قفل للمالك)', true],
      ['cmds_prefix_dot', 'بادئة النقطة (.الأمر)', true],
      ['cmds_prefix_slash', 'بادئة الشرطة (/الأمر)', true],
      ['cmds_no_prefix', 'الأوامر بدون بادئة', false],
      ['cmds_welcome_new_member', 'ترحيب بالعضو الجديد في المجموعات', true],
      ['cmds_goodbye_member', 'وداع من يغادر المجموعة', true],
      ['cmds_group_link_protect', 'حماية المجموعة من روابط الإعلانات', false],
      ['cmds_antilink', 'مضاد الروابط في المجموعات', false],
      ['cmds_antisticker', 'مضاد الملصقات في المجموعات', false],
      ['cmds_welcome_dm', 'رسالة ترحيب أول مرة يكتب أحد للحساب', true]
    ]
  },
  {
    key: 'status', name: 'الحالات والتفاعل', icon: '👁️',
    features: [
      ['status_auto_view', 'المشاهدة التلقائية للحالات', true],
      ['status_auto_react', 'التفاعل التلقائي بالإيموجي', true],
      ['status_auto_like', 'القلب الأخضر التلقائي', true],
      ['status_auto_archive', 'نقل الحالات للمشاهدة (الأرشفة)', true],
      ['status_read_receipts', 'إرسال إيصالات القراءة للحالات', true],
      ['status_react_text', 'التفاعل مع الحالات النصية', true],
      ['status_react_image', 'التفاعل مع الحالات المصوّرة', true],
      ['status_react_video', 'التفاعل مع حالات الفيديو', true],
      ['status_react_audio', 'التفاعل مع الحالات الصوتية', true],
      ['status_react_own_status', 'التفاعل مع حالاتي الخاصة', false],
      ['status_delayed_react', 'تأخير عشوائي بين التفاعلات', true],
      ['status_notify_owner', 'إشعار صاحب الرقم عند تفاعل جديد', false],
      ['status_daily_report', 'تقرير يومي بعدد الحالات المشاهدة', false],
      ['status_blacklist_mode', 'وضع القائمة السوداء للتفاعل', false],
      ['status_only_contacts', 'التفاعل مع حالات جهات الاتصال فقط', false]
    ]
  },
  {
    key: 'antidelete', name: 'مضاد الحذف والكشف', icon: '🛡️',
    features: [
      ['antidelete_messages', 'مضاد حذف الرسائل (تقاط المحذوف وإرساله لي)', true],
      ['antidelete_include_media', 'إرسال وسائط الرسائل المحذوفة كاملة', true],
      ['antidelete_include_sender_info', 'إرفاق اسم ورقم المرسل مع المحذوف', true],
      ['antidelete_include_time', 'إرفاق وقت الحذف مع المحذوف', true],
      ['antidelete_status', 'مضاد حذف الحالات (تقاط الحالة المحذوفة وإرسالها لي)', true],
      ['antidelete_status_media', 'إرسال وسائط الحالة المحذوفة كاملة', true],
      ['antidelete_status_notify', 'إشعار صريح بصاحب الحالة المحذوفة', true],
      ['antidelete_chat_clear', 'مضاد حذف المحادثة كاملة', false],
      ['viewonce_reveal', 'كشف رسائل العرض لمرة واحدة', true],
      ['viewonce_reveal_media', 'إرسال الوسائط المكشوفة ضمن التقرير', true],
      ['viewonce_notify', 'إشعار صريح باسم ورقم مرسل العرض لمرة واحدة', true],
      ['viewonce_also_group', 'كشف العرض لمرة واحد في المجموعات أيضاً', true],
      ['antiedit_messages', 'مضاد تعديل الرسائل (تقاط المعدّل وإرساله لي)', false]
    ]
  },
  {
    key: 'messages', name: 'الرسائل والردود', icon: '✉️',
    features: [
      ['msg_welcome', 'رسالة ترحيب تلقائية', false],
      ['msg_auto_reply', 'الرد التلقائي على الرسائل', false],
      ['msg_auto_reply_text', 'نص الرد التلقائي قابل للتخصيص', true],
      ['msg_read_messages', 'تعليم رسائل المحادثات كمقروءة', true],
      ['msg_read_status', 'تعليم رسائل المحادثات للرقم نفسه كمقروءة', true],
      ['msg_typing_indicator', 'إظهار حالة (يكتب…) قبل الرد', true],
      ['msg_recording_indicator', 'إظهار حالة (يسجّل صوتاً) قبل الرد الصوتي', true],
      ['msg_delay_reply', 'تأخير بسيط بين الردود (طبيعي أكثر)', true],
      ['msg_forward_protection', 'منع إعادة توجيه رسائلي بلا ذكر المصدر', false],
      ['msg_reject_links_preview', 'تعطيل معاينة الروابط في رسائلي', false],
      ['msg_quote_reply', 'الرد مقتبساً الرسالة الأصلية دائماً', true],
      ['msg_send_seen_sound', 'إرسال إشارة السماع للرسائل الصوتية', true],
      ['msg_reaction_to_commands', 'إرسال تفاعل إيموجي عند تنفيذ أمر', true],
      ['msg_error_report', 'إبلاغ المرسل عند فشل تنفيذ أمر', true],
      ['msg_daily_greeting', 'تحية صباحية تلقائية لنفسي', false]
    ]
  },
  {
    key: 'privacy', name: 'الخصوصية والحضور', icon: '🕵️',
    features: [
      ['privacy_online_hide', 'إخفاء حالة الاتصال (يظهر آخر ظهور فقط)', true],
      ['privacy_typing_hide', 'عدم إظهار أنني أكتب أبداً', false],
      ['privacy_read_receipts_hide', 'عدم إرسال إيصالات قراءة (عين واحدة)', false],
      ['privacy_group_read_hide', 'عدم إرسال إيصالات القراءة في المجموعات', false],
      ['privacy_last_seen_mask', 'إخفاء آخر ظهور للجهات غير المحفوظة', false],
      ['privacy_profile_lock', 'قفل صورة الملف الشخصي', false],
      ['privacy_status_lock', 'إخفاء حالاتي من غير جهات الاتصال', false],
      ['privacy_call_reject', 'رفض المكالمات تلقائياً', false],
      ['privacy_call_reject_msg', 'إرسال رسالة لمن يتصل بعد رفض الاتصال', true],
      ['privacy_auto_block_stickers', 'حجب الملصقات من الغرباء', false],
      ['privacy_anti_spam_dm', 'حماية من التهام الرسائل المزعجة (Anti-Spam)', true],
      ['privacy_anti_spam_limit', 'حد الرسائل قبل اعتبارها إزعاجاً (10/دقيقة)', true],
      ['privacy_block_unknown_media', 'حجب الوسائط من أرقام غير محفوظة', false],
      ['privacy_self_chat_hide', 'إخفاء رسائل «الرسالة المرسلة لي» (Chat WA)', false]
    ]
  },
  {
    key: 'groups', name: 'إدارة المجموعات', icon: '👥',
    features: [
      ['groups_auto_accept', 'قبول تلقائي لطلبات الانضمام', false],
      ['groups_welcome_image', 'صورة ترحيب للعضو الجديد', false],
      ['groups_tag_all_admins', 'مناداة المشرفين عند الحاجة', false],
      ['groups_antibadwords', 'مضاد الألفاظ البذيئة', false],
      ['groups_auto_delete_links', 'حذف الروابط تلقائياً', false],
      ['groups_only_admin_post', 'تقييد النشر للمشرفين (إعلان مؤقت)', false],
      ['groups_auto_kick_spam', 'طرد المزعج تلقائياً', false],
      ['groups_welcome_message', 'رسالة ترحيب مخصّصة للعضو الجديد', true],
      ['groups_goodbye_message', 'رسالة وداع مخصّصة', true],
      ['groups_daily_backup', 'نسخة احتياطية يومية لأعضاء المجموعة', false],
      ['groups_auto_detect_toxic', 'كشف السلوك السام تلقائياً', false],
      ['groups_antiporn_media', 'حجب المحتوى غير اللائق تلقائياً', false],
      ['groups_max_warning', 'عدد التحذيرات قبل الطرد (3)', true]
    ]
  },
  {
    key: 'media', name: 'الوسائط والتحميل', icon: '📥',
    features: [
      ['media_auto_download', 'تنزيل الوسائط الواردة تلقائياً', false],
      ['media_max_size_guard', 'حد أقصى لحجم التحميل (حماية من الحظر)', true],
      ['media_ytdlp_enabled', 'تشغيل محرّك yt-dlp للتحميل', true],
      ['media_tiktok', 'التحميل من تيك توك', true],
      ['media_instagram', 'التحميل من إنستغرام', true],
      ['media_youtube', 'التحميل من يوتيوب', true],
      ['media_facebook', 'التحميل من فيسبوك', true],
      ['media_twitter_x', 'التحميل من إكس (تويتر سابقاً)', true],
      ['media_send_as_document', 'إرسال الوسائط كملف (بلا ضغط)', false],
      ['media_send_thumb', 'إرسال صورة مصغّرة مع الفيديو', true],
      ['media_convert_audio', 'تحويل الصوت لصيغة MP3 تلقائياً', true],
      ['media_compress_video', 'ضغط الفيديو إن تجاوز الحد الآمن', true],
      ['media_sticker_maker', 'صناعة الملصقات من الصور', true],
      ['media_tg_download', 'تحميل الوسائط من تيليجرام عبر البوت', true],
      ['media_auto_send_to_owner', 'إرسال الوسائط المُحمّلة لي مباشرة', true]
    ]
  },
  {
    key: 'security', name: 'الأمان والحماية', icon: '🔐',
    features: [
      ['sec_anti_hack', 'حماية من محاولات الاختراق', true],
      ['sec_anti_crash', 'حماية من أخطاء الجلسة (Anti-Crash)', true],
      ['sec_session_lock', 'قفل الجلسة بلا إعادة اتصال تلقائي', false],
      ['sec_strict_owners', 'تقييد أوامر المالك على رقم صاحب البوت فقط', true],
      ['sec_log_all_messages', 'تسجيل كل الرسائل في السجل (خصوصية أقل)', false],
      ['sec_anti_call_bomb', 'حماية من اتصالات الإزعاج المتكررة', true],
      ['sec_notify_suspicious', 'إشعاري عند أي نشاط مشبوه', true],
      ['sec_anti_bulk_msg', 'حماية من الإذاعات الواردة المزعجة', true],
      ['sec_auto_reconnect', 'إعادة الاتصال التلقائي عند الانقطاع', true],
      ['sec_backup_before_update', 'نسخة احتياطية قبل أي تحديث', true],
      ['sec_encrypt_local_data', 'تشفير بيانات الجلسة على القرص', false],
      ['sec_two_step_verify', 'تفعيل التحقق بخطوتين على واتساب', false],
      ['sec_login_alerts', 'تنبيه عند دخول جهاز جديد', true],
      ['sec_anti_export', 'منع تصدير بيانات المحادثات من الهاتف', false]
    ]
  },
  {
    key: 'notifications', name: 'الإشعارات', icon: '🔔',
    features: [
      ['notify_new_link', 'إشعار عند ربط رقم جديد', true],
      ['notify_disconnect', 'إشعار عند انقطاع الجلسة', true],
      ['notify_message_deleted', 'إشعار عند حذف رسالة لي', true],
      ['notify_status_reaction', 'إشعار عند تفاعل أحد مع حالتي', false],
      ['notify_bulk_done', 'إشعار بانتهاء الإذاعة', true],
      ['notify_download_done', 'إشعار بانتهاء التحميل', true],
      ['notify_daily_summary', 'ملخص يومي بالنشاط', false],
      ['notify_new_follower', 'إشعار بانضمام عضو جديد لقناة واتساب', false],
      ['notify_login_telegram', 'إشعار تيليجرام عند أي حدث مهم', true],
      ['notify_silent_mode', 'إرسال الإشعارات بصمت (بلا صوت)', false],
      ['notify_only_working_hours', 'الإشعارات في ساعات العمل فقط', false],
      ['notify_group_mentions', 'إشعار عند ذكري في مجموعة', true],
      ['notify_backup_done', 'إشعار عند اكتمال النسخ الاحتياطي', true],
      ['notify_error_alerts', 'إشعار فوري بأي خطأ حرج', true],
      ['notify_anti_delete_capture', 'إشعار بتقاط رسالة محذوفة', true]
    ]
  },
  {
    key: 'automation', name: 'الأتمتة والذكاء', icon: '🤖',
    features: [
      ['auto_reply_ai', 'الرد الذكي بالذكاء الاصطناعي', false],
      ['auto_schedule_msg', 'جدولة الرسائل (إرسال مؤجّل)', true],
      ['auto_wa_channel_follow', 'الانضمام التلقائي لقناة واتساب الرسمية', true],
      ['auto_daily_emoji_change', 'تغيير إيموجي التفاعل يومياً عشوائياً', false],
      ['auto_status_repost', 'إعادة نشر حالات جميلة (اختياري)', false],
      ['auto_clean_tmp', 'تنظيف الملفات المؤقتة تلقائياً', true],
      ['auto_heartbeat_backup', 'نسخ احتياطي دوري تلقائي', true],
      ['auto_update_ytdlp', 'تحديث yt-dlp تلقائياً', true],
      ['auto_night_mode', 'وضع ليلي: إيقاف التفاعل ليلاً', false],
      ['auto_working_hours', 'تحديد ساعات عمل للتفاعل', false],
      ['auto_forward_to_tg', 'تمرير رسائل واتساب مهمة لتيليجرام', false],
      ['auto_translator', 'ترجمة الرسائل الواردة تلقائياً', false],
      ['auto_voice_to_text', 'تحويل الرسائل الصوتية لنص', false],
      ['auto_text_to_voice', 'تحويل النص لرسالة صوتية عند الطلب', false],
      ['auto_smart_delay', 'تأخير ذكي بين الأوامر (يقلّل الحظر)', true],
      ['auto_backup_daily', 'نسخة احتياطية يومية تلقائية', true],
      ['auto_restart_on_error', 'إعادة تشغيل الجلسة عند الخطأ الحرج', true],
      ['auto_chat_backup', 'نسخ المحادثات المحلية يومياً', false],
      ['auto_anti_revoke_status', 'تقاط الحالات المحذوفة (اختصار سريع)', false],
      ['auto_notify_owner_busy', 'رد «أنا مشغول» تلقائياً عند الاتصال', false]
    ]
  },
  {
    key: 'advanced', name: 'خيارات متقدّمة', icon: '⚙️',
    features: [
      ['adv_debug_mode', 'وضع التصحيح (سجلات تفصيلية)', false],
      ['adv_raw_events_log', 'تسجيل أحداث Baileys الخام', false],
      ['adv_bypass_rate_limit', 'تجاهل حدود المعدل (خطر حظر أعلى)', false],
      ['adv_force_legacy_protocol', 'فرض بروتوكول قديم للاتصال', false],
      ['adv_disable_reconnect_backoff', 'إلغاء التأخير التدريجي في إعادة الاتصال', false],
      ['adv_use_lid_jids', 'استخدام معرّفات LID الجديدة', false],
      ['adv_full_history_sync', 'مزامنة تاريخ المحادثات بالكامل', false],
      ['adv_ignore_broadcast_dnd', 'تجاهل رسائل البث الجماعي', true],
      ['adv_manual_presence', 'تحكّم يدوي بحالة الحضور', false],
      ['adv_cache_media_off', 'تعطيل كاش الوسائط', false],
      ['adv_multi_device_strict', 'وضع الأجهزة المتعددة الصارم', false],
      ['adv_send_read_receipts_owner', 'إرسال إيصالات قراءة لرسائل المالك', true],
      ['adv_disable_media_reupload', 'تعطيل إعادة رفع الوسائط الفاسدة', false],
      ['adv_extra_slow_mode', 'وضع بطيء إضافي (أقصى حماية من الحظر)', false],
      ['adv_skip_server_version_check', 'تجاوز فحص إصدار السيرفر', false],
      ['adv_log_to_file', 'كتابة السجل في ملف منفصل', true],
      ['adv_emoji_fallback_set', 'استخدام مجموعة إيموجي بديلة عند الفشل', true],
      ['adv_preserve_session_files', 'الحفاظ على ملفات الجلسة عند قطع الربط', false],
      ['adv_allow_remote_debug', 'السماح بتصحيح عن بُعد (غير آمن)', false],
      ['adv_experimental_features', 'تشغيل الميزات التجريبية', false]
    ]
  }
];

/** كل الخيارات كسطح مستوٍ: { key: { name, group, def } } */
const FLAT = {};
for (const g of FEATURE_GROUPS) {
  for (const [key, name, def] of g.features) {
    FLAT[key] = { name, group: g.key, groupName: g.name, def: !!def };
  }
}

export function allFeatureKeys() { return Object.keys(FLAT); }
export function featureMeta(key) { return FLAT[key] || null; }
export function featureGroups() { return FEATURE_GROUPS; }
export function totalFeaturesCount() { return Object.keys(FLAT).length; }

const digitsOf = (phone) => String(phone || '').replace(/\D/g, '');

/** إعدادات رقم معيّن (مدموجة مع الافتراضيات) */
export function getPhoneFeatures(phone) {
  const phones = featuresStore.get('phones') || {};
  const saved = phones[digitsOf(phone)] || {};
  const merged = {};
  for (const [key, meta] of Object.entries(FLAT)) {
    merged[key] = typeof saved[key] === 'boolean' ? saved[key] : meta.def;
  }
  merged._updatedAt = saved._updatedAt || 0;
  return merged;
}

/** قراءة خيار واحد لرقم — الدالة التي تستعلم منها الأوامر الداخلية */
export function isEnabled(phone, key) {
  const meta = FLAT[key];
  const phones = featuresStore.get('phones') || {};
  const saved = phones[digitsOf(phone)] || {};
  if (typeof saved[key] === 'boolean') return saved[key];
  return meta ? meta.def : true;
}

/** تعيين خيار واحد لرقم + تطبيق فوري عبر المزامنة */
export async function setPhoneFeature(phone, key, value) {
  const meta = FLAT[key];
  if (!meta) return { ok: false, error: `خيار غير معروف: ${key}` };
  const phones = { ...(featuresStore.get('phones') || {}) };
  const cur = phones[digitsOf(phone)] || {};
  phones[digitsOf(phone)] = { ...cur, [key]: !!value, _updatedAt: Date.now() };
  featuresStore.setSync('phones', phones); // فوري على القرص — لا سباق كتابة
  logger.info({ phone, key, value }, 'تغيير خيار تحكم من لوحة التحكم');
  return { ok: true, key, value: !!value, features: getPhoneFeatures(phone) };
}

/** تعيين مجموعة خيارات دفعة واحدة (patch) */
export function patchPhoneFeatures(phone, patch = {}) {
  const phones = { ...(featuresStore.get('phones') || {}) };
  const cur = phones[digitsOf(phone)] || {};
  const clean = {};
  for (const [k, v] of Object.entries(patch)) {
    if (FLAT[k]) clean[k] = !!v;
  }
  phones[digitsOf(phone)] = { ...cur, ...clean, _updatedAt: Date.now() };
  featuresStore.setSync('phones', phones); // فوري على القرص
  return { ok: true, applied: Object.keys(clean).length, features: getPhoneFeatures(phone) };
}

/** حذف إعدادات رقم (عند فك الربط) */
export function dropPhoneFeatures(phone) {
  const phones = { ...(featuresStore.get('phones') || {}) };
  delete phones[digitsOf(phone)];
  featuresStore.setSync('phones', phones); // فوري على القرص
  return true;
}

/** ملخص عددي لكل الأرقام (للوحة) */
export function featuresSummary() {
  const phones = featuresStore.get('phones') || {};
  return {
    phonesConfigured: Object.keys(phones).length,
    totalKeys: Object.keys(FLAT).length,
    groups: FEATURE_GROUPS.map((g) => ({ key: g.key, name: g.name, icon: g.icon, count: g.features.length }))
  };
}
