<script setup>
import { useRouter } from "vue-router"
import { ClipboardList, LogOut } from "lucide-vue-next"
import { t } from "@/lib/i18n"
import { session, signOut } from "@/stores/session"

const router = useRouter()

async function logout() {
  await signOut()
  router.replace("/login")
}
</script>

<template>
  <section class="mx-auto min-h-screen max-w-5xl px-5 py-6">
    <header class="mb-8 flex items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-extrabold">{{ t("Manufacture Home") }}</h1>
        <p class="mt-1 text-sm text-manufacture-muted">{{ session.user }}</p>
      </div>
      <button class="flex items-center gap-2 rounded-xl border border-manufacture-line bg-white px-4 py-2 text-sm font-semibold" @click="logout">
        <LogOut class="h-4 w-4" />
        {{ t("Logout") }}
      </button>
    </header>
    <button class="grid w-full gap-4 rounded-2xl border border-manufacture-line bg-white p-6 text-start shadow-sm hover:border-manufacture-green" @click="router.push('/food-logger/new')">
      <div class="grid h-12 w-12 place-items-center rounded-xl bg-green-50 text-manufacture-green">
        <ClipboardList class="h-6 w-6" />
      </div>
      <div>
        <h2 class="text-xl font-bold">{{ t("Food Logger") }}</h2>
        <p class="mt-1 text-sm text-manufacture-muted">{{ t("Record production batches, materials, waste, loss, and final cost.") }}</p>
      </div>
    </button>
  </section>
</template>
