import { onMounted, onUnmounted } from 'vue'
import { useUiStore } from '@/stores/ui'

export interface KeyboardShortcut {
  key: string
  ctrl?: boolean
  meta?: boolean
  shift?: boolean
  alt?: boolean
  handler: () => void
  description?: string
}

export function useKeyboard(shortcuts: KeyboardShortcut[] = []) {
  const uiStore = useUiStore()

  // Default shortcuts
  const defaultShortcuts: KeyboardShortcut[] = [
    {
      key: 'k',
      ctrl: true,
      handler: () => uiStore.toggleSearch(),
      description: 'Open search',
    },
    {
      key: 'k',
      meta: true,
      handler: () => uiStore.toggleSearch(),
      description: 'Open search (Mac)',
    },
  ]

  const allShortcuts = [...defaultShortcuts, ...shortcuts]

  function handleKeyDown(event: KeyboardEvent) {
    // Ignore if typing in an input
    const target = event.target as HTMLElement
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable
    ) {
      return
    }

    for (const shortcut of allShortcuts) {
      const ctrlMatch = shortcut.ctrl ? event.ctrlKey : !event.ctrlKey
      const metaMatch = shortcut.meta ? event.metaKey : !event.metaKey
      const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey
      const altMatch = shortcut.alt ? event.altKey : !event.altKey
      const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase()

      if (ctrlMatch && metaMatch && shiftMatch && altMatch && keyMatch) {
        event.preventDefault()
        shortcut.handler()
        break
      }
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown)
  })

  return {
    shortcuts: allShortcuts,
  }
}
