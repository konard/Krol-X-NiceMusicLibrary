<script setup lang="ts">
import { computed } from 'vue'
import { usePlayerStore } from '@/stores'

const playerStore = usePlayerStore()

const track = computed(() => playerStore.currentTrack)

// Cover image URL
const coverUrl = computed(() => {
  if (!track.value) return null
  if (track.value.cover_url) return track.value.cover_url
  // Generate API URL for cover if file_path exists
  const baseUrl = import.meta.env.VITE_API_URL || '/api/v1'
  return `${baseUrl}/songs/${track.value.id}/cover`
})

// Placeholder SVG for missing cover
const showPlaceholder = computed(() => !track.value?.cover_url)
</script>

<template>
  <div class="flex items-center gap-3 min-w-0">
    <!-- Cover Art -->
    <div
      class="relative h-14 w-14 flex-shrink-0 rounded-lg overflow-hidden bg-bg-secondary"
    >
      <img
        v-if="coverUrl && !showPlaceholder"
        :src="coverUrl"
        :alt="track?.title || 'Album cover'"
        class="h-full w-full object-cover"
        @error="() => {}"
      >
      <div
        v-else
        class="flex h-full w-full items-center justify-center text-text-muted"
      >
        <svg
          class="h-6 w-6"
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
    </div>

    <!-- Track Info -->
    <div
      v-if="track"
      class="min-w-0 flex-1"
    >
      <p class="truncate text-sm font-medium text-text-primary">
        {{ track.title }}
      </p>
      <p class="truncate text-xs text-text-secondary">
        {{ track.artist }}
      </p>
    </div>
    <div
      v-else
      class="min-w-0 flex-1"
    >
      <p class="text-sm text-text-muted">
        No track playing
      </p>
    </div>
  </div>
</template>
