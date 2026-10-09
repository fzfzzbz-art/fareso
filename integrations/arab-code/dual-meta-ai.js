// مقتطف relayMessage مستقل وليس أمراً قابلاً للتشغيل وحده.
export default async function dualMetaAiStub() {
  throw new Error('هذا المقتطف يحتاج سياق conn وm من مصدره الأصلي.');
}
