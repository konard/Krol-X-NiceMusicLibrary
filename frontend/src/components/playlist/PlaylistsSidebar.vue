<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { usePlaylistStore } from '@/stores/playlist'

export interface PlaylistsSidebarProps {
  isExpanded?: boolean
}

withDefaults(defineProps<PlaylistsSidebarProps>(), {
  isExpanded: true,
})

const router = useRouter()
const route = useRoute()
const playlistStore = usePlaylistStore()

const { playlists, isLoading } = storeToRefs(playlistStore)

onMounted(() => {
  if (playlists.value.length === 0) {
    playlistStore.fetchPlaylists(true)
  }
})

function isActive(playlistId: string): boolean {
  return route.path === `/playlists/${playlistId}`
}

function navigateToPlaylist(playlistId: string) {
  router.push(`/playlists/${playlistId}`)
}

function handleCreatePlaylist() {
  playlistStore.openCreateModal()
}
</script>

<template>
  <div class="mb-4">
    <!-- Header -->
    <div class="mb-2 flex items-center justify-between px-3">
      <p
        v-if="isExpanded"
        class="text-caption font-medium uppercase tracking-wider text-text-muted"
      >
        Playlists
      </p>
      <button
        type="button"
        class="rounded p-1 text-text-muted transition-colors hover:bg-bg-secondary hover:text-text-primary"
        :title="isExpanded ? 'Create playlist' : 'Playlists'"
        aria-label="Create playlist"
        @click="handleCreatePlaylist"
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
      </button>
    </div>

    <!-- Loading state -->
    <div
      v-if="isLoading && playlists.length === 0"
      class="px-3 py-2"
    >
      <div class="h-6 w-24 animate-pulse rounded bg-bg-tertiary" />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="playlists.length === 0"
      class="px-3 py-2"
    >
      <p
        v-if="isExpanded"
        class="text-small text-text-muted"
      >
        No playlists yet
      </p>
    </div>

    <!-- Playlist items -->
    <div
      v-else
      class="space-y-0.5"
    >
      <button
        v-for="playlist in playlists"
        :key="playlist.id"
        type="button"
        :class="[
          'flex w-full items-center gap-3 rounded-lg px-3 py-2 transition-colors duration-fast',
          isActive(playlist.id)
            ? 'bg-accent-primary/10 text-accent-primary'
            : 'text-text-secondary hover:bg-bg-secondary hover:text-text-primary',
        ]"
        :title="!isExpanded ? playlist.name : undefined"
        @click="navigateToPlaylist(playlist.id)"
      >
        <!-- Playlist icon -->
        <svg
          class="h-5 w-5 flex-shrink-0"
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

        <span
          v-if="isExpanded"
          class="truncate text-small font-medium"
        >
          {{ playlist.name }}
        </span>
      </button>
    </div>

    <!-- View all link -->
    <router-link
      v-if="playlists.length > 0 && isExpanded"
      to="/playlists"
      class="mt-2 flex items-center gap-2 px-3 py-1 text-small text-text-muted transition-colors hover:text-accent-primary"
    >
      View all playlists
    </router-link>
  </div>
</template>
