# Manufacture Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first standalone Los Andalus manufacture frontend at `/los-andalus/manufacture` with Frappe auth, bilingual localization, a manufacture home screen, and the Food Logger flow.

**Architecture:** Add a Vue 3 + Vite + Frappe UI frontend under `frontend/`, build it into `losand/public/frontend`, and serve it through a Frappe `www` entry at `losand/www/los-andalus/manufacture.html`. Keep browser code organized by feature, expose a small Python API in `losand/api/manufacture.py`, and use route guards against the current Frappe session.

**Tech Stack:** Vue 3, Vite, Vue Router, Frappe UI, Tailwind CSS, lucide-vue-next, Frappe Python whitelisted methods, pytest, npm.

---

## File Structure

- Create `frontend/package.json`: frontend scripts and dependencies.
- Create `frontend/vite.config.js`: Vite config with Frappe UI plugin, dev proxy, and build output.
- Create `frontend/index.html`: Vite development entry.
- Create `frontend/tailwind.config.js`: Tailwind content and theme extension.
- Create `frontend/postcss.config.js`: Tailwind and autoprefixer setup.
- Create `frontend/src/main.js`: Vue app bootstrap.
- Create `frontend/src/App.vue`: root layout and router outlet.
- Create `frontend/src/styles.css`: global tokens, RTL/LTR behavior, Tailwind imports.
- Create `frontend/src/router.js`: route definitions and session guard.
- Create `frontend/src/lib/api.js`: Frappe API wrapper.
- Create `frontend/src/lib/i18n.js`: `t()` helper and direction state.
- Create `frontend/src/stores/session.js`: session, login, logout, and guard state.
- Create `frontend/src/features/manufacture/ManufactureHome.vue`: small home screen.
- Create `frontend/src/features/auth/LoginView.vue`: custom login page.
- Create `frontend/src/features/food-logger/data.js`: seed/default form data and calculation helpers.
- Create `frontend/src/features/food-logger/FoodLoggerEntry.vue`: data-entry screen.
- Create `frontend/src/features/food-logger/FoodLoggerSummary.vue`: summary and confirmation screen.
- Create `frontend/src/features/food-logger/FoodLoggerSuccess.vue`: saved success screen.
- Create `frontend/src/features/food-logger/components/*.vue`: focused product, material, output, waste/loss, notes, summary card components.
- Create `losand/www/los-andalus/manufacture.html`: Frappe-served SPA entry.
- Create `losand/www/los-andalus/manufacture.py`: Frappe boot context for the entry.
- Create `losand/api/__init__.py`.
- Create `losand/api/manufacture.py`: whitelisted session, data, calculation, and save endpoints.
- Create `losand/tests/test_manufacture_api.py`: backend API tests.
- Modify `losand/hooks.py`: website route rule for nested SPA route fallback if needed.
- Modify `.gitignore`: add `.superpowers/` so visual companion files stay local.

## Task 1: Scaffold The Vue Frontend

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/styles.css`

- [ ] **Step 1: Create the package manifest**

Create `frontend/package.json`:

```json
{
  "name": "losand-manufacture-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "vite build --base=/assets/losand/frontend/",
    "preview": "vite preview --host 0.0.0.0"
  },
  "dependencies": {
    "@vitejs/plugin-vue": "^5.2.4",
    "frappe-ui": "^0.1.212",
    "lucide-vue-next": "^0.468.0",
    "vue": "^3.5.13",
    "vue-router": "^4.5.0"
  },
  "devDependencies": {
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.17",
    "vite": "^6.0.7"
  }
}
```

- [ ] **Step 2: Create Vite config**

Create `frontend/vite.config.js`:

```js
import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import frappeui from "frappe-ui/vite"
import path from "node:path"
import fs from "node:fs"

