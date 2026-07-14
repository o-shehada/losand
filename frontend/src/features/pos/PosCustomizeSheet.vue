<script setup>
import { ref, computed } from "vue"
import { NOTES } from "./data"
import { pos } from "@/stores/pos"

const EXTRAS = computed(() => pos.extras)
const money = (value) =>
  `${Number(value || 0).toFixed(2)} ${pos.config?.currency_symbol || pos.config?.currency || "د.ل"}`

// One sheet, parameterized by title + the piece being edited. Used both for
// "customize the whole line" (all pieces at once) and "customize piece N" —
// the parent decides what to do with the emitted result.
const props = defineProps({
  title: { type: String, required: true },
  extras: { type: Array, default: () => [] }, // seed: selected extra objects
  notes: { type: Array, default: () => [] }, // seed: selected note strings
})
const emit = defineEmits(["done", "close"])

// Local draft — nothing leaves until "تم".
const selExtras = ref(props.extras.map((e) => e.id))
const selNotes = ref([...props.notes])
const customNote = ref("")

const hasExtra = (id) => selExtras.value.includes(id)
function toggleExtra(id) {
  selExtras.value = hasExtra(id) ? selExtras.value.filter((x) => x !== id) : [...selExtras.value, id]
}
const hasNote = (n) => selNotes.value.includes(n)
function toggleNote(n) {
  selNotes.value = hasNote(n) ? selNotes.value.filter((x) => x !== n) : [...selNotes.value, n]
}
function addCustomNote() {
  const n = customNote.value.trim()
  if (n && !hasNote(n)) selNotes.value.push(n)
  customNote.value = ""
}

function done() {
  emit("done", {
    extras: EXTRAS.value.filter((e) => selExtras.value.includes(e.id)),
    notes: [...selNotes.value],
  })
}
</script>

<template>
  <div
    class="fixed inset-0 bg-black/50 z-50 flex items-end justify-center"
    style="backdrop-filter: blur(4px)"
    @click.self="emit('close')"
  >
    <div class="pos-modal bg-pos-surface rounded-t-2xl shadow-2xl border border-pos-border w-full max-w-md p-6 max-h-[85dvh] overflow-y-auto">
      <!-- header -->
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-extrabold text-gray-800 text-base flex items-center gap-2">
          <i class="fa-solid fa-pen text-pos-brand text-sm"></i> {{ title }}
        </h3>
        <button
          @click="emit('close')"
          class="w-8 h-8 bg-pos-canvas border border-pos-border rounded-lg flex items-center justify-center text-pos-muted hover:text-pos-danger hover:border-pos-danger transition-colors"
        >
          <i class="fa-solid fa-xmark text-sm"></i>
        </button>
      </div>

      <!-- paid add-ons -->
      <p class="text-sm font-extrabold text-gray-700 mb-2 pr-2 border-r-4 border-pos-amber">إضافات مدفوعة</p>
      <div class="flex flex-wrap gap-2 mb-5">
        <button
          v-for="e in EXTRAS"
          :key="e.id"
          @click="toggleExtra(e.id)"
          class="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold border transition-colors min-h-[40px]"
          :class="hasExtra(e.id) ? 'border-pos-brand bg-pos-brand-light text-pos-brand-dark' : 'border-pos-border bg-pos-canvas text-gray-600 hover:border-pos-brand'"
        >
          <i class="fa-solid text-[10px]" :class="hasExtra(e.id) ? 'fa-check text-pos-brand' : 'fa-plus text-pos-muted'"></i>
          <span>{{ e.name }}</span>
          <span class="text-pos-amber font-extrabold">+{{ money(e.price) }}</span>
        </button>
      </div>

      <!-- free notes -->
      <p class="text-sm font-extrabold text-gray-700 mb-2 pr-2 border-r-4 border-pos-brand">ملاحظات مجانية</p>
      <div class="flex flex-wrap gap-2 mb-3">
        <button
          v-for="n in NOTES"
          :key="n"
          @click="toggleNote(n)"
          class="px-3 py-2 rounded-full text-xs font-bold border transition-colors min-h-[40px]"
          :class="hasNote(n) ? 'bg-pos-brand border-pos-brand text-white' : 'border-pos-border bg-pos-canvas text-gray-600 hover:border-pos-brand'"
        >
          {{ n }}
        </button>
      </div>

      <!-- custom note -->
      <div class="flex items-center gap-2 mb-6">
        <button
          @click="addCustomNote"
          class="w-9 h-9 flex-shrink-0 bg-pos-brand text-white rounded-full flex items-center justify-center hover:bg-pos-brand-dark transition-colors"
        >
          <i class="fa-solid fa-plus text-sm"></i>
        </button>
        <input
          v-model="customNote"
          @keyup.enter="addCustomNote"
          type="text"
          placeholder="ملاحظة..."
          class="flex-1 bg-pos-canvas border border-pos-border rounded-xl px-4 py-2 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[40px]"
        />
      </div>

      <!-- done -->
      <button
        @click="done"
        class="w-full bg-pos-brand text-white font-extrabold text-sm py-3 rounded-xl min-h-[48px] hover:bg-pos-brand-dark transition-colors shadow-md shadow-pos-brand/25"
      >
        تم
      </button>
    </div>
  </div>
</template>
