<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import { LockKeyhole } from "lucide-vue-next"
import { t } from "@/lib/i18n"
import { session, signIn } from "@/stores/session"

const logoUrl = "/assets/losand/images/losand-logo.jpg"
const router = useRouter()
const username = ref("")
const password = ref("")

async function submit() {
  await signIn(username.value, password.value)
  router.replace("/home")
}
</script>

<template>
  <section class="grid min-h-screen bg-white lg:grid-cols-[1fr_0.9fr]">
    <div class="flex items-center justify-center px-6 py-10">
      <form class="w-full max-w-md" @submit.prevent="submit">
        <div class="mb-8 flex items-center gap-3">
          <img :src="logoUrl" alt="Los Andalos" class="h-14 w-14 rounded-xl bg-white object-contain ring-1 ring-manufacture-line" />
          <div>
            <h1 class="text-2xl font-bold">{{ t("Los Andalus Manufacture") }}</h1>
            <p class="text-sm text-manufacture-muted">{{ t("Login") }}</p>
          </div>
        </div>
        <label class="mb-4 block">
          <span class="mb-2 block text-sm font-semibold">{{ t("Email or username") }}</span>
          <input v-model="username" autocomplete="username" class="w-full rounded-xl border border-manufacture-line px-4 py-3 outline-none focus:border-manufacture-green" />
        </label>
        <label class="mb-5 block">
          <span class="mb-2 block text-sm font-semibold">{{ t("Password") }}</span>
          <input v-model="password" type="password" autocomplete="current-password" class="w-full rounded-xl border border-manufacture-line px-4 py-3 outline-none focus:border-manufacture-green" />
        </label>
        <p v-if="session.error" class="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-manufacture-red">{{ session.error }}</p>
        <button class="flex w-full items-center justify-center gap-2 rounded-xl bg-manufacture-green px-4 py-3 font-bold text-white shadow-sm hover:bg-manufacture-greenDark" :disabled="session.loading">
          <LockKeyhole class="h-4 w-4" />
          {{ session.loading ? t("Login") : t("Sign in") }}
        </button>
      </form>
    </div>
    <div class="hidden bg-[radial-gradient(circle_at_top,#dcfce7,#f8fafc_45%,#ffffff)] p-10 lg:block">
      <div class="flex h-full flex-col items-center justify-center rounded-2xl border border-manufacture-line bg-white/70 p-8 text-center">
        <img :src="logoUrl" alt="Los Andalos" class="mb-8 w-56 max-w-full object-contain" />
        <p class="text-sm font-semibold text-manufacture-green">{{ t("Food Logger") }}</p>
        <h2 class="mt-3 text-4xl font-bold leading-tight">{{ t("Manufacture Home") }}</h2>
      </div>
    </div>
  </section>
</template>