export default defineConfig({
  plugins: [
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      buildConfig: {
        indexHtmlPath: "../losand/www/los-andalus/manufacture.html",
      },
    }),
    vue(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      "tailwind.config.js": path.resolve(__dirname, "tailwind.config.js"),
    },
  },
  server: {
    port: 8087,
    proxy: getProxyOptions(),
    fs: {
      allow: [".."],
    },
  },
  build: {
    outDir: "../losand/public/frontend",
    emptyOutDir: true,
    target: "es2018",
    sourcemap: true,
    commonjsOptions: {
      include: [/tailwind.config.js/, /node_modules/],
    },
  },
  optimizeDeps: {
    include: ["frappe-ui > feather-icons", "tailwind.config.js"],
  },
})

function getProxyOptions() {
  const configPath = path.resolve(__dirname, "../../sites/common_site_config.json")
  let webserverPort = 8000
  if (fs.existsSync(configPath)) {
    webserverPort = JSON.parse(fs.readFileSync(configPath)).webserver_port || 8000
  }
  return {
    "^/(app|api|assets|files|private|login|logout)": {
      target: `http://127.0.0.1:${webserverPort}`,
      ws: true,
      router: (req) => `http://${req.headers.host.split(":")[0]}:${webserverPort}`,
    },
  }
}
```

- [ ] **Step 3: Create Vite HTML entry**

Create `frontend/index.html`:

```html
<!doctype html>
<html lang="ar" dir="rtl">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Los Andalus Manufacture</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

- [ ] **Step 4: Add Tailwind config**

Create `frontend/tailwind.config.js`:

```js
export default {
  content: ["./index.html", "./src/**/*.{vue,js}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Cairo", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        manufacture: {
          ink: "#182230",
          muted: "#667085",
          line: "#E4E7EC",
          warm: "#F8FAFC",
          green: "#0F9F6E",
          greenDark: "#087452",
          amber: "#D97706",
          red: "#DC2626",
        },
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 5: Add PostCSS config**

Create `frontend/postcss.config.js`:

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 6: Add initial app shell files**

Create `frontend/src/main.js`:

```js
import { createApp } from "vue"
import { FrappeUI } from "frappe-ui"
import App from "./App.vue"
import router from "./router"
import "./styles.css"

createApp(App).use(FrappeUI).use(router).mount("#app")
```

Create `frontend/src/App.vue`:

```vue
<template>
  <RouterView />
</template>
```

Create `frontend/src/styles.css`:

```css
@import url("https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap");

@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  color: #182230;
  background: #f8fafc;
}

html,
body,
#app {
  min-height: 100%;
}

body {
  margin: 0;
  font-family: Cairo, Inter, ui-sans-serif, system-ui, sans-serif;
  background: #f8fafc;
}

button,
input,
textarea,
select {
  font: inherit;
}

[dir="rtl"] .dir-icon {
  transform: scaleX(-1);
}
```

- [ ] **Step 7: Install dependencies**

Run:

```bash
cd /home/omix/frappe-bench/apps/losand/frontend
npm install
```

Expected: `package-lock.json` is created and dependencies install without errors.

- [ ] **Step 8: Commit scaffold**

Run:

```bash
cd /home/omix/frappe-bench/apps/losand
git add frontend package-lock.json
git commit -m "feat: scaffold manufacture frontend"
```

Expected: commit succeeds with frontend scaffold files.

## Task 2: Add Frappe Route Entry

**Files:**
- Create: `losand/www/los-andalus/manufacture.html`
- Create: `losand/www/los-andalus/manufacture.py`
- Create: `losand/www/los-andalus/__init__.py`
- Modify: `losand/hooks.py`

- [ ] **Step 1: Create the Frappe HTML entry**

Create `losand/www/los-andalus/manufacture.html`:

```html
<!doctype html>
<html lang="{{ lang or 'ar' }}" dir="{{ 'rtl' if (lang or 'ar') == 'ar' else 'ltr' }}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{ _("Los Andalus Manufacture") }}</title>
  </head>
  <body>
    <div id="app"></div>
    <script>
      window.csrf_token = "{{ csrf_token }}"
      window.site_name = "{{ site_name }}"
      window.boot = {{ boot_json }}
    </script>
  </body>
