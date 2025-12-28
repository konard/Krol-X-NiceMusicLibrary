<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const uiStore = useUiStore()
const authStore = useAuthStore()

const { isSidebarExpanded, isMobile } = storeToRefs(uiStore)
const { isAuthenticated } = storeToRefs(authStore)

interface NavItem {
  name: string
  path: string
  icon: string
  requiresAuth?: boolean
}

const mainNavItems: NavItem[] = [
  { name: 'Home', path: '/', icon: 'home' },
  { name: 'Search', path: '/search', icon: 'search' },
  { name: 'Library', path: '/library', icon: 'library', requiresAuth: true },
]

const userNavItems: NavItem[] = [
  { name: 'Favorites', path: '/favorites', icon: 'heart', requiresAuth: true },
  { name: 'Recent', path: '/recent', icon: 'clock', requiresAuth: true },
  { name: 'Statistics', path: '/stats', icon: 'chart', requiresAuth: true },
]

const bottomNavItems: NavItem[] = [
  { name: 'Settings', path: '/settings', icon: 'settings' },
]

const icons: Record<string, string> = {
  home: '<path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />',
  search: '<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />',
  library: '<path stroke-linecap="round" stroke-linejoin="round" d="M9 9l10.5-3m0 6.553v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 11-.99-3.467l2.31-.66a2.25 2.25 0 001.632-2.163zm0 0V2.25L9 5.25v10.303m0 0v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 01-.99-3.467l2.31-.66A2.25 2.25 0 009 15.553z" />',
  heart: '<path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />',
  clock: '<path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />',
  chart: '<path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />',
  settings: '<path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />',
}

const sidebarClasses = computed(() => [
  'fixed left-0 top-0 z-40 flex h-full flex-col border-r border-bg-tertiary bg-bg-primary',
  'transition-all duration-normal',
  isSidebarExpanded.value ? 'w-sidebar-expanded' : 'w-sidebar-collapsed',
  isMobile.value ? '-translate-x-full' : 'translate-x-0',
])

function isActive(path: string): boolean {
  return route.path === path
}

function navigate(path: string) {
  router.push(path)
  if (isMobile.value) {
    uiStore.setSidebarVisible(false)
  }
}

function shouldShowItem(item: NavItem): boolean {
  if (item.requiresAuth && !isAuthenticated.value) {
    return false
  }
  return true
}
</script>

<template>
  <aside :class="sidebarClasses">
    <!-- Logo -->
    <div class="flex h-16 items-center justify-center border-b border-bg-tertiary px-4">
      <router-link
        to="/"
        class="flex items-center gap-2"
      >
        <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-primary">
          <svg
            class="h-5 w-5 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M9 9l10.5-3m0 6.553v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 11-.99-3.467l2.31-.66a2.25 2.25 0 001.632-2.163zm0 0V2.25L9 5.25v10.303m0 0v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 01-.99-3.467l2.31-.66A2.25 2.25 0 009 15.553z"
            />
          </svg>
        </div>
        <span
          v-if="isSidebarExpanded"
          class="text-h3 font-bold text-text-primary"
        >
          NiceMusic
        </span>
      </router-link>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto p-3 scrollbar-thin">
      <!-- Main Navigation -->
      <div class="mb-4">
        <template
          v-for="item in mainNavItems"
          :key="item.path"
        >
          <button
            v-if="shouldShowItem(item)"
            type="button"
            :class="[
              'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 transition-colors duration-fast',
              isActive(item.path)
                ? 'bg-accent-primary/10 text-accent-primary'
                : 'text-text-secondary hover:bg-bg-secondary hover:text-text-primary',
            ]"
            @click="navigate(item.path)"
          >
            <svg
              class="h-5 w-5 flex-shrink-0"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
              v-html="icons[item.icon]"
            />
            <span
              v-if="isSidebarExpanded"
              class="text-small font-medium"
            >
              {{ item.name }}
            </span>
          </button>
        </template>
      </div>

      <!-- User Navigation -->
      <div
        v-if="isAuthenticated"
        class="mb-4"
      >
        <p
          v-if="isSidebarExpanded"
          class="mb-2 px-3 text-caption font-medium uppercase tracking-wider text-text-muted"
        >
          My Music
        </p>
        <template
          v-for="item in userNavItems"
          :key="item.path"
        >
          <button
            v-if="shouldShowItem(item)"
            type="button"
            :class="[
              'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 transition-colors duration-fast',
              isActive(item.path)
                ? 'bg-accent-primary/10 text-accent-primary'
                : 'text-text-secondary hover:bg-bg-secondary hover:text-text-primary',
            ]"
            @click="navigate(item.path)"
          >
            <svg
              class="h-5 w-5 flex-shrink-0"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
              v-html="icons[item.icon]"
            />
            <span
              v-if="isSidebarExpanded"
              class="text-small font-medium"
            >
              {{ item.name }}
            </span>
          </button>
        </template>
      </div>
    </nav>

    <!-- Bottom Navigation -->
    <div class="border-t border-bg-tertiary p-3">
      <template
        v-for="item in bottomNavItems"
        :key="item.path"
      >
        <button
          type="button"
          :class="[
            'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 transition-colors duration-fast',
            isActive(item.path)
              ? 'bg-accent-primary/10 text-accent-primary'
              : 'text-text-secondary hover:bg-bg-secondary hover:text-text-primary',
          ]"
          @click="navigate(item.path)"
        >
          <svg
            class="h-5 w-5 flex-shrink-0"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="1.5"
            v-html="icons[item.icon]"
          />
          <span
            v-if="isSidebarExpanded"
            class="text-small font-medium"
          >
            {{ item.name }}
          </span>
        </button>
      </template>
    </div>
  </aside>
</template>
