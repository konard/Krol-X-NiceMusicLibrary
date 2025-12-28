<script setup lang="ts">
import { ref, computed } from 'vue'
import { usePlayerStore } from '@/stores'

const playerStore = usePlayerStore()

const isDragging = ref(false)
const hoverProgress = ref(0)
const isHovering = ref(false)

const progress = computed(() => playerStore.progress)
const bufferedProgress = computed(() => playerStore.bufferedProgress)
const currentTime = computed(() => playerStore.formattedCurrentTime)
const duration = computed(() => playerStore.formattedDuration)
const hasTrack = computed(() => !!playerStore.currentTrack)

const progressBarRef = ref<HTMLDivElement | null>(null)

function getProgressFromEvent(event: MouseEvent | TouchEvent): number {
  if (!progressBarRef.value) return 0

  const rect = progressBarRef.value.getBoundingClientRect()
  const clientX = 'touches' in event ? event.touches[0].clientX : event.clientX
  const x = clientX - rect.left
  const percent = (x / rect.width) * 100

  return Math.max(0, Math.min(100, percent))
}

function handleMouseDown(event: MouseEvent) {
  if (!hasTrack.value) return
  isDragging.value = true
  handleSeek(event)
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

function handleMouseMove(event: MouseEvent) {
  if (isDragging.value) {
    handleSeek(event)
  }
}

function handleMouseUp() {
  isDragging.value = false
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
}

function handleSeek(event: MouseEvent | TouchEvent) {
  const percent = getProgressFromEvent(event)
  playerStore.seekByPercent(percent)
}

function handleHover(event: MouseEvent) {
  if (!hasTrack.value) return
  isHovering.value = true
  hoverProgress.value = getProgressFromEvent(event)
}

function handleMouseLeave() {
  isHovering.value = false
}

// Touch events
function handleTouchStart(event: TouchEvent) {
  if (!hasTrack.value) return
  isDragging.value = true
  handleSeek(event)
}

function handleTouchMove(event: TouchEvent) {
  if (isDragging.value) {
    event.preventDefault()
    handleSeek(event)
  }
}

function handleTouchEnd() {
  isDragging.value = false
}

// Hover time preview
const hoverTime = computed(() => {
  if (!hasTrack.value || playerStore.duration === 0) return '0:00'
  const seconds = (hoverProgress.value / 100) * playerStore.duration
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
})
</script>

<template>
  <div class="flex w-full items-center gap-2">
    <!-- Current time -->
    <span class="w-10 text-right text-xs tabular-nums text-text-secondary">
      {{ currentTime }}
    </span>

    <!-- Progress bar container -->
    <div
      ref="progressBarRef"
      class="group relative flex-1 cursor-pointer py-2"
      :class="{ 'cursor-not-allowed opacity-50': !hasTrack }"
      @mousedown="handleMouseDown"
      @mousemove="handleHover"
      @mouseleave="handleMouseLeave"
      @touchstart.prevent="handleTouchStart"
      @touchmove="handleTouchMove"
      @touchend="handleTouchEnd"
    >
      <!-- Track background -->
      <div class="h-1 w-full rounded-full bg-bg-tertiary transition-all group-hover:h-1.5">
        <!-- Buffered progress -->
        <div
          class="absolute left-0 top-1/2 h-1 -translate-y-1/2 rounded-full bg-bg-secondary transition-all group-hover:h-1.5"
          :style="{ width: `${bufferedProgress}%` }"
        />

        <!-- Progress fill -->
        <div
          class="absolute left-0 top-1/2 h-1 -translate-y-1/2 rounded-full transition-all group-hover:h-1.5"
          :class="isDragging ? 'bg-accent-primary' : 'bg-player-progress'"
          :style="{ width: `${progress}%` }"
        />

        <!-- Seek handle -->
        <div
          class="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-text-primary opacity-0 shadow-md transition-opacity group-hover:opacity-100"
          :class="{ 'opacity-100': isDragging }"
          :style="{ left: `${progress}%` }"
        />
      </div>

      <!-- Hover time tooltip -->
      <div
        v-if="isHovering && hasTrack && !isDragging"
        class="absolute -top-6 -translate-x-1/2 rounded bg-bg-secondary px-1.5 py-0.5 text-xs text-text-primary shadow-md"
        :style="{ left: `${hoverProgress}%` }"
      >
        {{ hoverTime }}
      </div>
    </div>

    <!-- Duration -->
    <span class="w-10 text-xs tabular-nums text-text-secondary">
      {{ duration }}
    </span>
  </div>
</template>
