<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { usePlaylistStore } from '@/stores/playlist'

export interface AddToPlaylistMenuProps {
  modelValue: boolean
  songId: string
  x?: number
  y?: number
}

const props = withDefaults(defineProps<AddToPlaylistMenuProps>(), {
  x: 0,
  y: 0,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  added: [playlistId: string, playlistName: string]
  createNew: []
}>()

const menuRef = ref<HTMLElement | null>(null)
const position = ref({ x: 0, y: 0 })
const isAdding = ref<string | null>(null)

const playlistStore = usePlaylistStore()
const { playlists, isLoading } = storeToRefs(playlistStore)

onMounted(() => {
  if (playlists.value.length === 0) {
    playlistStore.fetchPlaylists(true)
  }
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('scroll', handleScroll, true)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('scroll', handleScroll, true)
})

// Adjust position to keep menu within viewport
function adjustPosition() {
  if (!menuRef.value) return

  const menu = menuRef.value
  const rect = menu.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  let x = props.x
  let y = props.y

  // Adjust horizontal position
  if (x + rect.width > viewportWidth) {
    x = viewportWidth - rect.width - 10
  }

  // Adjust vertical position
  if (y + rect.height > viewportHeight) {
    y = viewportHeight - rect.height - 10
  }

  // Ensure minimum values
  x = Math.max(10, x)
  y = Math.max(10, y)

  position.value = { x, y }
}

watch(
  () => props.modelValue,
  async (isOpen) => {
    if (isOpen) {
      position.value = { x: props.x, y: props.y }
      await nextTick()
      adjustPosition()
    }
  }
)

async function handleAddToPlaylist(playlistId: string, playlistName: string) {
  if (isAdding.value) return

  isAdding.value = playlistId
  try {
    await playlistStore.addSongToPlaylist(playlistId, props.songId)
    emit('added', playlistId, playlistName)
    emit('update:modelValue', false)
  } catch {
    // Error handled by store
  } finally {
    isAdding.value = null
  }
}

function handleCreateNew() {
  emit('createNew')
  emit('update:modelValue', false)
}

function handleClickOutside(event: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(event.target as Node)) {
    emit('update:modelValue', false)
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    emit('update:modelValue', false)
  }
}

function handleScroll() {
  emit('update:modelValue', false)
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-fast"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition-all duration-fast"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="modelValue"
        ref="menuRef"
        class="fixed z-50 min-w-[200px] max-w-[280px] rounded-lg border border-bg-tertiary bg-bg-primary py-1 shadow-lg"
        :style="{
          left: `${position.x}px`,
          top: `${position.y}px`,
        }"
        role="menu"
      >
        <!-- Header -->
        <div class="border-b border-bg-tertiary px-3 py-2">
          <p class="text-small font-medium text-text-primary">Add to playlist</p>
        </div>

        <!-- Loading state -->
        <div
          v-if="isLoading && playlists.length === 0"
          class="px-3 py-4 text-center"
        >
          <svg
            class="mx-auto h-5 w-5 animate-spin text-text-muted"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>

        <!-- Playlist list -->
        <div
          v-else
          class="max-h-[300px] overflow-y-auto py-1"
        >
          <!-- Create new playlist option -->
          <button
            type="button"
            class="flex w-full items-center gap-2 px-3 py-2 text-left text-small text-accent-primary transition-colors hover:bg-bg-secondary"
            role="menuitem"
            @click="handleCreateNew"
          >
            <svg
              class="h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 4.5v15m7.5-7.5h-15"
              />
            </svg>
            Create new playlist
          </button>

          <!-- Divider -->
          <div
            v-if="playlists.length > 0"
            class="my-1 h-px bg-bg-tertiary"
            role="separator"
          />

          <!-- Empty state -->
          <div
            v-if="playlists.length === 0"
            class="px-3 py-2 text-center text-small text-text-muted"
          >
            No playlists yet
          </div>

          <!-- Playlist items -->
          <button
            v-for="playlist in playlists"
            :key="playlist.id"
            type="button"
            :class="[
              'flex w-full items-center gap-2 px-3 py-2 text-left text-small transition-colors',
              isAdding === playlist.id
                ? 'cursor-wait opacity-50'
                : 'text-text-primary hover:bg-bg-secondary',
            ]"
            :disabled="isAdding !== null"
            role="menuitem"
            @click="handleAddToPlaylist(playlist.id, playlist.name)"
          >
            <!-- Loading spinner or icon -->
            <svg
              v-if="isAdding === playlist.id"
              class="h-4 w-4 animate-spin"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              />
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <svg
              v-else
              class="h-4 w-4 text-text-muted"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 9l10.5-3m0 6.553v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 11-.99-3.467l2.31-.66a2.25 2.25 0 001.632-2.163zm0 0V2.25L9 5.25v10.303m0 0v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 01-.99-3.467l2.31-.66A2.25 2.25 0 009 15.553z"
              />
            </svg>
            <span class="truncate">{{ playlist.name }}</span>
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
