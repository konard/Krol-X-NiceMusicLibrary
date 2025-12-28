<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { usePlaylistStore } from '@/stores/playlist'
import { useUiStore } from '@/stores/ui'
import type { Playlist, PlaylistCreate } from '@/types'
import { Button, Loader, ConfirmDialog } from '@/components/ui'
import { PlaylistCard, CreatePlaylistModal } from '@/components/playlist'
import { ref } from 'vue'

const router = useRouter()
const playlistStore = usePlaylistStore()
const uiStore = useUiStore()

const {
  playlists,
  isLoading,
  error,
  playlistCount,
  isEmpty,
  isCreateModalOpen,
} = storeToRefs(playlistStore)

const isCreating = ref(false)
const deleteConfirmVisible = ref(false)
const deletingPlaylist = ref<Playlist | null>(null)
const isDeleting = ref(false)

onMounted(() => {
  playlistStore.fetchPlaylists(true)
})

// Watch for error to show toast
watch(error, (newError) => {
  if (newError) {
    uiStore.showError(newError)
    playlistStore.clearError()
  }
})

function handlePlaylistClick(playlist: Playlist) {
  router.push(`/playlists/${playlist.id}`)
}

function handlePlaylistPlay(playlist: Playlist) {
  // TODO: Integrate with player store
  uiStore.showInfo(`Playing playlist: ${playlist.name}`)
}

function handleCreateClick() {
  playlistStore.openCreateModal()
}

async function handleCreate(data: PlaylistCreate) {
  isCreating.value = true
  try {
    const newPlaylist = await playlistStore.createPlaylist(data)
    playlistStore.closeCreateModal()
    uiStore.showSuccess('Playlist created successfully')
    router.push(`/playlists/${newPlaylist.id}`)
  } catch {
    // Error handled by store
  } finally {
    isCreating.value = false
  }
}

function handleDeleteConfirm(playlist: Playlist) {
  deletingPlaylist.value = playlist
  deleteConfirmVisible.value = true
}

async function handleDelete() {
  if (!deletingPlaylist.value) return

  isDeleting.value = true
  try {
    await playlistStore.deletePlaylist(deletingPlaylist.value.id)
    deleteConfirmVisible.value = false
    uiStore.showSuccess('Playlist deleted successfully')
  } catch {
    // Error handled by store
  } finally {
    isDeleting.value = false
    deletingPlaylist.value = null
  }
}

function handleContextMenu(event: MouseEvent, playlist: Playlist) {
  // For now, just prevent default context menu
  // TODO: Implement playlist context menu
  event.preventDefault()
  handleDeleteConfirm(playlist)
}
</script>

<template>
  <div class="animate-fade-in">
    <!-- Header -->
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-h1 text-text-primary">Playlists</h1>
        <p class="text-text-secondary">
          {{ playlistCount }} {{ playlistCount === 1 ? 'playlist' : 'playlists' }}
        </p>
      </div>
      <Button
        variant="primary"
        @click="handleCreateClick"
      >
        <svg
          class="mr-1 h-4 w-4"
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
        New Playlist
      </Button>
    </div>

    <!-- Loading state -->
    <div
      v-if="isLoading && playlists.length === 0"
      class="flex items-center justify-center py-12"
    >
      <Loader size="lg" />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="isEmpty"
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
            d="M9 9l10.5-3m0 6.553v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 11-.99-3.467l2.31-.66a2.25 2.25 0 001.632-2.163zm0 0V2.25L9 5.25v10.303m0 0v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 01-.99-3.467l2.31-.66A2.25 2.25 0 009 15.553z"
          />
        </svg>
      </div>
      <h3 class="text-h3 text-text-primary mb-2">No playlists yet</h3>
      <p class="text-text-secondary mb-4">
        Create your first playlist to organize your music
      </p>
      <Button
        variant="primary"
        @click="handleCreateClick"
      >
        Create Playlist
      </Button>
    </div>

    <!-- Grid of playlists -->
    <div
      v-else
      class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6"
    >
      <PlaylistCard
        v-for="playlist in playlists"
        :key="playlist.id"
        :playlist="playlist"
        @click="handlePlaylistClick"
        @dblclick="handlePlaylistClick"
        @play="handlePlaylistPlay"
        @contextmenu="handleContextMenu"
      />
    </div>

    <!-- Create playlist modal -->
    <CreatePlaylistModal
      v-model="isCreateModalOpen"
      :is-loading="isCreating"
      @create="handleCreate"
      @close="playlistStore.closeCreateModal()"
    />

    <!-- Delete confirmation -->
    <ConfirmDialog
      v-model="deleteConfirmVisible"
      title="Delete Playlist"
      :message="`Are you sure you want to delete '${deletingPlaylist?.name}'? This action cannot be undone.`"
      confirm-text="Delete"
      variant="danger"
      :is-loading="isDeleting"
      @confirm="handleDelete"
      @cancel="deletingPlaylist = null"
    />
  </div>
</template>
