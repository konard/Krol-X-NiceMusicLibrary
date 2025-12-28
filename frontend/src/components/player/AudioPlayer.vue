<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue'
import { usePlayerStore, useUiStore } from '@/stores'
import { useKeyboard } from '@/composables'
import NowPlaying from './NowPlaying.vue'
import PlayerControls from './PlayerControls.vue'
import ProgressBar from './ProgressBar.vue'
import VolumeControl from './VolumeControl.vue'
import QueuePanel from './QueuePanel.vue'

const playerStore = usePlayerStore()
const uiStore = useUiStore()

const hasTrack = computed(() => !!playerStore.currentTrack)
const isQueueVisible = computed(() => uiStore.isQueueVisible)
const isMobile = computed(() => uiStore.isMobile)

// Initialize audio on mount
onMounted(() => {
  playerStore.initAudio()
})

// Cleanup on unmount
onUnmounted(() => {
  playerStore.cleanup()
})

// Keyboard shortcuts for player
useKeyboard([
  {
    key: ' ',
    handler: () => {
      if (hasTrack.value) {
        playerStore.togglePlay()
      }
    },
    description: 'Play/Pause',
  },
  {
    key: 'ArrowLeft',
    handler: () => {
      if (hasTrack.value) {
        playerStore.seek(playerStore.currentTime - 10)
      }
    },
    description: 'Seek backward 10s',
  },
  {
    key: 'ArrowRight',
    handler: () => {
      if (hasTrack.value) {
        playerStore.seek(playerStore.currentTime + 10)
      }
    },
    description: 'Seek forward 10s',
  },
  {
    key: 'ArrowUp',
    handler: () => {
      playerStore.setVolume(playerStore.volume + 0.1)
    },
    description: 'Volume up',
  },
  {
    key: 'ArrowDown',
    handler: () => {
      playerStore.setVolume(playerStore.volume - 0.1)
    },
    description: 'Volume down',
  },
  {
    key: 'm',
    handler: () => {
      playerStore.toggleMute()
    },
    description: 'Toggle mute',
  },
  {
    key: 's',
    handler: () => {
      if (hasTrack.value) {
        playerStore.toggleShuffle()
      }
    },
    description: 'Toggle shuffle',
  },
  {
    key: 'r',
    handler: () => {
      if (hasTrack.value) {
        playerStore.cycleRepeatMode()
      }
    },
    description: 'Cycle repeat mode',
  },
  {
    key: 'n',
    handler: () => {
      if (hasTrack.value) {
        playerStore.next()
      }
    },
    description: 'Next track',
  },
  {
    key: 'p',
    handler: () => {
      if (hasTrack.value) {
        playerStore.previous()
      }
    },
    description: 'Previous track',
  },
  {
    key: 'q',
    handler: () => {
      uiStore.toggleQueue()
    },
    description: 'Toggle queue',
  },
])

function toggleQueue() {
  uiStore.toggleQueue()
}
</script>

<template>
  <!-- Desktop Player -->
  <div
    v-if="!isMobile"
    class="fixed bottom-0 left-0 right-0 z-30 flex h-[var(--player-height)] items-center border-t border-bg-tertiary bg-player-bg px-4"
    :class="{ 'pl-sidebar-collapsed': !uiStore.isSidebarExpanded, 'pl-sidebar-expanded': uiStore.isSidebarExpanded }"
    style="transition: padding-left 0.2s ease;"
  >
    <!-- Left section: Now Playing -->
    <div class="flex w-1/4 min-w-0">
      <NowPlaying />
    </div>

    <!-- Center section: Controls & Progress -->
    <div class="flex flex-1 flex-col items-center gap-1 px-4">
      <PlayerControls />
      <ProgressBar class="max-w-xl" />
    </div>

    <!-- Right section: Volume & Queue -->
    <div class="flex w-1/4 items-center justify-end gap-4">
      <VolumeControl />

      <!-- Queue toggle button -->
      <button
        type="button"
        class="rounded-full p-2 transition-colors"
        :class="{
          'bg-accent-primary/10 text-accent-primary': isQueueVisible,
          'text-text-secondary hover:bg-bg-secondary hover:text-text-primary': !isQueueVisible
        }"
        aria-label="Toggle queue"
        @click="toggleQueue"
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
    </div>
  </div>

  <!-- Mobile Player (Mini) -->
  <div
    v-else
    class="fixed bottom-0 left-0 right-0 z-30 flex h-[var(--player-height)] flex-col border-t border-bg-tertiary bg-player-bg"
  >
    <!-- Progress bar at top -->
    <div class="h-1 w-full bg-bg-tertiary">
      <div
        class="h-full bg-player-progress transition-all"
        :style="{ width: `${playerStore.progress}%` }"
      />
    </div>

    <!-- Player content -->
    <div class="flex flex-1 items-center gap-3 px-3">
      <!-- Now Playing (compact) -->
      <NowPlaying class="flex-1" />

      <!-- Play/Pause button -->
      <button
        type="button"
        class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-text-primary text-bg-primary"
        :disabled="!hasTrack"
        :aria-label="playerStore.isPlaying ? 'Pause' : 'Play'"
        @click="playerStore.togglePlay()"
      >
        <!-- Loading -->
        <svg
          v-if="playerStore.isLoading"
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
        <!-- Pause -->
        <svg
          v-else-if="playerStore.isPlaying"
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
        <!-- Play -->
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

      <!-- Time display -->
      <span class="flex-shrink-0 text-xs tabular-nums text-text-secondary">
        {{ playerStore.formattedCurrentTime }}
      </span>
    </div>
  </div>

  <!-- Queue Panel -->
  <QueuePanel />
</template>

<style scoped>
.pl-sidebar-collapsed {
  padding-left: calc(var(--sidebar-width-collapsed) + 1rem);
}

.pl-sidebar-expanded {
  padding-left: calc(var(--sidebar-width-expanded) + 1rem);
}
</style>
