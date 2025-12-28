<script setup lang="ts">
import { computed } from 'vue'
import type { Song } from '@/types'
import { formatDuration, getCoverUrl } from '@/services/songs'

export interface SongRowProps {
  song: Song
  index: number
  isSelected?: boolean
  isPlaying?: boolean
}

const props = withDefaults(defineProps<SongRowProps>(), {
  isSelected: false,
  isPlaying: false,
})

const emit = defineEmits<{
  click: [song: Song]
  dblclick: [song: Song]
  contextmenu: [event: MouseEvent, song: Song]
  play: [song: Song]
  favorite: [song: Song]
  edit: [song: Song]
  delete: [song: Song]
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
  <tr
    :class="[
      'group cursor-pointer transition-colors duration-fast',
      isSelected
        ? 'bg-accent-primary/10'
        : 'hover:bg-bg-secondary',
      isPlaying && 'text-accent-primary',
    ]"
    @click="handleClick"
    @dblclick="handleDblClick"
    @contextmenu="handleContextMenu"
  >
    <!-- Index / Play indicator -->
    <td class="w-12 py-2 pl-4 pr-2 text-center">
      <div class="relative">
        <span
          :class="[
            'text-small transition-opacity group-hover:opacity-0',
            isPlaying ? 'text-accent-primary' : 'text-text-muted',
          ]"
        >
          {{ isPlaying ? '▶' : index + 1 }}
        </span>
        <button
          type="button"
          class="absolute inset-0 flex items-center justify-center opacity-0 transition-opacity group-hover:opacity-100"
          aria-label="Play"
          @click="handlePlay"
        >
          <svg
            class="h-4 w-4 text-text-primary"
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
    </td>

    <!-- Cover + Title + Artist -->
    <td class="py-2 pr-4">
      <div class="flex items-center gap-3">
        <!-- Cover art -->
        <div
          class="h-10 w-10 flex-shrink-0 overflow-hidden rounded bg-bg-tertiary"
        >
          <img
            v-if="coverUrl"
            :src="coverUrl"
            :alt="song.title"
            class="h-full w-full object-cover"
            loading="lazy"
          >
          <div
            v-else
            class="flex h-full w-full items-center justify-center"
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
        </div>

        <!-- Title + Artist -->
        <div class="min-w-0 flex-1">
          <p
            :class="[
              'truncate font-medium',
              isPlaying ? 'text-accent-primary' : 'text-text-primary',
            ]"
          >
            {{ song.title }}
          </p>
          <p class="truncate text-small text-text-secondary">
            {{ song.artist || 'Unknown Artist' }}
          </p>
        </div>
      </div>
    </td>

    <!-- Album -->
    <td class="hidden py-2 pr-4 md:table-cell">
      <span class="truncate text-text-secondary">
        {{ song.album || '-' }}
      </span>
    </td>

    <!-- Genre -->
    <td class="hidden py-2 pr-4 lg:table-cell">
      <span class="truncate text-text-secondary">
        {{ song.genre || '-' }}
      </span>
    </td>

    <!-- Play count -->
    <td class="hidden py-2 pr-4 text-right xl:table-cell">
      <span class="text-text-secondary">
        {{ song.play_count }}
      </span>
    </td>

    <!-- Duration -->
    <td class="py-2 pr-2 text-right">
      <span class="text-small text-text-secondary">
        {{ duration }}
      </span>
    </td>

    <!-- Favorite button -->
    <td class="w-10 py-2 pr-4">
      <button
        type="button"
        class="rounded p-1 transition-colors hover:bg-bg-tertiary"
        :aria-label="song.is_favorite ? 'Remove from favorites' : 'Add to favorites'"
        @click="handleFavorite"
      >
        <svg
          :class="[
            'h-4 w-4 transition-colors',
            song.is_favorite
              ? 'fill-accent-error text-accent-error'
              : 'text-text-muted hover:text-accent-error',
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
    </td>
  </tr>
</template>
