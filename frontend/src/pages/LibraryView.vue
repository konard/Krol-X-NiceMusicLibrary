<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useLibraryStore, type SortField } from '@/stores/library'
import { useUiStore } from '@/stores/ui'
import type { Song, SongUpdate } from '@/types'
import { Button, Loader, ContextMenu, ConfirmDialog } from '@/components/ui'
import type { ContextMenuItem } from '@/components/ui/ContextMenu.vue'
import {
  SongTable,
  SongCard,
  UploadModal,
  SongEditModal,
  LibraryFilters,
  UploadZone,
} from '@/components/library'

// Stores
const libraryStore = useLibraryStore()
const uiStore = useUiStore()

const {
  songs,
  isLoading,
  error,
  trackCount,
  hasMore,
  isEmpty,
  filters,
  viewMode,
  activeFiltersCount,
} = storeToRefs(libraryStore)

// Local state
const selectedSong = ref<Song | null>(null)
const playingSongId = ref<string | null>(null)

// Context menu state
const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })
const contextMenuSong = ref<Song | null>(null)

// Edit modal state
const editModalVisible = ref(false)
const editingSong = ref<Song | null>(null)
const isEditLoading = ref(false)

// Delete confirm state
const deleteConfirmVisible = ref(false)
const deletingSong = ref<Song | null>(null)
const isDeleteLoading = ref(false)

// Computed
const contextMenuItems = computed<ContextMenuItem[]>(() => {
  if (!contextMenuSong.value) return []

  return [
    { id: 'play', label: 'Play', icon: 'play' },
    { id: 'queue', label: 'Add to Queue', icon: 'queue' },
    { id: 'divider1', label: '', divider: true },
    { id: 'playlist', label: 'Add to Playlist', icon: 'playlist' },
    {
      id: 'favorite',
      label: contextMenuSong.value.is_favorite ? 'Remove from Favorites' : 'Add to Favorites',
      icon: contextMenuSong.value.is_favorite ? 'heart-filled' : 'heart',
    },
    { id: 'divider2', label: '', divider: true },
    { id: 'edit', label: 'Edit Details', icon: 'edit' },
    { id: 'delete', label: 'Delete', icon: 'delete', danger: true },
  ]
})

// Lifecycle
onMounted(() => {
  libraryStore.fetchSongs(true)
})

// Watch for error to show toast
watch(error, (newError) => {
  if (newError) {
    uiStore.showError(newError)
    libraryStore.clearError()
  }
})

// Handlers
function handleSort(field: SortField) {
  libraryStore.setSort(field)
}

function handleLoadMore() {
  libraryStore.loadMore()
}

function handleSelect(song: Song) {
  selectedSong.value = song
}

function handlePlay(song: Song) {
  playingSongId.value = song.id
  // TODO: Integrate with player store when available
  uiStore.showInfo(`Now playing: ${song.title}`)
}

function handleFavorite(song: Song) {
  libraryStore.toggleFavorite(song.id)
}

function handleContextMenu(event: MouseEvent, song: Song) {
  contextMenuSong.value = song
  contextMenuPosition.value = { x: event.clientX, y: event.clientY }
  contextMenuVisible.value = true
}

function handleContextMenuSelect(item: ContextMenuItem) {
  if (!contextMenuSong.value) return

  switch (item.id) {
    case 'play':
      handlePlay(contextMenuSong.value)
      break
    case 'queue':
      // TODO: Add to queue when player is implemented
      uiStore.showInfo('Added to queue')
      break
    case 'playlist':
      // TODO: Open playlist selector
      uiStore.showInfo('Playlist feature coming soon')
      break
    case 'favorite':
      handleFavorite(contextMenuSong.value)
      break
    case 'edit':
      handleEdit(contextMenuSong.value)
      break
    case 'delete':
      handleDeleteConfirm(contextMenuSong.value)
      break
  }

  contextMenuSong.value = null
}

function handleEdit(song: Song) {
  editingSong.value = song
  editModalVisible.value = true
}

async function handleSaveEdit(id: string, data: SongUpdate) {
  isEditLoading.value = true
  try {
    await libraryStore.updateSong(id, data)
    editModalVisible.value = false
    uiStore.showSuccess('Song updated successfully')
  } catch {
    // Error is handled by store
  } finally {
    isEditLoading.value = false
  }
}

function handleDeleteConfirm(song: Song) {
  deletingSong.value = song
  deleteConfirmVisible.value = true
}

async function handleDelete() {
  if (!deletingSong.value) return

  isDeleteLoading.value = true
  try {
    await libraryStore.deleteSong(deletingSong.value.id)
    deleteConfirmVisible.value = false
    deletingSong.value = null
    uiStore.showSuccess('Song deleted successfully')
  } catch {
    // Error is handled by store
  } finally {
    isDeleteLoading.value = false
  }
}

function handleUploadClick() {
  libraryStore.openUploadModal()
}

function handleFilesDropped(files: File[]) {
  libraryStore.addToUploadQueue(files)
  libraryStore.openUploadModal()
}

