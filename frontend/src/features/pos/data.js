// Static mock data for the POS portal (visual build — wired to ERPNext later).
// Currency label matches the mockups (د.ل).

export const CURRENCY = "د.ل"
export const BRANCH = "فرع وسط المدينة"

// Digits are rendered with normal (Western) numerals.
export function ar(value) {
  return String(value)
}

export function money(value) {
  const n = Number(value)
  return `${ar(n.toFixed(2))} ${CURRENCY}`
}

// ---- Register: menu categories + products ----
export const CATEGORIES = [
  { key: "all", label: "الكل", icon: "fa-utensils" },
  { key: "burgers", label: "برجر", icon: "fa-burger" },
  { key: "pizza", label: "بيتزا", icon: "fa-pizza-slice" },
  { key: "grill", label: "مشويات", icon: "fa-fire" },
  { key: "salads", label: "سلطات", icon: "fa-leaf" },
  { key: "drinks", label: "مشروبات", icon: "fa-mug-hot" },
]

export const PRODUCTS = [
  { id: "P1", name: "برجر كلاسيك", category: "burgers", price: 12.5, img: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&q=70" },
  { id: "P2", name: "برجر دجاج مقرمش", category: "burgers", price: 13.0, img: "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=400&q=70" },
  { id: "P3", name: "بيتزا مارغريتا", category: "pizza", price: 22.0, img: "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400&q=70" },
  { id: "P4", name: "بيتزا خضار", category: "pizza", price: 20.0, img: "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&q=70" },
  { id: "P5", name: "دجاج مشوي", category: "grill", price: 15.0, img: "https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400&q=70" },
  { id: "P6", name: "كفتة مشوية", category: "grill", price: 18.0, img: "https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&q=70" },
  { id: "P7", name: "ستيك لحم", category: "grill", price: 35.0, img: "https://images.unsplash.com/photo-1546964124-0cce460f38ef?w=400&q=70" },
  { id: "P8", name: "سلطة سيزر", category: "salads", price: 9.0, img: "https://images.unsplash.com/photo-1550304943-4f24f54ddde9?w=400&q=70" },
  { id: "P9", name: "سلطة خضار", category: "salads", price: 7.5, img: "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&q=70" },
  { id: "P10", name: "عصير برتقال", category: "drinks", price: 8.0, img: "https://images.unsplash.com/photo-1613478223719-2ab802602423?w=400&q=70" },
  { id: "P11", name: "ليموناضة", category: "drinks", price: 6.0, img: "https://images.unsplash.com/photo-1621263764928-df1444c5e859?w=400&q=70" },
  { id: "P12", name: "قهوة عربية", category: "drinks", price: 5.0, img: "https://images.unsplash.com/photo-1442512595331-e89e73853f31?w=400&q=70" },
]

// ---- Orders: kanban board ----
export const ORDER_COLUMNS = [
  { key: "new", label: "جديدة", dot: "bg-pos-brand", badge: "pos-badge-new", accent: "pos-col-new" },
  { key: "prep", label: "قيد التحضير", dot: "bg-pos-amber", badge: "pos-badge-prep", accent: "pos-col-prep" },
  { key: "ready", label: "جاهزة", dot: "bg-pos-green", badge: "pos-badge-ready", accent: "pos-col-ready" },
  { key: "done", label: "تم التسليم", dot: "bg-pos-muted", badge: "pos-badge-done", accent: "pos-col-done" },
]

const TYPE_META = {
  dine: { label: "داخلي", icon: "fa-hashtag", chip: "pos-type-dine" },
  take: { label: "تيك أواي", icon: "fa-bag-shopping", chip: "pos-type-take" },
  delivery: { label: "توصيل", icon: "fa-motorcycle", chip: "pos-type-delivery" },
}
export const orderType = (k) => TYPE_META[k] || TYPE_META.dine

export const ORDERS = [
  { id: "0247", col: "new", type: "dine", where: "طاولة 3", mins: 2, time: "fresh", note: "بدون بصل في البرجر",
    items: [{ q: 2, name: "برجر كلاسيك", price: 25 }, { q: 1, name: "بيتزا مارغريتا", price: 22 }, { q: 2, name: "عصير برتقال", price: 16 }] },
  { id: "0246", col: "new", type: "take", where: "استلام ذاتي", mins: 4, time: "fresh",
    items: [{ q: 1, name: "شاورما لحم", price: 10.5 }, { q: 1, name: "كولا كبيرة", price: 5 }] },
  { id: "0245", col: "new", type: "delivery", where: "توصيل", mins: 8, time: "warn",
    items: [{ q: 3, name: "كفتة مشوية", price: 54 }, { q: 1, name: "خبز بيتا", price: 3 }, { q: 2, name: "ليموناضة", price: 12 }] },
  { id: "0243", col: "prep", type: "dine", where: "طاولة 5", mins: 10, time: "warn", progress: 60,
    items: [{ q: 2, name: "برجر كلاسيك", price: 25, done: true }, { q: 1, name: "دجاج مشوي", price: 15, cooking: true }, { q: 2, name: "بطاطس مقلية", price: 10 }] },
  { id: "0242", col: "prep", type: "take", where: "استلام ذاتي", mins: 18, time: "late", progress: 30, late: true,
    items: [{ q: 2, name: "فطيرة جبن", price: 16 }, { q: 3, name: "عصير تفاح", price: 18 }] },
  { id: "0240", col: "ready", type: "dine", where: "طاولة 1", mins: 22, time: "late", hint: "جاهز للتسليم — ينتظر النادل",
    items: [{ q: 2, name: "بيتزا مارغريتا", price: 44 }, { q: 1, name: "سلطة سيزر", price: 9 }, { q: 2, name: "مياه معدنية", price: 4 }] },
  { id: "0239", col: "ready", type: "take", where: "استلام ذاتي", mins: 15, time: "fresh", hint: "جاهز للاستلام",
    items: [{ q: 1, name: "شاورما دجاج", price: 11 }, { q: 1, name: "عصير مشكل", price: 7 }] },
  { id: "0237", col: "done", type: "dine", where: "طاولة 7", mins: 35, paid: true,
    items: [{ q: 1, name: "ستيك لحم", price: 35 }, { q: 2, name: "بطاطس مقلية", price: 10 }, { q: 2, name: "كولا", price: 10 }] },
  { id: "0236", col: "done", type: "take", where: "استلام ذاتي", mins: 42, paid: true,
    items: [{ q: 3, name: "فطيرة جبن", price: 24 }, { q: 2, name: "قهوة عربية", price: 8 }] },
]

export const orderTotal = (o) => o.items.reduce((s, it) => s + it.price, 0)

// ---- Inventory ----
const STATUS_META = {
  instock: { label: "متوفر", icon: "fa-circle-check", badge: "pos-badge-instock", row: "pos-row-ok", qty: "pos-qty-ok", bar: "bg-pos-green" },
  lowstock: { label: "منخفض", icon: "fa-triangle-exclamation", badge: "pos-badge-lowstock", row: "pos-row-low", qty: "pos-qty-low", bar: "bg-pos-orange" },
  outstock: { label: "نفد", icon: "fa-circle-xmark", badge: "pos-badge-outstock", row: "pos-row-out", qty: "pos-qty-out", bar: "bg-pos-danger" },
}
export const stockStatus = (k) => STATUS_META[k] || STATUS_META.instock

const CAT_META = {
  meat: { label: "لحوم", pill: "pos-cat-meat" },
  veg: { label: "خضروات", pill: "pos-cat-veg" },
  dairy: { label: "ألبان وبيض", pill: "pos-cat-dairy" },
  bev: { label: "مشروبات", pill: "pos-cat-bev" },
  dry: { label: "جافة", pill: "pos-cat-dry" },
  bakery: { label: "مخبوزات", pill: "pos-cat-bakery" },
}
export const itemCat = (k) => CAT_META[k] || CAT_META.dry

export const INVENTORY = [
  { name: "لحم بقري مفروم", sku: "MTB-001", cat: "meat", icon: "fa-drumstick-bite", status: "lowstock", qty: 2.5, max: 14, unit: "كيلوغرام", unitShort: "كجم" },
  { name: "بيض طازج", sku: "DRY-021", cat: "dairy", icon: "fa-egg", status: "outstock", qty: 0, max: 120, unit: "حبة", unitShort: "حبة" },
  { name: "طماطم طازجة", sku: "VEG-005", cat: "veg", icon: "fa-carrot", status: "instock", qty: 18, max: 25, unit: "كيلوغرام", unitShort: "كجم" },
  { name: "دقيق أبيض", sku: "DRY-003", cat: "dry", icon: "fa-wheat-awn", status: "instock", qty: 35, max: 40, unit: "كيلوغرام", unitShort: "كجم" },
  { name: "جبن موزاريلا", sku: "DRY-011", cat: "dairy", icon: "fa-cheese", status: "lowstock", qty: 1.2, max: 10, unit: "كيلوغرام", unitShort: "كجم" },
  { name: "زيت زيتون", sku: "DRY-008", cat: "dry", icon: "fa-droplet", status: "outstock", qty: 0, max: 8, unit: "لتر", unitShort: "لتر" },
  { name: "قهوة عربية", sku: "BEV-002", cat: "bev", icon: "fa-mug-hot", status: "instock", qty: 4.5, max: 7.5, unit: "كيلوغرام", unitShort: "كجم" },
  { name: "خبز عربي", sku: "BAK-001", cat: "bakery", icon: "fa-bread-slice", status: "lowstock", qty: 12, max: 60, unit: "رغيف", unitShort: "رغيف" },
  { name: "مياه معدنية 0.5 لتر", sku: "BEV-010", cat: "bev", icon: "fa-bottle-water", status: "instock", qty: 96, max: 120, unit: "علبة", unitShort: "علبة" },
  { name: "سمك مقلي مجمد", sku: "MTB-007", cat: "meat", icon: "fa-fish", status: "outstock", qty: 0, max: 12, unit: "كيلوغرام", unitShort: "كجم" },
  { name: "بهارات مشكلة", sku: "DRY-015", cat: "dry", icon: "fa-pepper-hot", status: "instock", qty: 3.8, max: 5, unit: "كيلوغرام", unitShort: "كجم" },
]
