import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUiStore } from '@/stores/ui'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(global, 'localStorage', { value: localStorageMock })

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

describe('useUiStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('theme', () => {
    it('has default theme as system', () => {
      const store = useUiStore()
      expect(store.theme).toBe('system')
    })

    it('can set theme to light', () => {
      const store = useUiStore()
      store.setTheme('light')
      expect(store.theme).toBe('light')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('theme', 'light')
    })

    it('can set theme to dark', () => {
      const store = useUiStore()
      store.setTheme('dark')
      expect(store.theme).toBe('dark')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('theme', 'dark')
    })
  })

  describe('sidebar', () => {
    it('has sidebar expanded by default', () => {
      const store = useUiStore()
      expect(store.isSidebarExpanded).toBe(true)
    })

    it('can toggle sidebar', () => {
      const store = useUiStore()
      store.toggleSidebar()
      expect(store.isSidebarExpanded).toBe(false)
      store.toggleSidebar()
      expect(store.isSidebarExpanded).toBe(true)
    })
  })

  describe('toasts', () => {
    it('starts with no toasts', () => {
      const store = useUiStore()
      expect(store.toasts).toHaveLength(0)
    })

    it('can add a toast', () => {
      const store = useUiStore()
      store.addToast({ type: 'success', message: 'Test message' })
      expect(store.toasts).toHaveLength(1)
      expect(store.toasts[0].message).toBe('Test message')
      expect(store.toasts[0].type).toBe('success')
    })

    it('can remove a toast', () => {
      const store = useUiStore()
      store.addToast({ type: 'error', message: 'Error message' })
      const toastId = store.toasts[0].id
      store.removeToast(toastId)
      expect(store.toasts).toHaveLength(0)
    })

    it('has convenience methods for toast types', () => {
      const store = useUiStore()

      store.showSuccess('Success!')
      expect(store.toasts[0].type).toBe('success')

      store.showError('Error!')
      expect(store.toasts[1].type).toBe('error')

      store.showWarning('Warning!')
      expect(store.toasts[2].type).toBe('warning')

      store.showInfo('Info!')
      expect(store.toasts[3].type).toBe('info')
    })
  })

  describe('modal', () => {
    it('starts with modal closed', () => {
      const store = useUiStore()
      expect(store.modal.isOpen).toBe(false)
      expect(store.modal.component).toBeNull()
    })

    it('can open modal', () => {
      const store = useUiStore()
      store.openModal('TestModal', { id: 1 })
      expect(store.modal.isOpen).toBe(true)
      expect(store.modal.component).toBe('TestModal')
      expect(store.modal.props).toEqual({ id: 1 })
    })

    it('can close modal', () => {
      const store = useUiStore()
      store.openModal('TestModal')
      store.closeModal()
      expect(store.modal.isOpen).toBe(false)
      expect(store.modal.component).toBeNull()
    })
  })

  describe('search', () => {
    it('starts with search closed', () => {
      const store = useUiStore()
      expect(store.isSearchOpen).toBe(false)
    })

    it('can toggle search', () => {
      const store = useUiStore()
      store.toggleSearch()
      expect(store.isSearchOpen).toBe(true)
      store.toggleSearch()
      expect(store.isSearchOpen).toBe(false)
    })
  })
})
