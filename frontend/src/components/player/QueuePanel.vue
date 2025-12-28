<script setup lang="ts">
import { computed } from 'vue'
import { usePlayerStore, useUiStore } from '@/stores'

const playerStore = usePlayerStore()
const uiStore = useUiStore()

const queue = computed(() => playerStore.queue)
const queueIndex = computed(() => playerStore.queueIndex)
const isVisible = computed(() => uiStore.isQueueVisible)

function handleClose() {
  uiStore.toggleQueue()
}

function handlePlayTrack(index: number) {
  playerStore.playFromQueue(index)
}

function handleRemoveTrack(index: number) {
  playerStore.removeFromQueue(index)
}

function handleClearQueue() {
  playerStore.clearQueue()
  uiStore.toggleQueue()
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<template>
  <Transition name="slide">
    <div
      v-if="isVisible"
      class="fixed bottom-[var(--player-height)] right-0 z-40 flex h-96 w-80 flex-col border-l border-t border-bg-tertiary bg-bg-primary shadow-lg"
    >
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-bg-tertiary px-4 py-3">
        <h3 class="text-sm font-medium text-text-primary">
          Queue
          <span class="ml-1 text-text-secondary">({{ queue.length }})</span>
        </h3>
        <div class="flex items-center gap-2">
          <button
            v-if="queue.length > 0"
            type="button"
            class="text-xs text-text-secondary hover:text-accent-error"
            @click="handleClearQueue"
          >
            Clear
          </button>
          <button
            type="button"
            class="rounded-full p-1 text-text-secondary transition-colors hover:bg-bg-secondary hover:text-text-primary"
            aria-label="Close queue"
            @click="handleClose"
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
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- Queue list -->
      <div class="flex-1 overflow-y-auto scrollbar-thin">
        <div
          v-if="queue.length === 0"
          class="flex h-full items-center justify-center"
        >
          <p class="text-sm text-text-muted">
            Queue is empty
          </p>
        </div>

        <ul v-else>
          <li
            v-for="(track, index) in queue"
            :key="`${track.id}-${index}`"
            class="group flex items-center gap-3 border-b border-bg-tertiary px-4 py-2 transition-colors hover:bg-bg-secondary"
            :class="{ 'bg-accent-primary/10': index === queueIndex }"
          >
            <!-- Track number / Play indicator -->
            <div class="flex h-6 w-6 flex-shrink-0 items-center justify-center">
              <span
                v-if="index === queueIndex"
                class="text-accent-primary"
              >
                <svg
                  class="h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    d="M13.5 4.06c0-1.336-1.616-2.005-2.56-1.06l-4.5 4.5H4.508c-1.141 0-2.318.664-2.66 1.905A9.76 9.76 0 001.5 12c0 .898.121 1.768.35 2.595.341 1.24 1.518 1.905 2.659 1.905h1.93l4.5 4.5c.945.945 2.561.276 2.561-1.06V4.06zM18.584 5.106a.75.75 0 011.06 0c3.808 3.807 3.808 9.98 0 13.788a.75.75 0 01-1.06-1.06 8.25 8.25 0 000-11.668.75.75 0 010-1.06z"
                  />
                  <path
                    d="M15.932 7.757a.75.75 0 011.061 0 6 6 0 010 8.486.75.75 0 01-1.06-1.061 4.5 4.5 0 000-6.364.75.75 0 010-1.06z"
                  />
                </svg>
              </span>
              <span
                v-else
                class="text-xs text-text-muted group-hover:hidden"
              >
                {{ index + 1 }}
              </span>
              <button
                v-if="index !== queueIndex"
                type="button"
                class="hidden text-text-primary group-hover:block"
                aria-label="Play track"
                @click="handlePlayTrack(index)"
              >
                <svg
                  class="h-4 w-4"
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
            </div>

            <!-- Track info -->
            <div class="min-w-0 flex-1">
              <p
                class="truncate text-sm"
                :class="index === queueIndex ? 'text-accent-primary font-medium' : 'text-text-primary'"
              >
                {{ track.title }}
              </p>
              <p class="truncate text-xs text-text-secondary">
                {{ track.artist }}
              </p>
            </div>

            <!-- Duration -->
            <span class="flex-shrink-0 text-xs tabular-nums text-text-muted">
              {{ formatDuration(track.duration) }}
            </span>

            <!-- Remove button -->
            <button
              type="button"
              class="flex-shrink-0 rounded-full p-1 text-text-muted opacity-0 transition-opacity hover:bg-bg-tertiary hover:text-accent-error group-hover:opacity-100"
              aria-label="Remove from queue"
              @click.stop="handleRemoveTrack(index)"
            >
              <svg
                class="h-3.5 w-3.5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </li>
        </ul>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
