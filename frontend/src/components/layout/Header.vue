<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import Button from '@/components/ui/Button.vue'

const router = useRouter()
const uiStore = useUiStore()
const authStore = useAuthStore()

const { isSidebarExpanded, isDarkMode, isMobile } = storeToRefs(uiStore)
const { isAuthenticated, currentUser } = storeToRefs(authStore)

const themeIcon = computed(() =>
  isDarkMode.value
    ? '<path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />'
    : '<path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />'
)

function toggleTheme() {
  uiStore.setTheme(isDarkMode.value ? 'light' : 'dark')
}

function toggleSidebar() {
  uiStore.toggleSidebar()
}

function openSearch() {
  uiStore.toggleSearch()
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

function goToLogin() {
  router.push('/login')
}

function goToProfile() {
  router.push('/settings')
}
</script>

<template>
  <header
    :class="[
      'fixed top-0 right-0 z-30 flex h-16 items-center justify-between border-b border-bg-tertiary bg-bg-primary/80 backdrop-blur-sm px-4',
      'transition-all duration-normal',
      isMobile ? 'left-0' : isSidebarExpanded ? 'left-sidebar-expanded' : 'left-sidebar-collapsed',
    ]"
  >
    <!-- Left: Menu toggle & Search -->
    <div class="flex items-center gap-3">
      <button
        type="button"
        class="rounded-lg p-2 text-text-secondary hover:bg-bg-secondary hover:text-text-primary transition-colors"
        aria-label="Toggle sidebar"
        @click="toggleSidebar"
      >
        <svg
          class="h-5 w-5"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
          />
        </svg>
      </button>

      <!-- Search button -->
      <button
        type="button"
        class="flex items-center gap-2 rounded-lg border border-bg-tertiary bg-bg-secondary px-3 py-1.5 text-text-muted hover:border-accent-primary hover:text-text-secondary transition-colors"
        @click="openSearch"
      >
        <svg
          class="h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
          />
        </svg>
        <span class="text-small hidden sm:inline">Search...</span>
        <kbd class="hidden rounded border border-bg-tertiary bg-bg-primary px-1.5 py-0.5 text-caption font-mono text-text-muted sm:inline">
          ⌘K
        </kbd>
      </button>
    </div>

    <!-- Right: Theme toggle & User -->
    <div class="flex items-center gap-2">
      <!-- Theme toggle -->
      <button
        type="button"
        class="rounded-lg p-2 text-text-secondary hover:bg-bg-secondary hover:text-text-primary transition-colors"
        aria-label="Toggle theme"
        @click="toggleTheme"
      >
        <svg
          class="h-5 w-5"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
          v-html="themeIcon"
        />
      </button>

      <!-- User menu -->
      <template v-if="isAuthenticated">
        <button
          type="button"
          class="flex items-center gap-2 rounded-lg p-2 text-text-secondary hover:bg-bg-secondary hover:text-text-primary transition-colors"
          @click="goToProfile"
        >
          <div class="flex h-7 w-7 items-center justify-center rounded-full bg-accent-primary text-white text-caption font-medium">
            {{ currentUser?.username?.charAt(0).toUpperCase() || 'U' }}
          </div>
          <span class="hidden text-small font-medium sm:inline">
            {{ currentUser?.username || 'User' }}
          </span>
        </button>
        <button
          type="button"
          class="rounded-lg p-2 text-text-secondary hover:bg-bg-secondary hover:text-accent-error transition-colors"
          aria-label="Logout"
          @click="handleLogout"
        >
          <svg
            class="h-5 w-5"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9"
            />
          </svg>
        </button>
      </template>
      <template v-else>
        <Button
          variant="primary"
          size="sm"
          @click="goToLogin"
        >
          Sign In
        </Button>
      </template>
    </div>
  </header>
</template>
