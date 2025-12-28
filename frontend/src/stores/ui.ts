import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { useMediaQuery, usePreferredDark } from '@vueuse/core'
import type { Theme, Toast, ModalState } from '@/types'

const THEME_STORAGE_KEY = 'theme'

export const useUiStore = defineStore('ui', () => {
  // State
  const theme = ref<Theme>((localStorage.getItem(THEME_STORAGE_KEY) as Theme) || 'system')
  const isSidebarExpanded = ref(true)
  const isSidebarVisible = ref(true)
  const toasts = ref<Toast[]>([])
  const modal = ref<ModalState>({
    isOpen: false,
    component: null,
    props: undefined,
  })
  const isSearchOpen = ref(false)
  const isQueueVisible = ref(false)

  // Media queries
  const isMobile = useMediaQuery('(max-width: 768px)')
  const isTablet = useMediaQuery('(min-width: 768px) and (max-width: 1024px)')
  const isDesktop = useMediaQuery('(min-width: 1024px)')
  const prefersDark = usePreferredDark()

  // Getters
  const isDarkMode = computed(() => {
    if (theme.value === 'system') {
      return prefersDark.value
    }
    return theme.value === 'dark'
  })

  const sidebarWidth = computed(() => {
    if (isMobile.value) return 0
    return isSidebarExpanded.value ? 260 : 72
  })

  // Theme watcher - apply dark class to html
  watch(
    isDarkMode,
    (dark) => {
      if (dark) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    },
    { immediate: true }
  )

  // Actions
  function setTheme(newTheme: Theme): void {
    theme.value = newTheme
    localStorage.setItem(THEME_STORAGE_KEY, newTheme)
  }

  function toggleSidebar(): void {
    isSidebarExpanded.value = !isSidebarExpanded.value
  }

  function setSidebarVisible(visible: boolean): void {
    isSidebarVisible.value = visible
  }

  function addToast(toast: Omit<Toast, 'id'>): void {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration ?? 5000,
    }
    toasts.value.push(newToast)

    // Auto-remove toast after duration
    if (newToast.duration && newToast.duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, newToast.duration)
    }
  }

  function removeToast(id: string): void {
    const index = toasts.value.findIndex((t) => t.id === id)
    if (index !== -1) {
      toasts.value.splice(index, 1)
    }
  }

  function showSuccess(message: string): void {
    addToast({ type: 'success', message })
  }

  function showError(message: string): void {
    addToast({ type: 'error', message })
  }

  function showWarning(message: string): void {
    addToast({ type: 'warning', message })
  }

  function showInfo(message: string): void {
    addToast({ type: 'info', message })
  }

  function openModal(component: string, props?: Record<string, unknown>): void {
    modal.value = {
      isOpen: true,
      component,
      props,
    }
  }

  function closeModal(): void {
    modal.value = {
      isOpen: false,
      component: null,
      props: undefined,
    }
  }

  function toggleSearch(): void {
    isSearchOpen.value = !isSearchOpen.value
  }

  function toggleQueue(): void {
    isQueueVisible.value = !isQueueVisible.value
  }

  // Initialize - auto-collapse sidebar on mobile
  watch(
    isMobile,
    (mobile) => {
      if (mobile) {
        isSidebarExpanded.value = false
        isSidebarVisible.value = false
      } else {
        isSidebarVisible.value = true
      }
    },
    { immediate: true }
  )

  return {
    // State
    theme,
    isSidebarExpanded,
    isSidebarVisible,
    toasts,
    modal,
    isSearchOpen,
    isQueueVisible,
    // Media queries
    isMobile,
    isTablet,
    isDesktop,
    // Getters
    isDarkMode,
    sidebarWidth,
    // Actions
    setTheme,
    toggleSidebar,
    setSidebarVisible,
    addToast,
    removeToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    openModal,
    closeModal,
    toggleSearch,
    toggleQueue,
  }
})
