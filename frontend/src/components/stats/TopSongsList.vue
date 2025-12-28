<script setup lang="ts">
import { computed } from 'vue'
import type { TopSongItem } from '@/types'
import { usePlayerStore } from '@/stores/player'

export interface TopSongsListProps {
  songs: TopSongItem[]
  isLoading?: boolean
  limit?: number
}

const props = withDefaults(defineProps<TopSongsListProps>(), {
  isLoading: false,
  limit: 5,
})

const playerStore = usePlayerStore()

const displayedSongs = computed(() => props.songs.slice(0, props.limit))

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function playSong(song: TopSongItem['song']) {
  playerStore.play(song)
}
</script>

<template>
  <div class="card">
    <h2 class="text-h3 text-text-primary mb-4">Top Tracks</h2>

    <div
      v-if="isLoading"
      class="space-y-3"
    >
      <div
        v-for="i in limit"
        :key="i"
        class="flex items-center gap-3 animate-pulse"
      >
        <div class="flex h-10 w-10 items-center justify-center rounded bg-bg-secondary text-text-muted">
          {{ i }}
        </div>
        <div class="flex-1">
          <div class="h-4 w-3/4 rounded bg-bg-secondary" />
          <div class="mt-1 h-3 w-1/2 rounded bg-bg-secondary" />
        </div>
      </div>
    </div>

    <div
      v-else-if="songs.length === 0"
      class="py-8 text-center"
    >
      <p class="text-text-muted">No listening data yet</p>
    </div>

    <div
      v-else
      class="space-y-2"
    >
      <button
        v-for="(item, index) in displayedSongs"
        :key="item.song.id"
        class="flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors hover:bg-bg-secondary group"
        @click="playSong(item.song)"
      >
        <!-- Rank -->
        <div
          class="flex h-8 w-8 shrink-0 items-center justify-center rounded text-small font-medium"
          :class="[
            index === 0 ? 'bg-accent-primary/20 text-accent-primary' :
            index === 1 ? 'bg-accent-secondary/20 text-accent-secondary' :
            index === 2 ? 'bg-accent-success/20 text-accent-success' :
            'bg-bg-secondary text-text-muted'
          ]"
        >
          {{ index + 1 }}
        </div>

        <!-- Cover Art -->
        <div class="relative h-10 w-10 shrink-0 overflow-hidden rounded bg-bg-secondary">
          <img
            v-if="item.song.cover_art_path"
            :src="item.song.cover_art_path"
            :alt="item.song.title"
            class="h-full w-full object-cover"
          />
          <div
            v-else
            class="flex h-full w-full items-center justify-center text-text-muted"
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
                d="M9 9l10.5-3m0 6.553v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 11-.99-3.467l2.31-.66a2.25 2.25 0 001.632-2.163zm0 0V2.25L9 5.25v10.303m0 0v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 01-.99-3.467l2.31-.66A2.25 2.25 0 009 15.553z"
              />
            </svg>
          </div>

          <!-- Play overlay -->
          <div class="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100">
            <svg
              class="h-5 w-5 text-white"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M4.5 5.653c0-1.426 1.529-2.33 2.779-1.643l11.54 6.348c1.295.712 1.295 2.573 0 3.285L7.28 19.991c-1.25.687-2.779-.217-2.779-1.643V5.653z"
                clip-rule="evenodd"
              />
            </svg>
          </div>
        </div>

        <!-- Song Info -->
        <div class="min-w-0 flex-1">
          <p class="truncate text-small font-medium text-text-primary">
            {{ item.song.title }}
          </p>
          <p class="truncate text-caption text-text-muted">
            {{ item.song.artist || 'Unknown Artist' }}
          </p>
        </div>

        <!-- Play Count & Duration -->
        <div class="shrink-0 text-right">
          <p class="text-small font-medium text-accent-primary">
            {{ item.play_count }}x
          </p>
          <p class="text-caption text-text-muted">
            {{ formatDuration(item.song.duration_seconds) }}
          </p>
        </div>
      </button>
    </div>
  </div>
</template>