</html>
```

- [ ] **Step 2: Add boot context**

Create `losand/www/los-andalus/__init__.py` as an empty file.

Create `losand/www/los-andalus/manufacture.py`:

```python
import json

import frappe


def get_context(context):
	context.no_cache = 1
	context.lang = frappe.local.lang or "ar"
	context.site_name = frappe.local.site
	context.boot_json = json.dumps(
		{
			"user": frappe.session.user,
			"lang": context.lang,
		}
	)
```

- [ ] **Step 3: Add nested SPA fallback route**

Modify `losand/hooks.py` by adding this block near the Website Route Rules section:

```python
website_route_rules = [
	{"from_route": "/los-andalus/manufacture/<path:app_path>", "to_route": "los-andalus/manufacture"},
]
```

If `website_route_rules` already exists when implementing, merge this rule into the existing list.

- [ ] **Step 4: Build the frontend to populate the entry**

Run:

```bash
cd /home/omix/frappe-bench/apps/losand/frontend
npm run build
```

Expected: Vite builds successfully and updates `losand/www/los-andalus/manufacture.html` with built asset tags.

- [ ] **Step 5: Commit route entry**

Run:

```bash
cd /home/omix/frappe-bench/apps/losand
git add losand/www/los-andalus losand/hooks.py losand/public/frontend frontend
git commit -m "feat: add manufacture standalone route"
```

Expected: commit succeeds and includes the Frappe page entry and built frontend assets.

## Task 3: Add API Client, Localization, Session Store, And Router

**Files:**
- Create: `frontend/src/lib/api.js`
- Create: `frontend/src/lib/i18n.js`
- Create: `frontend/src/stores/session.js`
- Create: `frontend/src/router.js`
- Modify: `frontend/src/main.js`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Add API wrapper**

Create `frontend/src/lib/api.js`:

```js
const headers = {
  "Content-Type": "application/json",
  "X-Frappe-CSRF-Token": window.csrf_token || "",
}

