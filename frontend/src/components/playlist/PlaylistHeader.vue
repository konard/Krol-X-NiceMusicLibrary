<script setup lang="ts">
import { computed } from 'vue'
import type { Playlist } from '@/types'
import { Button } from '@/components/ui'

export interface PlaylistHeaderProps {
  playlist: Playlist
}

const props = defineProps<PlaylistHeaderProps>()

const emit = defineEmits<{
  play: []
  edit: []
  delete: []
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
</script>

<template>
  <div class="flex flex-col gap-6 sm:flex-row sm:items-end">
    <!-- Cover Art -->
    <div class="h-48 w-48 flex-shrink-0 overflow-hidden rounded-lg bg-bg-secondary shadow-lg">
      <img
        v-if="playlist.cover_url"
        :src="playlist.cover_url"
        :alt="playlist.name"
        class="h-full w-full object-cover"
      />
      <div
        v-else
        class="flex h-full w-full items-center justify-center bg-bg-tertiary"
      >
        <svg
          class="h-20 w-20 text-text-muted"
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

    <!-- Info -->
    <div class="flex flex-1 flex-col gap-3">
      <div>
        <p class="text-small font-medium uppercase tracking-wider text-text-muted">
          Playlist
        </p>
        <h1 class="text-h1 text-text-primary">
          {{ playlist.name }}
        </h1>
        <p
          v-if="playlist.description"
          class="mt-1 text-body text-text-secondary"
        >
          {{ playlist.description }}
        </p>
        <p class="mt-2 text-small text-text-muted">
          {{ playlist.song_count }} {{ playlist.song_count === 1 ? 'track' : 'tracks' }} • {{ formattedDuration }}
        </p>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-3">
        <Button
          variant="primary"
          size="lg"
          :disabled="playlist.song_count === 0"
          @click="emit('play')"
        >
          <svg
            class="mr-2 h-5 w-5"
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
          Play
        </Button>

        <Button
          variant="ghost"
          size="md"
          aria-label="Edit playlist"
          @click="emit('edit')"
        >
          <svg
            class="h-5 w-5"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"
            />
          </svg>
        </Button>

        <Button
          variant="ghost"
          size="md"
          aria-label="Delete playlist"
          @click="emit('delete')"
        >
          <svg
            class="h-5 w-5 text-accent-error"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
            />
          </svg>
        </Button>
      </div>
    </div>
  </div>
</template>
