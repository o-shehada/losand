<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import { LockKeyhole } from "lucide-vue-next"
import { t } from "@/lib/i18n"
import { session, signIn } from "@/stores/session"

const logoUrl = "/assets/losand/images/losand-logo.jpg"
const wallpaperUrl = "/assets/losand/images/losand-wallpaper.png"
const router = useRouter()
const username = ref("")
const password = ref("")

async function submit() {
  await signIn(username.value, password.value)
  router.replace("/home")
}
</script>

<template>
  <section class="min-h-screen bg-[#f5f0eb] text-[#211b16] lg:grid lg:grid-cols-[minmax(520px,0.92fr)_1.08fr]">
    <div class="relative flex min-h-screen items-center justify-center overflow-hidden px-5 py-8 sm:px-8 lg:px-12">
      <div class="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-[#e8490f] via-[#f0b429] to-[#12946b]"></div>
      <div class="pointer-events-none absolute -top-24 end-[-140px] h-80 w-80 rounded-full border border-[#e8d8cd]"></div>
      <div class="pointer-events-none absolute bottom-[-170px] start-[-150px] h-96 w-96 rounded-full border border-[#ead9cd]"></div>

      <form class="relative w-full max-w-[460px] rounded-[28px] border border-[#eaded6] bg-white/95 p-6 shadow-[0_24px_80px_rgba(63,40,24,0.14)] backdrop-blur sm:p-8" :aria-busy="session.loading" @submit.prevent="submit">
        <div v-if="session.loading" class="pointer-events-none absolute inset-0 z-10 rounded-[28px] border border-[#e8490f]/10 bg-white/45 backdrop-blur-[1px]"></div>

        <div class="mb-8 flex items-center gap-4">
          <img :src="logoUrl" alt="Los Andalos" class="h-16 w-16 rounded-2xl bg-[#16120f] object-contain p-1.5 shadow-sm ring-1 ring-[#eaded6]" />
          <div>
            <p class="text-xs font-extrabold uppercase tracking-[0.22em] text-[#e8490f]">{{ t("Los Andalus") }}</p>
            <h1 class="mt-1 text-2xl font-extrabold leading-tight text-[#211b16]">{{ t("Operations Portal") }}</h1>
          </div>
        </div>

        <div class="mb-7">
          <h2 class="text-3xl font-extrabold leading-tight text-[#211b16]">{{ t("Welcome back") }}</h2>
          <p class="mt-2 text-sm leading-6 text-[#7a6558]">{{ t("Sign in to continue") }}</p>
        </div>

        <label class="mb-4 block">
          <span class="mb-2 block text-sm font-bold text-[#4c4038]">{{ t("Email or username") }}</span>
          <input v-model="username" autocomplete="username" class="min-h-[52px] w-full rounded-2xl border border-[#e4d7cd] bg-[#fffaf6] px-4 py-3 text-[#211b16] shadow-inner shadow-[#e7d9cf]/30 outline-none transition focus:border-[#e8490f] focus:bg-white focus:ring-4 focus:ring-[#e8490f]/10 disabled:cursor-wait disabled:opacity-70" :disabled="session.loading" />
        </label>
        <label class="mb-5 block">
          <span class="mb-2 block text-sm font-bold text-[#4c4038]">{{ t("Password") }}</span>
          <input v-model="password" type="password" autocomplete="current-password" class="min-h-[52px] w-full rounded-2xl border border-[#e4d7cd] bg-[#fffaf6] px-4 py-3 text-[#211b16] shadow-inner shadow-[#e7d9cf]/30 outline-none transition focus:border-[#e8490f] focus:bg-white focus:ring-4 focus:ring-[#e8490f]/10 disabled:cursor-wait disabled:opacity-70" :disabled="session.loading" />
        </label>
        <p v-if="session.error" class="mb-4 rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm font-semibold text-manufacture-red">{{ session.error }}</p>
        <button class="relative z-20 flex min-h-[52px] w-full items-center justify-center gap-2 rounded-2xl bg-[#e8490f] px-4 py-3 text-base font-extrabold text-white shadow-[0_14px_34px_rgba(232,73,15,0.28)] transition hover:bg-[#c73d0c] focus:outline-none focus:ring-4 focus:ring-[#e8490f]/20 disabled:cursor-wait disabled:bg-[#c73d0c] disabled:opacity-95" :disabled="session.loading">
          <span v-if="session.loading" class="h-5 w-5 animate-spin rounded-full border-2 border-white/35 border-t-white"></span>
          <LockKeyhole v-else class="h-4 w-4" />
          {{ session.loading ? t("Signing in") : t("Sign in") }}
        </button>
        <p v-if="session.loading" class="relative z-20 mt-3 text-center text-xs font-bold text-[#e8490f]">{{ t("Checking credentials") }}</p>

        <div class="mt-6 grid grid-cols-3 gap-2 text-center text-[11px] font-bold text-[#7a6558]">
          <div class="rounded-xl bg-[#f7eee7] px-2 py-2">{{ t("POS") }}</div>
          <div class="rounded-xl bg-[#f7eee7] px-2 py-2">{{ t("Production") }}</div>
          <div class="rounded-xl bg-[#f7eee7] px-2 py-2">{{ t("Reports") }}</div>
        </div>
      </form>
    </div>

    <div class="relative hidden min-h-screen overflow-hidden bg-[#17120f] p-8 lg:block">
      <img :src="wallpaperUrl" alt="" class="absolute inset-0 h-full w-full object-cover opacity-70" />
      <div class="absolute inset-0 bg-gradient-to-br from-black/20 via-[#241107]/55 to-[#e8490f]/35"></div>
      <div class="relative flex h-full flex-col justify-between rounded-[28px] border border-white/15 bg-black/25 p-8 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.18)] backdrop-blur-[2px]">
        <div class="flex items-center justify-between">
          <img :src="logoUrl" alt="Los Andalos" class="h-20 w-20 rounded-2xl bg-[#16120f] p-2 object-contain ring-1 ring-white/20" />
          <span class="rounded-full border border-white/20 bg-white/10 px-4 py-2 text-xs font-extrabold uppercase tracking-[0.18em]">{{ t("Secure Access") }}</span>
        </div>
        <div class="max-w-xl">
          <p class="text-sm font-extrabold uppercase tracking-[0.22em] text-[#ffb089]">{{ t("Operations Portal") }}</p>
          <h2 class="mt-4 text-5xl font-black leading-[1.05]">{{ t("Los Andalus") }}</h2>
          <p class="mt-5 max-w-md text-base leading-8 text-white/78">{{ t("Your role decides which workspace opens after login.") }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