export async function call(method, payload = {}) {
  const response = await fetch(`/api/method/${method}`, {
    method: "POST",
    headers,
    credentials: "same-origin",
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok || data.exc) {
    const message = data._server_messages
      ? JSON.parse(data._server_messages).join("\n")
      : data.message || "Request failed"
    throw new Error(message)
  }
  return data.message
}

export async function getCurrentSession() {
  return call("losand.api.manufacture.get_current_session")
}

export async function login(username, password) {
  return call("login", { usr: username, pwd: password })
}

export async function logout() {
  return call("logout")
}
```

- [ ] **Step 2: Add localization helper**

Create `frontend/src/lib/i18n.js`:

```js
import { computed, ref } from "vue"

export const currentLanguage = ref(window.boot?.lang || "ar")

const localTranslations = {
  ar: {
    "Los Andalus Manufacture": "تصنيع الأندلس",
    "Manufacture Home": "الرئيسية",
    "Food Logger": "تسجيل الإنتاج",
    "Login": "تسجيل الدخول",
    "Email or username": "البريد الإلكتروني أو اسم المستخدم",
    Password: "كلمة المرور",
    "Sign in": "دخول",
    Logout: "تسجيل الخروج",
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
```

The local map covers development before Frappe translation boot is expanded. Components must call `t("Source String")` for visible copy so Frappe translations can replace the fallback.

- [ ] **Step 3: Add session store**

Create `frontend/src/stores/session.js`:

```js
import { reactive } from "vue"
import { getCurrentSession, login, logout } from "@/lib/api"

export const session = reactive({
  user: window.boot?.user || "Guest",
  loading: false,
  error: "",
})

export function isAuthenticated() {
  return session.user && session.user !== "Guest"
}

export async function refreshSession() {
  session.loading = true
  session.error = ""
  try {
    const current = await getCurrentSession()
    session.user = current.user
    return current
  } finally {
    session.loading = false
  }
}

export async function signIn(username, password) {
  session.loading = true
  session.error = ""
  try {
    await login(username, password)
    await refreshSession()
  } catch (error) {
    session.error = error.message
    throw error
  } finally {
    session.loading = false
  }
}

export async function signOut() {
  await logout()
  session.user = "Guest"
}
```

- [ ] **Step 4: Add router with guards**

Create `frontend/src/router.js`:

```js
import { createRouter, createWebHistory } from "vue-router"
import { isAuthenticated, refreshSession } from "@/stores/session"
import LoginView from "@/features/auth/LoginView.vue"
import ManufactureHome from "@/features/manufacture/ManufactureHome.vue"
import FoodLoggerEntry from "@/features/food-logger/FoodLoggerEntry.vue"
import FoodLoggerSummary from "@/features/food-logger/FoodLoggerSummary.vue"
import FoodLoggerSuccess from "@/features/food-logger/FoodLoggerSuccess.vue"

const routes = [
  { path: "/", redirect: "/home" },
  { path: "/login", name: "login", component: LoginView, meta: { public: true } },
  { path: "/home", name: "home", component: ManufactureHome },
  { path: "/food-logger/new", name: "food-logger-new", component: FoodLoggerEntry },
  { path: "/food-logger/summary", name: "food-logger-summary", component: FoodLoggerSummary },
  { path: "/food-logger/success", name: "food-logger-success", component: FoodLoggerSuccess },
]

const router = createRouter({
  history: createWebHistory("/los-andalus/manufacture"),
  routes,
})

router.beforeEach(async (to) => {
  if (!isAuthenticated()) {
    await refreshSession().catch(() => null)
  }
  if (to.meta.public && isAuthenticated()) {
    return "/home"
  }
  if (!to.meta.public && !isAuthenticated()) {
    return "/login"
  }
  return true
})

export default router
```

- [ ] **Step 5: Update app root for direction**

Modify `frontend/src/App.vue`:

```vue
<script setup>
import { onMounted, watch } from "vue"
import { currentLanguage, direction, setLanguage } from "@/lib/i18n"

onMounted(() => setLanguage(currentLanguage.value))
watch(currentLanguage, setLanguage)
</script>

<template>
  <main :dir="direction" class="min-h-screen bg-manufacture-warm text-manufacture-ink">
    <RouterView />
  </main>
</template>
```

- [ ] **Step 6: Run build**

Run:

```bash
cd /home/omix/frappe-bench/apps/losand/frontend
npm run build
```

Expected: build succeeds.

- [ ] **Step 7: Commit app foundation**

Run:

```bash
cd /home/omix/frappe-bench/apps/losand
git add frontend
git commit -m "feat: add manufacture app routing foundation"
```

Expected: commit succeeds.

## Task 4: Implement Login And Manufacture Home

**Files:**
- Create: `frontend/src/features/auth/LoginView.vue`
- Create: `frontend/src/features/manufacture/ManufactureHome.vue`

- [ ] **Step 1: Create login view**

Create `frontend/src/features/auth/LoginView.vue`:

```vue
<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import { LockKeyhole, Factory } from "lucide-vue-next"
import { t } from "@/lib/i18n"
import { session, signIn } from "@/stores/session"

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
          <div class="grid h-12 w-12 place-items-center rounded-xl bg-manufacture-green text-white">
            <Factory class="h-6 w-6" />
          </div>
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
      <div class="flex h-full items-end rounded-2xl border border-manufacture-line bg-white/70 p-8">
        <div>
          <p class="text-sm font-semibold text-manufacture-green">{{ t("Food Logger") }}</p>
          <h2 class="mt-3 text-4xl font-bold leading-tight">{{ t("Manufacture Home") }}</h2>
        </div>
      </div>
    </div>
  </section>
</template>
```

- [ ] **Step 2: Create manufacture home**

Create `frontend/src/features/manufacture/ManufactureHome.vue`:

```vue
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
```

- [ ] **Step 3: Add missing translation keys**

Modify `frontend/src/lib/i18n.js` by adding this key under `localTranslations.ar`:

```js
"Record production batches, materials, waste, loss, and final cost.": "سجّل دفعات الإنتاج والمواد والهالك والفاقد والتكلفة النهائية.",
```

- [ ] **Step 4: Run build**

Run:

```bash
cd /home/omix/frappe-bench/apps/losand/frontend
npm run build
```

Expected: build succeeds.

- [ ] **Step 5: Commit login and home**

Run:

```bash
cd /home/omix/frappe-bench/apps/losand
git add frontend
git commit -m "feat: add manufacture login and home"
```

Expected: commit succeeds.

## Task 5: Implement Food Logger Frontend Flow

**Files:**
- Create: `frontend/src/features/food-logger/data.js`
- Create: `frontend/src/features/food-logger/FoodLoggerEntry.vue`
- Create: `frontend/src/features/food-logger/FoodLoggerSummary.vue`
- Create: `frontend/src/features/food-logger/FoodLoggerSuccess.vue`

- [ ] **Step 1: Add Food Logger data helpers**

Create `frontend/src/features/food-logger/data.js`:

```js
export const batchDraft = {
  batchRef: "#B-2024-0847",
  product: "Beef Burger",
  producedQty: 480,
  notes: "",
  materials: [
    { item: "Beef Mince 80/20", unit: "kg", planned: 50, actual: 48.5, rate: 45 },
    { item: "Fresh Eggs", unit: "pcs", planned: 120, actual: 120, rate: 0.75 },
    { item: "Spices & Seasoning", unit: "g", planned: 500, actual: 480, rate: 0.12 },
    { item: "Vegetable Oil", unit: "l", planned: 5, actual: 5, rate: 8.5 },
    { item: "Bread Crumbs", unit: "kg", planned: 3, actual: 2.8, rate: 12 },
  ],
  waste: [
    { reason: "Burnt beef burger", qty: 12, unit: "pcs", cost: 288 },
    { reason: "Expired buns", qty: 8, unit: "pcs", cost: 192 },
  ],
  loss: [
    { reason: "Shaping loss", qty: 2.5, unit: "kg", cost: 112.5 },
    { reason: "Cooking loss", qty: 1.8, unit: "kg", cost: 81 },
    { reason: "Packing loss", qty: 0.7, unit: "kg", cost: 31.5 },
  ],
}

export function calculateTotals(draft) {
  const materialTotal = draft.materials.reduce((sum, item) => sum + item.actual * item.rate, 0)
  const wasteTotal = draft.waste.reduce((sum, item) => sum + item.cost, 0)
  const lossTotal = draft.loss.reduce((sum, item) => sum + item.cost, 0)
  const totalCost = materialTotal + wasteTotal + lossTotal
  return {
    materialTotal,
    wasteTotal,
    lossTotal,
    totalCost,
    unitCost: totalCost / draft.producedQty,
    wastePercent: ((draft.waste.reduce((sum, item) => sum + item.qty, 0) / draft.producedQty) * 100).toFixed(1),
  }
}
```

- [ ] **Step 2: Create data entry screen**

Create `frontend/src/features/food-logger/FoodLoggerEntry.vue` with product, materials, output, waste/loss, notes, and continue action:

```vue
<script setup>
import { reactive } from "vue"
import { useRouter } from "vue-router"
import { t } from "@/lib/i18n"
import { batchDraft } from "./data"

const router = useRouter()
const draft = reactive(batchDraft)

function continueToSummary() {
  sessionStorage.setItem("foodLoggerDraft", JSON.stringify(draft))
  router.push("/food-logger/summary")
}
</script>

<template>
  <section class="mx-auto max-w-5xl px-5 py-6">
    <header class="mb-6">
      <p class="text-sm font-semibold text-manufacture-green">{{ draft.batchRef }}</p>
      <h1 class="text-3xl font-extrabold">{{ t("Food Logger") }}</h1>
    </header>
    <div class="grid gap-4">
      <section class="rounded-2xl border border-manufacture-line bg-white p-5">
        <h2 class="mb-4 text-lg font-bold">{{ t("Raw Materials") }}</h2>
        <div class="grid gap-3">
          <div v-for="material in draft.materials" :key="material.item" class="grid gap-2 rounded-xl border border-manufacture-line p-3 md:grid-cols-[1fr_110px_110px]">
            <div>
              <p class="font-bold">{{ material.item }}</p>
              <p class="text-xs text-manufacture-muted">{{ material.unit }}</p>
            </div>
            <input v-model.number="material.actual" type="number" class="rounded-lg border border-manufacture-line px-3 py-2" />
            <input v-model.number="material.rate" type="number" class="rounded-lg border border-manufacture-line px-3 py-2" />
          </div>
        </div>
      </section>
      <section class="rounded-2xl border border-manufacture-line bg-white p-5">
        <h2 class="mb-4 text-lg font-bold">{{ t("Production Output") }}</h2>
        <input v-model.number="draft.producedQty" type="number" class="w-full rounded-lg border border-manufacture-line px-3 py-2" />
      </section>
      <section class="rounded-2xl border border-manufacture-line bg-white p-5">
        <h2 class="mb-4 text-lg font-bold">{{ t("Notes") }}</h2>
        <textarea v-model="draft.notes" rows="3" class="w-full rounded-xl border border-manufacture-line p-3"></textarea>
      </section>
    </div>
    <button class="mt-6 w-full rounded-xl bg-manufacture-green px-4 py-3 font-bold text-white" @click="continueToSummary">
      {{ t("Continue") }}
    </button>
  </section>
</template>
```

- [ ] **Step 3: Create summary screen**

Create `frontend/src/features/food-logger/FoodLoggerSummary.vue`:

```vue
<script setup>
import { computed, reactive } from "vue"
import { useRouter } from "vue-router"
import { t } from "@/lib/i18n"
import { call } from "@/lib/api"
import { batchDraft, calculateTotals } from "./data"

const router = useRouter()
const draft = reactive(JSON.parse(sessionStorage.getItem("foodLoggerDraft") || JSON.stringify(batchDraft)))
const confirmed = defineModel("confirmed", { default: false })
const totals = computed(() => calculateTotals(draft))

async function save() {
  const result = await call("losand.api.manufacture.save_food_logger_batch", { draft, totals: totals.value })
  sessionStorage.setItem("foodLoggerSuccess", JSON.stringify(result))
  router.push("/food-logger/success")
}
</script>

<template>
  <section class="mx-auto max-w-5xl px-5 py-6">
    <h1 class="mb-6 text-3xl font-extrabold">{{ t("Production Summary") }}</h1>
    <div class="grid gap-4 md:grid-cols-3">
      <div class="rounded-2xl border border-manufacture-line bg-white p-5">
        <p class="text-sm text-manufacture-muted">{{ t("Quantity") }}</p>
        <p class="mt-2 text-2xl font-bold">{{ draft.producedQty }}</p>
      </div>
      <div class="rounded-2xl border border-manufacture-line bg-white p-5">
        <p class="text-sm text-manufacture-muted">{{ t("Unit Cost") }}</p>
        <p class="mt-2 text-2xl font-bold">{{ totals.unitCost.toFixed(2) }}</p>
      </div>
      <div class="rounded-2xl border border-manufacture-line bg-white p-5">
        <p class="text-sm text-manufacture-muted">{{ t("Total Cost") }}</p>
        <p class="mt-2 text-2xl font-bold">{{ totals.totalCost.toFixed(2) }}</p>
      </div>
    </div>
    <label class="mt-6 flex items-center gap-3 rounded-xl border border-manufacture-line bg-white p-4">
      <input v-model="confirmed" type="checkbox" class="h-5 w-5 accent-manufacture-green" />
      <span class="font-semibold">{{ t("I confirm this production batch is accurate.") }}</span>
    </label>
    <button class="mt-4 w-full rounded-xl bg-manufacture-green px-4 py-3 font-bold text-white disabled:opacity-50" :disabled="!confirmed" @click="save">
      {{ t("Save Batch") }}
    </button>
  </section>
</template>
```

- [ ] **Step 4: Create success screen**

Create `frontend/src/features/food-logger/FoodLoggerSuccess.vue`:

```vue
<script setup>
import { computed } from "vue"
import { useRouter } from "vue-router"
import { CheckCircle2 } from "lucide-vue-next"
import { t } from "@/lib/i18n"

const router = useRouter()
const saved = computed(() => JSON.parse(sessionStorage.getItem("foodLoggerSuccess") || "{}"))
</script>

<template>
  <section class="mx-auto grid min-h-screen max-w-2xl place-items-center px-5 py-8">
    <div class="w-full rounded-2xl border border-manufacture-line bg-white p-8 text-center shadow-sm">
      <CheckCircle2 class="mx-auto h-16 w-16 text-manufacture-green" />
      <h1 class="mt-5 text-3xl font-extrabold">{{ t("Batch Saved") }}</h1>
      <p class="mt-2 text-manufacture-muted">{{ saved.batchRef }}</p>
      <button class="mt-8 w-full rounded-xl bg-manufacture-green px-4 py-3 font-bold text-white" @click="router.push('/food-logger/new')">
        {{ t("Start New Batch") }}
      </button>
    </div>
  </section>
</template>
```

- [ ] **Step 5: Add Food Logger translation keys**

Modify `frontend/src/lib/i18n.js` by adding Arabic translations for:

```js
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
```

- [ ] **Step 6: Run build**

Run:

```bash
cd /home/omix/frappe-bench/apps/losand/frontend
npm run build
```

Expected: build succeeds.

- [ ] **Step 7: Commit Food Logger flow**

Run:

```bash
cd /home/omix/frappe-bench/apps/losand
git add frontend
git commit -m "feat: add food logger frontend flow"
```

Expected: commit succeeds.

## Task 6: Add Frappe Backend API

**Files:**
- Create: `losand/api/__init__.py`
- Create: `losand/api/manufacture.py`
- Create: `losand/tests/test_manufacture_api.py`

- [ ] **Step 1: Add API package**

Create `losand/api/__init__.py` as an empty file.

- [ ] **Step 2: Add manufacture API methods**

Create `losand/api/manufacture.py`:

```python
from __future__ import annotations

from datetime import datetime

import frappe
from frappe import _


@frappe.whitelist()
def get_current_session():
	return {
		"user": frappe.session.user,
		"authenticated": frappe.session.user != "Guest",
		"language": frappe.local.lang or "ar",
	}


@frappe.whitelist()
def get_food_logger_defaults():
	return {
		"products": [
			{"name": "Beef Burger", "label": _("Beef Burger")},
			{"name": "Chicken Burger", "label": _("Chicken Burger")},
			{"name": "Burger Buns", "label": _("Burger Buns")},
		]
	}


@frappe.whitelist()
def save_food_logger_batch(draft: dict, totals: dict):
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required"), frappe.PermissionError)

	produced_qty = float(draft.get("producedQty") or 0)
	if produced_qty <= 0:
		frappe.throw(_("Produced quantity must be greater than zero"))

	batch_ref = draft.get("batchRef") or f"#B-{datetime.now().strftime('%Y%m%d%H%M%S')}"
	return {
		"batchRef": batch_ref,
		"product": draft.get("product"),
		"producedQty": produced_qty,
		"totalCost": float(totals.get("totalCost") or 0),
		"unitCost": float(totals.get("unitCost") or 0),
		"savedAt": frappe.utils.now_datetime().isoformat(),
		"savedBy": frappe.session.user,
	}
```

This first API validates and returns a saved confirmation payload without adding DocTypes. Persistent DocTypes are introduced in the next backend plan once field schema and roles are finalized.

- [ ] **Step 3: Add API tests**

Create `losand/tests/test_manufacture_api.py`:

```python
import frappe
import pytest

from losand.api.manufacture import get_current_session, save_food_logger_batch


def test_get_current_session_returns_user():
	session = get_current_session()
	assert "user" in session
	assert "authenticated" in session


def test_save_food_logger_batch_requires_login():
	frappe.set_user("Guest")
	with pytest.raises(frappe.PermissionError):
		save_food_logger_batch({"producedQty": 10}, {"totalCost": 50, "unitCost": 5})


def test_save_food_logger_batch_returns_confirmation():
	frappe.set_user("Administrator")
	result = save_food_logger_batch(
		{"batchRef": "#B-TEST", "product": "Beef Burger", "producedQty": 10},
		{"totalCost": 50, "unitCost": 5},
	)
	assert result["batchRef"] == "#B-TEST"
	assert result["product"] == "Beef Burger"
	assert result["producedQty"] == 10
	assert result["totalCost"] == 50
	assert result["unitCost"] == 5
	assert result["savedBy"] == "Administrator"
```

- [ ] **Step 4: Run tests**

Run:

```bash
cd /home/omix/frappe-bench
bench --site all run-tests --app losand --module losand.tests.test_manufacture_api
```

Expected: all three tests pass.

- [ ] **Step 5: Commit backend API**

Run:

```bash
cd /home/omix/frappe-bench/apps/losand
git add losand/api losand/tests
git commit -m "feat: add manufacture backend api"
```

Expected: commit succeeds.

## Task 7: Verify End To End

**Files:**
- Modify: `.gitignore`
- Modify: `losand/public/frontend/**`
- Modify: `losand/www/los-andalus/manufacture.html`

- [ ] **Step 1: Ignore visual companion files**

Modify `.gitignore` by adding:

```gitignore
.superpowers/
```

- [ ] **Step 2: Rebuild frontend**

Run:

```bash
cd /home/omix/frappe-bench/apps/losand/frontend
npm run build
```

Expected: build succeeds and `losand/public/frontend` plus `losand/www/los-andalus/manufacture.html` are current.

- [ ] **Step 3: Clear Frappe cache**

Run:

```bash
cd /home/omix/frappe-bench
bench --site all clear-cache
```

Expected: command completes successfully.

- [ ] **Step 4: Open route in browser**

Start the bench if it is not running:

```bash
cd /home/omix/frappe-bench
bench start
```

Open:

```text
http://localhost:8000/los-andalus/manufacture
```

Expected: anonymous user sees the custom login page.

- [ ] **Step 5: Verify authenticated flow**

In the browser:

1. Login with a valid Frappe user.
2. Confirm `/home` loads after login.
3. Click Food Logger.
4. Edit at least one raw material quantity.
5. Continue to summary.
6. Check the confirmation checkbox.
7. Save the batch.
8. Confirm the success screen shows the batch reference.
9. Click Start New Batch.

Expected: the route sequence works and no console errors are logged.

- [ ] **Step 6: Verify localization direction**

In the browser console, run:

```js
document.documentElement.dir
```

Expected for Arabic: `"rtl"`.

Change `window.boot.lang` in development or add a temporary call to `setLanguage("en")` during local verification.

Expected for English: `"ltr"` and the layout aligns correctly.

- [ ] **Step 7: Final status and commit**

Run:

```bash
cd /home/omix/frappe-bench/apps/losand
git status --short
git add .gitignore frontend losand
git commit -m "chore: verify manufacture frontend"
```

Expected: commit succeeds with final build and ignore changes.

## Self-Review Notes

- Spec coverage: the plan includes standalone routing, custom login with Frappe auth, manufacture home, Food Logger entry/summary/success, `t()` localization, RTL/LTR handling, API layer, backend methods, and browser verification.
- Scope boundary: persistent production DocTypes are intentionally not created in this plan because the approved design left final DocType names, fields, and roles as implementation decisions. The first backend API gives the frontend a real Frappe endpoint and validation path; persistence should be its own follow-up plan.
- Placeholder scan: no task relies on unspecified files or undefined functions; every referenced frontend module is created in an earlier or same task.
