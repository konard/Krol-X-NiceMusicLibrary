<script setup lang="ts">
import { computed } from 'vue'
import type { Playlist } from '@/types'

export interface PlaylistCardProps {
  playlist: Playlist
  isSelected?: boolean
}

const props = withDefaults(defineProps<PlaylistCardProps>(), {
  isSelected: false,
})

const emit = defineEmits<{
  click: [playlist: Playlist]
  dblclick: [playlist: Playlist]
  contextmenu: [event: MouseEvent, playlist: Playlist]
  play: [playlist: Playlist]
}>()

const formattedDuration = computed(() => {
  const totalSeconds = props.playlist.total_duration
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)

  if (hours > 0) {
    return `${hours} hr ${minutes} min`
  }
  return `${minutes} min`
})

function handleClick() {
  emit('click', props.playlist)
}

function handleDblClick() {
  emit('dblclick', props.playlist)
}

function handleContextMenu(event: MouseEvent) {
  event.preventDefault()
  emit('contextmenu', event, props.playlist)
}

function handlePlay(event: MouseEvent) {
  event.stopPropagation()
  emit('play', props.playlist)
}
</script>

<template>
  <div
    :class="[
      'group relative cursor-pointer rounded-lg bg-bg-secondary p-4 transition-all duration-fast',
      'hover:bg-bg-tertiary',
      isSelected && 'ring-2 ring-accent-primary',
    ]"
    @click="handleClick"
    @dblclick="handleDblClick"
    @contextmenu="handleContextMenu"
  >
    <!-- Cover Art -->
    <div class="relative mb-3 aspect-square overflow-hidden rounded-md bg-bg-tertiary">
      <img
        v-if="playlist.cover_url"
        :src="playlist.cover_url"
        :alt="playlist.name"
        class="h-full w-full object-cover"
      />
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
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M9 9l10.5-3m0 6.553v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 11-.99-3.467l2.31-.66a2.25 2.25 0 001.632-2.163zm0 0V2.25L9 5.25v10.303m0 0v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 01-.99-3.467l2.31-.66A2.25 2.25 0 009 15.553z"
          />
        </svg>
      </div>

      <!-- Play button overlay -->
      <button
        type="button"
        class="absolute bottom-2 right-2 flex h-10 w-10 items-center justify-center rounded-full bg-accent-primary text-white opacity-0 shadow-lg transition-all duration-fast group-hover:opacity-100 hover:scale-105"
        aria-label="Play playlist"
        @click="handlePlay"
      >
        <svg
          class="h-5 w-5"
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

    <!-- Info -->
    <div>
      <h3 class="truncate text-body font-medium text-text-primary">
        {{ playlist.name }}
      </h3>
      <p class="truncate text-small text-text-secondary">
        {{ playlist.song_count }} {{ playlist.song_count === 1 ? 'track' : 'tracks' }} • {{ formattedDuration }}
      </p>
    </div>
  </div>
</template>