function toggleViewMode() {
  libraryStore.setViewMode(viewMode.value === 'table' ? 'grid' : 'table')
}
</script>

<template>
  <div class="animate-fade-in">
    <!-- Header -->
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-h1 text-text-primary">Library</h1>
        <p class="text-text-secondary">
          {{ trackCount }} {{ trackCount === 1 ? 'track' : 'tracks' }}
        </p>
      </div>
      <div class="flex items-center gap-3">
        <!-- View toggle -->
        <div class="flex rounded-lg border border-bg-tertiary">
          <button
            type="button"
            :class="[
              'p-2 transition-colors',
              viewMode === 'table' ? 'bg-accent-primary text-white' : 'text-text-secondary hover:text-text-primary',
            ]"
            aria-label="Table view"
            @click="viewMode === 'grid' && toggleViewMode()"
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
                d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z"
              />
            </svg>
          </button>
          <button
            type="button"
            :class="[
              'p-2 transition-colors',
              viewMode === 'grid' ? 'bg-accent-primary text-white' : 'text-text-secondary hover:text-text-primary',
            ]"
            aria-label="Grid view"
            @click="viewMode === 'table' && toggleViewMode()"
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
                d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"
              />
            </svg>
          </button>
        </div>

        <!-- Upload button -->
        <Button
          variant="primary"
          size="sm"
          @click="handleUploadClick"
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
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
            />
          </svg>
          Upload
        </Button>
      </div>
    </div>

    <!-- Filters -->
    <div class="mb-6">
      <LibraryFilters
        :filters="filters"
        :active-count="activeFiltersCount"
        @update:filters="libraryStore.setFilters"
        @clear="libraryStore.clearFilters"
      />
    </div>

    <!-- Loading state (initial) -->
    <div
      v-if="isLoading && songs.length === 0"
      class="flex items-center justify-center py-12"
    >
      <Loader size="lg" />
    </div>

    <!-- Empty state with upload zone -->
    <template v-else-if="isEmpty && activeFiltersCount === 0">
      <div class="card py-12 text-center">
        <UploadZone @files="handleFilesDropped" />
      </div>
    </template>

    <!-- Empty filtered state -->
    <template v-else-if="isEmpty && activeFiltersCount > 0">
      <div class="card py-12 text-center">
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
              d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
            />
          </svg>
        </div>
        <h3 class="text-h3 text-text-primary mb-2">No results found</h3>
        <p class="text-text-secondary mb-4">
          Try adjusting your filters or search term
        </p>
        <Button
          variant="ghost"
          @click="libraryStore.clearFilters"
        >
          Clear Filters
        </Button>
      </div>
    </template>

    <!-- Table view -->
    <template v-else-if="viewMode === 'table'">
      <SongTable
        :songs="songs"
        :is-loading="isLoading"
        :has-more="hasMore"
        :sort-by="filters.sort"
        :sort-order="filters.order"
        :selected-song-id="selectedSong?.id"
        :playing-song-id="playingSongId"
        @sort="handleSort"
        @load-more="handleLoadMore"
        @select="handleSelect"
        @play="handlePlay"
        @favorite="handleFavorite"
        @edit="handleEdit"
        @delete="handleDeleteConfirm"
        @contextmenu="handleContextMenu"
      />
    </template>

    <!-- Grid view -->
    <template v-else>
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
        <SongCard
          v-for="song in songs"
          :key="song.id"
          :song="song"
          :is-selected="selectedSong?.id === song.id"
          :is-playing="playingSongId === song.id"
          @click="handleSelect"
          @dblclick="handlePlay"
          @contextmenu="handleContextMenu"
          @play="handlePlay"
          @favorite="handleFavorite"
        />
      </div>

      <!-- Load more for grid view -->
      <div
        v-if="hasMore"
        class="mt-6 text-center"
      >
        <Button
          variant="ghost"
          :disabled="isLoading"
          @click="handleLoadMore"
        >
          <Loader
            v-if="isLoading"
            size="sm"
            class="mr-2"
          />
          Load More
        </Button>
      </div>
    </template>

    <!-- Context menu -->
    <ContextMenu
      v-model="contextMenuVisible"
      :items="contextMenuItems"
      :x="contextMenuPosition.x"
      :y="contextMenuPosition.y"
      @select="handleContextMenuSelect"
    />

    <!-- Upload modal -->
    <UploadModal />

    <!-- Edit modal -->
    <SongEditModal
      v-model="editModalVisible"
      :song="editingSong"
      :is-loading="isEditLoading"
      @save="handleSaveEdit"
      @close="editingSong = null"
    />

    <!-- Delete confirmation -->
    <ConfirmDialog
      v-model="deleteConfirmVisible"
      title="Delete Song"
      :message="`Are you sure you want to delete '${deletingSong?.title}'? This action cannot be undone.`"
      confirm-text="Delete"
      variant="danger"
      :is-loading="isDeleteLoading"
      @confirm="handleDelete"
      @cancel="deletingSong = null"
    />
  </div>
</template>
