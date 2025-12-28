<script setup lang="ts">
import { computed } from 'vue'
import type { Song } from '@/types'
import { formatDuration, getCoverUrl } from '@/services/songs'

export interface SongCardProps {
  song: Song
  isSelected?: boolean
  isPlaying?: boolean
}

const props = withDefaults(defineProps<SongCardProps>(), {
  isSelected: false,
  isPlaying: false,
})

const emit = defineEmits<{
  click: [song: Song]
  dblclick: [song: Song]
  contextmenu: [event: MouseEvent, song: Song]
  play: [song: Song]
  favorite: [song: Song]
}>()

const duration = computed(() => formatDuration(props.song.duration_seconds))
const coverUrl = computed(() =>
  props.song.cover_art_path ? getCoverUrl(props.song.id) : null
)

function handleClick() {
  emit('click', props.song)
}

function handleDblClick() {
  emit('dblclick', props.song)
}

function handleContextMenu(event: MouseEvent) {
  event.preventDefault()
  emit('contextmenu', event, props.song)
}

function handlePlay(event: MouseEvent) {
  event.stopPropagation()
  emit('play', props.song)
}

function handleFavorite(event: MouseEvent) {
  event.stopPropagation()
  emit('favorite', props.song)
}
</script>

<template>
  <div
    :class="[
      'group relative cursor-pointer rounded-lg p-3 transition-colors duration-fast',
      isSelected
        ? 'bg-accent-primary/10 ring-1 ring-accent-primary'
        : 'bg-bg-secondary hover:bg-bg-tertiary',
    ]"
    @click="handleClick"
    @dblclick="handleDblClick"
    @contextmenu="handleContextMenu"
  >
    <!-- Cover art -->
    <div class="relative mb-3 aspect-square overflow-hidden rounded-md bg-bg-tertiary">
      <img
        v-if="coverUrl"
        :src="coverUrl"
        :alt="song.title"
        class="h-full w-full object-cover transition-transform duration-normal group-hover:scale-105"
        loading="lazy"
      >
      <div
        v-else
        class="flex h-full w-full items-center justify-center"
      >
        <svg
          class="h-12 w-12 text-text-muted"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M9 9l10.5-3m0 6.553v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 11-.99-3.467l2.31-.66a2.25 2.25 0 001.632-2.163zm0 0V2.25L9 5.25v10.303m0 0v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 01-.99-3.467l2.31-.66A2.25 2.25 0 009 15.553z"
          />
        </svg>
      </div>

      <!-- Play button overlay -->
      <div
        class="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity duration-fast group-hover:opacity-100"
      >
        <button
          type="button"
          class="flex h-12 w-12 items-center justify-center rounded-full bg-accent-primary text-white shadow-lg transition-transform hover:scale-110"
          aria-label="Play"
          @click="handlePlay"
        >
          <svg
            class="h-6 w-6 translate-x-0.5"
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
        </button>
      </div>

      <!-- Playing indicator -->
      <div
        v-if="isPlaying"
        class="absolute bottom-2 right-2 flex items-center gap-0.5 rounded bg-accent-primary px-1.5 py-0.5"
      >
        <span class="inline-block h-2 w-0.5 animate-pulse bg-white" />
        <span class="inline-block h-3 w-0.5 animate-pulse bg-white" style="animation-delay: 150ms" />
        <span class="inline-block h-2 w-0.5 animate-pulse bg-white" style="animation-delay: 300ms" />
      </div>

      <!-- Favorite button -->
      <button
        type="button"
        class="absolute right-2 top-2 rounded-full bg-black/50 p-1.5 opacity-0 transition-all hover:bg-black/70 group-hover:opacity-100"
        :class="{ '!opacity-100': song.is_favorite }"
        :aria-label="song.is_favorite ? 'Remove from favorites' : 'Add to favorites'"
        @click="handleFavorite"
      >
        <svg
          :class="[
            'h-4 w-4 transition-colors',
            song.is_favorite
              ? 'fill-accent-error text-accent-error'
              : 'text-white hover:text-accent-error',
          ]"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          :fill="song.is_favorite ? 'currentColor' : 'none'"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
          />
        </svg>
      </button>
    </div>

    <!-- Info -->
    <div class="min-w-0">
      <p
        :class="[
          'truncate font-medium',
          isPlaying ? 'text-accent-primary' : 'text-text-primary',
        ]"
        :title="song.title"
      >
        {{ song.title }}
      </p>
      <p
        class="truncate text-small text-text-secondary"
        :title="song.artist || 'Unknown Artist'"
      >
        {{ song.artist || 'Unknown Artist' }}
      </p>
      <div class="mt-1 flex items-center justify-between text-caption text-text-muted">
        <span>{{ song.album || 'Unknown Album' }}</span>
        <span>{{ duration }}</span>
      </div>
    </div>
  </div>
</template>
