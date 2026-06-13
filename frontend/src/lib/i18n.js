import { computed, ref } from "vue"

export const currentLanguage = ref(window.boot?.lang || "ar")

const localTranslations = {
  ar: {
    "Los Andalus Manufacture": "تصنيع الأندلس",
    "Manufacture Home": "الرئيسية",
    "Food Logger": "تسجيل الإنتاج",
    "Login": "تسجيل الدخول",
    "Manufacture": "التصنيع",
    "Welcome back": "مرحباً بعودتك",
    "Secure manufacturing workspace": "مساحة تصنيع آمنة لتسجيل الإنتاج ومراجعة التكاليف.",
    "Email or username": "البريد الإلكتروني أو اسم المستخدم",
    Password: "كلمة المرور",
    "Sign in": "دخول",
    "Signing in": "جارٍ تسجيل الدخول",
    "Checking credentials": "جارٍ التحقق من بيانات الدخول...",
    Logout: "تسجيل الخروج",
    Batch: "الدفعات",
    Cost: "التكلفة",
    Quality: "الجودة",
    "Production control": "مراقبة الإنتاج",
    "Track batches, materials, waste, and final cost from one focused workspace.": "تابع الدفعات والمواد والهالك والتكلفة النهائية من مساحة عمل مركزة واحدة.",
    "Record production batches, materials, waste, loss, and final cost.": "سجّل دفعات الإنتاج والمواد والهالك والفاقد والتكلفة النهائية.",
    "Raw Materials": "المواد الخام",
    "Production Output": "ناتج الإنتاج",
    "Notes": "ملاحظات",
    "Continue": "متابعة",
    "Production Summary": "ملخص الإنتاج",
    "Quantity": "الكمية",
    "Unit Cost": "تكلفة الوحدة",
    "Total Cost": "التكلفة الإجمالية",
    "I confirm this production batch is accurate.": "أؤكد أن بيانات دفعة الإنتاج صحيحة.",
    "Save Batch": "حفظ الدفعة",
    "Batch Saved": "تم حفظ الدفعة",
    "Start New Batch": "بدء دفعة جديدة",
  },
}

export const direction = computed(() => (currentLanguage.value === "ar" ? "rtl" : "ltr"))

export function setLanguage(language) {
  currentLanguage.value = language
  document.documentElement.lang = language
  document.documentElement.dir = language === "ar" ? "rtl" : "ltr"
}

export function t(source) {
  if (window.__ && typeof window.__ === "function") {
    return window.__(source)
  }
  return localTranslations[currentLanguage.value]?.[source] || source
}
