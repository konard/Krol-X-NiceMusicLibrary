<script setup lang="ts">
import { ref, computed } from 'vue'
import { usePlayerStore } from '@/stores'

const playerStore = usePlayerStore()

const volume = computed(() => playerStore.volume)
const isMuted = computed(() => playerStore.isMuted)
const isDragging = ref(false)
const sliderRef = ref<HTMLDivElement | null>(null)

const volumePercent = computed(() => {
  return isMuted.value ? 0 : volume.value * 100
})

// Volume icon based on level
const volumeIcon = computed(() => {
  if (isMuted.value || volume.value === 0) return 'muted'
  if (volume.value < 0.33) return 'low'
  if (volume.value < 0.67) return 'medium'
  return 'high'
})

function getVolumeFromEvent(event: MouseEvent | TouchEvent): number {
  if (!sliderRef.value) return 0

  const rect = sliderRef.value.getBoundingClientRect()
  const clientX = 'touches' in event ? event.touches[0].clientX : event.clientX
  const x = clientX - rect.left
  const percent = x / rect.width

  return Math.max(0, Math.min(1, percent))
}

function handleMouseDown(event: MouseEvent) {
  isDragging.value = true
  handleVolumeChange(event)
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

function handleMouseMove(event: MouseEvent) {
  if (isDragging.value) {
    handleVolumeChange(event)
  }
}

function handleMouseUp() {
  isDragging.value = false
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
}

function handleVolumeChange(event: MouseEvent | TouchEvent) {
  const newVolume = getVolumeFromEvent(event)
  playerStore.setVolume(newVolume)
  if (playerStore.isMuted && newVolume > 0) {
    playerStore.toggleMute()
  }
}

function handleTouchStart(event: TouchEvent) {
  isDragging.value = true
  handleVolumeChange(event)
}

function handleTouchMove(event: TouchEvent) {
  if (isDragging.value) {
    event.preventDefault()
    handleVolumeChange(event)
  }
}

function handleTouchEnd() {
  isDragging.value = false
}

function toggleMute() {
  playerStore.toggleMute()
}
</script>

<template>
  <div class="group flex items-center gap-2">
    <!-- Mute button -->
    <button
      type="button"
      class="rounded-full p-1.5 text-text-secondary transition-colors hover:bg-bg-secondary hover:text-text-primary"
      aria-label="Toggle mute"
      @click="toggleMute"
    >
      <!-- Muted -->
      <svg
        v-if="volumeIcon === 'muted'"
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
          d="M17.25 9.75L19.5 12m0 0l2.25 2.25M19.5 12l2.25-2.25M19.5 12l-2.25 2.25m-10.5-6l4.72-4.72a.75.75 0 011.28.531V18.94a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.506-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.395C2.806 8.757 3.63 8.25 4.51 8.25H6.75z"
        />
      </svg>
      <!-- Low volume -->
      <svg
        v-else-if="volumeIcon === 'low'"
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
          d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z"
          style="clip-path: inset(0 50% 0 0);"
        />
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z"
        />
      </svg>
      <!-- Medium volume -->
      <svg
        v-else-if="volumeIcon === 'medium'"
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
          d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z"
        />
      </svg>
      <!-- High volume -->
      <svg
        v-else
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
          d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z"
        />
      </svg>
    </button>

    <!-- Volume slider -->
    <div
      ref="sliderRef"
      class="relative w-20 cursor-pointer py-2 opacity-0 transition-opacity group-hover:opacity-100"
      :class="{ 'opacity-100': isDragging }"
      @mousedown="handleMouseDown"
      @touchstart.prevent="handleTouchStart"
      @touchmove="handleTouchMove"
      @touchend="handleTouchEnd"
    >
      <!-- Track background -->
      <div class="h-1 w-full rounded-full bg-bg-tertiary">
        <!-- Volume fill -->
        <div
          class="absolute left-0 top-1/2 h-1 -translate-y-1/2 rounded-full bg-text-primary"
          :style="{ width: `${volumePercent}%` }"
        />

        <!-- Handle -->
        <div
          class="absolute top-1/2 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-text-primary shadow-sm"
          :style="{ left: `${volumePercent}%` }"
        />
      </div>
    </div>
  </div>
</template>
