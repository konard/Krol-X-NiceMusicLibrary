<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { usePlaylistStore } from '@/stores/playlist'
import { useUiStore } from '@/stores/ui'
import type { Song, PlaylistUpdate } from '@/types'
import { Button, Loader, ConfirmDialog } from '@/components/ui'
import { PlaylistHeader, EditPlaylistModal } from '@/components/playlist'

const route = useRoute()
const router = useRouter()
const playlistStore = usePlaylistStore()
const uiStore = useUiStore()

const { currentPlaylist, isLoading, error } = storeToRefs(playlistStore)

const playlistId = computed(() => route.params.id as string)

// Modal states
const editModalVisible = ref(false)
const isEditing = ref(false)
const deleteConfirmVisible = ref(false)
const isDeleting = ref(false)

// Drag and drop state
const draggedIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)

onMounted(() => {
  if (playlistId.value) {
    playlistStore.fetchPlaylist(playlistId.value)
  }
})

// Watch for route changes
watch(playlistId, (newId) => {
  if (newId) {
    playlistStore.fetchPlaylist(newId)
  }
})

// Watch for error to show toast
watch(error, (newError) => {
  if (newError) {
    uiStore.showError(newError)
    playlistStore.clearError()
  }
})

function handlePlay() {
  if (!currentPlaylist.value) return
  // TODO: Integrate with player store
  uiStore.showInfo(`Playing playlist: ${currentPlaylist.value.name}`)
}

function handleEdit() {
  editModalVisible.value = true
}

async function handleSaveEdit(id: string, data: PlaylistUpdate) {
  isEditing.value = true
  try {
    await playlistStore.updatePlaylist(id, data)
    editModalVisible.value = false
    uiStore.showSuccess('Playlist updated successfully')
  } catch {
    // Error handled by store
  } finally {
    isEditing.value = false
  }
}

function handleDeleteConfirm() {
  deleteConfirmVisible.value = true
}

async function handleDelete() {
  if (!currentPlaylist.value) return

  isDeleting.value = true
  try {
    await playlistStore.deletePlaylist(currentPlaylist.value.id)
    deleteConfirmVisible.value = false
    uiStore.showSuccess('Playlist deleted successfully')
    router.push('/playlists')
  } catch {
    // Error handled by store
  } finally {
    isDeleting.value = false
  }
}

function handlePlaySong(song: Song) {
  // TODO: Integrate with player store
  uiStore.showInfo(`Now playing: ${song.title}`)
}

async function handleRemoveSong(song: Song) {
  if (!currentPlaylist.value) return

  try {
    await playlistStore.removeSongFromPlaylist(currentPlaylist.value.id, song.id)
    uiStore.showSuccess('Song removed from playlist')
  } catch {
    // Error handled by store
  }
}

// Drag and drop handlers
function handleDragStart(index: number) {
  draggedIndex.value = index
}

function handleDragOver(event: DragEvent, index: number) {
  event.preventDefault()
  dragOverIndex.value = index
}

function handleDragLeave() {
  dragOverIndex.value = null
}

async function handleDrop(index: number) {
  if (draggedIndex.value === null || draggedIndex.value === index || !currentPlaylist.value) {
    draggedIndex.value = null
    dragOverIndex.value = null
    return
  }

  const songs = [...currentPlaylist.value.songs]
  const [draggedSong] = songs.splice(draggedIndex.value, 1)
  songs.splice(index, 0, draggedSong)

  const newOrder = songs.map((s) => s.id)

  try {
    await playlistStore.reorderSongs(currentPlaylist.value.id, newOrder)
    uiStore.showSuccess('Songs reordered')
  } catch {
    // Error handled by store
  }

  draggedIndex.value = null
  dragOverIndex.value = null
}

function handleDragEnd() {
  draggedIndex.value = null
  dragOverIndex.value = null
}

function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}
</script>

