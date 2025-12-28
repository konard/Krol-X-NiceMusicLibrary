<script setup lang="ts">
import { computed } from 'vue'
import { usePlayerStore } from '@/stores'

const playerStore = usePlayerStore()

const isPlaying = computed(() => playerStore.isPlaying)
const isLoading = computed(() => playerStore.isLoading)
const hasTrack = computed(() => !!playerStore.currentTrack)
const hasPrevious = computed(() => playerStore.hasPrevious)
const hasNext = computed(() => playerStore.hasNext)
const isShuffled = computed(() => playerStore.isShuffled)
const repeatMode = computed(() => playerStore.repeatMode)

function handlePlayPause() {
  playerStore.togglePlay()
}

function handlePrevious() {
  playerStore.previous()
}

function handleNext() {
  playerStore.next()
}

function handleShuffle() {
  playerStore.toggleShuffle()
}

function handleRepeat() {
  playerStore.cycleRepeatMode()
}
</script>

<template>
  <div class="flex items-center justify-center gap-2">
    <!-- Shuffle -->
    <button
      type="button"
      class="rounded-full p-2 transition-colors hover:bg-bg-secondary"
      :class="{ 'text-accent-primary': isShuffled, 'text-text-secondary': !isShuffled }"
      :disabled="!hasTrack"
      aria-label="Toggle shuffle"
      @click="handleShuffle"
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
          d="M19.5 12c0-1.232-.046-2.453-.138-3.662a4.006 4.006 0 00-3.7-3.7 48.678 48.678 0 00-7.324 0 4.006 4.006 0 00-3.7 3.7c-.017.22-.032.441-.046.662M19.5 12l3-3m-3 3l3 3M19.5 12c0 1.232-.046 2.453-.138 3.662a4.006 4.006 0 01-3.7 3.7 48.656 48.656 0 01-7.324 0 4.006 4.006 0 01-3.7-3.7c-.017-.22-.032-.441-.046-.662M4.5 12l3-3m-3 3l3 3"
        />
      </svg>
    </button>

    <!-- Previous -->
    <button
      type="button"
      class="rounded-full p-2 text-text-primary transition-colors hover:bg-bg-secondary disabled:opacity-50"
      :disabled="!hasTrack || !hasPrevious"
      aria-label="Previous track"
      @click="handlePrevious"
    >
      <svg
        class="h-5 w-5"
        xmlns="http://www.w3.org/2000/svg"
        fill="currentColor"
        viewBox="0 0 24 24"
      >
        <path d="M9.195 18.44c1.25.713 2.805-.19 2.805-1.629v-2.34l6.945 3.968c1.25.714 2.805-.188 2.805-1.628V7.19c0-1.44-1.555-2.342-2.805-1.628L12 9.53v-2.34c0-1.44-1.555-2.343-2.805-1.629l-7.108 4.062c-1.26.72-1.26 2.536 0 3.256l7.108 4.061z" />
      </svg>
    </button>

    <!-- Play/Pause -->
    <button
      type="button"
      class="flex h-10 w-10 items-center justify-center rounded-full bg-text-primary text-bg-primary transition-transform hover:scale-105 active:scale-95 disabled:opacity-50"
      :disabled="!hasTrack"
      :aria-label="isPlaying ? 'Pause' : 'Play'"
      @click="handlePlayPause"
    >
      <!-- Loading spinner -->
      <svg
        v-if="isLoading"
        class="h-5 w-5 animate-spin"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        />
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      <!-- Pause icon -->
      <svg
        v-else-if="isPlaying"
        class="h-5 w-5"
        xmlns="http://www.w3.org/2000/svg"
        fill="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          fill-rule="evenodd"
          d="M6.75 5.25a.75.75 0 01.75-.75H9a.75.75 0 01.75.75v13.5a.75.75 0 01-.75.75H7.5a.75.75 0 01-.75-.75V5.25zm7.5 0A.75.75 0 0115 4.5h1.5a.75.75 0 01.75.75v13.5a.75.75 0 01-.75.75H15a.75.75 0 01-.75-.75V5.25z"
          clip-rule="evenodd"
        />
      </svg>
      <!-- Play icon -->
      <svg
        v-else
        class="h-5 w-5 ml-0.5"
        xmlns="http://www.w3.org/2000/svg"
        fill="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          fill-rule="evenodd"
          d="M4.5 5.653c0-1.426 1.529-2.33 2.779-1.643l11.54 6.348c1.295.712 1.295 2.573 0 3.285L7.28 19.991c-1.25.687-2.779-.217-2.779-1.643V5.653z"
          clip-rule="evenodd"
        />
      </svg>
    </button>

    <!-- Next -->
    <button
      type="button"
      class="rounded-full p-2 text-text-primary transition-colors hover:bg-bg-secondary disabled:opacity-50"
      :disabled="!hasTrack || !hasNext"
      aria-label="Next track"
      @click="handleNext"
    >
      <svg
        class="h-5 w-5"
        xmlns="http://www.w3.org/2000/svg"
        fill="currentColor"
        viewBox="0 0 24 24"
      >
        <path d="M5.055 7.06c-1.25-.714-2.805.189-2.805 1.628v8.123c0 1.44 1.555 2.342 2.805 1.628L12 14.471v2.34c0 1.44 1.555 2.342 2.805 1.628l7.108-4.061c1.26-.72 1.26-2.536 0-3.256L14.805 7.06C13.555 6.346 12 7.25 12 8.689v2.34L5.055 7.061z" />
      </svg>
    </button>

    <!-- Repeat -->
    <button
      type="button"
      class="relative rounded-full p-2 transition-colors hover:bg-bg-secondary"
      :class="{ 'text-accent-primary': repeatMode !== 'off', 'text-text-secondary': repeatMode === 'off' }"
      :disabled="!hasTrack"
      aria-label="Toggle repeat"
      @click="handleRepeat"
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
          d="M19.5 12c0-1.232-.046-2.453-.138-3.662a4.006 4.006 0 00-3.7-3.7 48.678 48.678 0 00-7.324 0 4.006 4.006 0 00-3.7 3.7c-.092 1.21-.138 2.43-.138 3.662m0 0c0 1.232.046 2.453.138 3.662a4.006 4.006 0 003.7 3.7 48.656 48.656 0 007.324 0 4.006 4.006 0 003.7-3.7c.092-1.21.138-2.43.138-3.662m0 0h3.75m-3.75 0l-3 3m3-3l-3-3m-9.75 0H4.5m0 0l3 3m-3-3l3-3"
        />
      </svg>
      <!-- "1" indicator for repeat one -->
      <span
        v-if="repeatMode === 'one'"
        class="absolute -right-0.5 -top-0.5 flex h-3 w-3 items-center justify-center rounded-full bg-accent-primary text-[8px] font-bold text-white"
      >
        1
      </span>
    </button>
  </div>
</template>