<template>
  <div class="animate-fade-in">
    <!-- Loading state -->
    <div
      v-if="isLoading && !currentPlaylist"
      class="flex items-center justify-center py-12"
    >
      <Loader size="lg" />
    </div>

    <!-- Not found state -->
    <div
      v-else-if="!currentPlaylist"
      class="card py-12 text-center"
    >
      <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-bg-secondary">
        <svg
          class="h-8 w-8 text-text-muted"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
          />
        </svg>
      </div>
      <h3 class="text-h3 text-text-primary mb-2">Playlist not found</h3>
      <p class="text-text-secondary mb-4">
        The playlist you're looking for doesn't exist or has been deleted.
      </p>
      <Button
        variant="primary"
        @click="router.push('/playlists')"
      >
        Back to Playlists
      </Button>
    </div>

    <!-- Playlist content -->
    <template v-else>
      <!-- Header -->
      <div class="mb-8">
        <PlaylistHeader
          :playlist="currentPlaylist"
          @play="handlePlay"
          @edit="handleEdit"
          @delete="handleDeleteConfirm"
        />
      </div>

      <!-- Songs list -->
      <div class="card overflow-hidden">
        <!-- Table header -->
        <div class="grid grid-cols-[40px_1fr_1fr_100px_40px] gap-4 border-b border-bg-tertiary px-4 py-2 text-caption font-medium uppercase tracking-wider text-text-muted">
          <div>#</div>
          <div>Title</div>
          <div>Artist</div>
          <div class="text-right">Duration</div>
          <div></div>
        </div>

        <!-- Empty state -->
        <div
          v-if="currentPlaylist.songs.length === 0"
          class="py-12 text-center text-text-muted"
        >
          <p>No songs in this playlist yet.</p>
          <p class="mt-1 text-small">
            Add songs from your library using the context menu.
          </p>
        </div>

        <!-- Songs -->
        <div v-else>
          <div
            v-for="(song, index) in currentPlaylist.songs"
            :key="song.id"
            :class="[
              'group grid cursor-pointer grid-cols-[40px_1fr_1fr_100px_40px] gap-4 px-4 py-3 transition-colors hover:bg-bg-secondary',
              dragOverIndex === index && 'border-t-2 border-accent-primary',
              draggedIndex === index && 'opacity-50',
            ]"
            draggable="true"
            @click="handlePlaySong(song)"
            @dragstart="handleDragStart(index)"
            @dragover="handleDragOver($event, index)"
            @dragleave="handleDragLeave"
            @drop="handleDrop(index)"
            @dragend="handleDragEnd"
          >
            <!-- Index / drag handle -->
            <div class="flex items-center">
              <span class="text-small text-text-muted group-hover:hidden">
                {{ index + 1 }}
              </span>
              <svg
                class="hidden h-4 w-4 cursor-grab text-text-muted group-hover:block"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
                />
              </svg>
            </div>

            <!-- Title -->
            <div class="flex items-center gap-3 overflow-hidden">
              <div
                v-if="song.cover_art_path"
                class="h-10 w-10 flex-shrink-0 overflow-hidden rounded bg-bg-tertiary"
              >
                <img
                  :src="song.cover_art_path"
                  :alt="song.title"
                  class="h-full w-full object-cover"
                />
              </div>
              <div
                v-else
                class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded bg-bg-tertiary"
              >
                <svg
                  class="h-5 w-5 text-text-muted"
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
              </div>
              <span class="truncate text-body text-text-primary">
                {{ song.title }}
              </span>
            </div>

            <!-- Artist -->
            <div class="flex items-center overflow-hidden">
              <span class="truncate text-small text-text-secondary">
                {{ song.artist || 'Unknown Artist' }}
              </span>
            </div>

            <!-- Duration -->
            <div class="flex items-center justify-end">
              <span class="text-small text-text-muted">
                {{ formatDuration(song.duration_seconds) }}
              </span>
            </div>

            <!-- Actions -->
            <div class="flex items-center justify-end">
              <button
                type="button"
                class="rounded p-1 text-text-muted opacity-0 transition-all hover:bg-bg-tertiary hover:text-accent-error group-hover:opacity-100"
                aria-label="Remove from playlist"
                @click.stop="handleRemoveSong(song)"
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
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Edit modal -->
    <EditPlaylistModal
      v-model="editModalVisible"
      :playlist="currentPlaylist"
      :is-loading="isEditing"
      @save="handleSaveEdit"
      @close="editModalVisible = false"
    />

    <!-- Delete confirmation -->
    <ConfirmDialog
      v-model="deleteConfirmVisible"
      title="Delete Playlist"
      :message="`Are you sure you want to delete '${currentPlaylist?.name}'? This action cannot be undone.`"
      confirm-text="Delete"
      variant="danger"
      :is-loading="isDeleting"
      @confirm="handleDelete"
    />
  </div>
</template>
