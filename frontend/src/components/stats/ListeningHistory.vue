<script setup lang="ts">
import { computed } from 'vue'
import type { ListeningHistoryItem } from '@/types'
import { usePlayerStore } from '@/stores/player'
import { Loader } from '@/components/ui'

export interface ListeningHistoryProps {
  items: ListeningHistoryItem[]
  isLoading?: boolean
  hasMore?: boolean
  total?: number
}

const props = withDefaults(defineProps<ListeningHistoryProps>(), {
  isLoading: false,
  hasMore: false,
  total: 0,
})

const emit = defineEmits<{
  loadMore: []
}>()

const playerStore = usePlayerStore()

// Group items by date
const groupedHistory = computed(() => {
  const groups: Map<string, ListeningHistoryItem[]> = new Map()

  props.items.forEach((item) => {
    const date = new Date(item.played_at)
    const dateKey = date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })

    if (!groups.has(dateKey)) {
      groups.set(dateKey, [])
    }
    groups.get(dateKey)!.push(item)
  })

  return Array.from(groups.entries())
})

function formatTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function getRelativeDate(dateStr: string): string {
  const today = new Date()
  const date = new Date(dateStr)

  today.setHours(0, 0, 0, 0)
  date.setHours(0, 0, 0, 0)

  const diffTime = today.getTime() - date.getTime()
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  return dateStr
}

function playSong(item: ListeningHistoryItem) {
  playerStore.play(item.song)
}

function handleLoadMore() {
  emit('loadMore')
}
</script>

<template>
  <div class="card">
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-h3 text-text-primary">Listening History</h2>
      <span
        v-if="total > 0"
        class="text-caption text-text-muted"
      >
        {{ total }} plays
      </span>
    </div>

    <div
      v-if="isLoading && items.length === 0"
      class="space-y-4"
    >
      <div
        v-for="i in 5"
        :key="i"
        class="flex items-center gap-3 animate-pulse"
      >
        <div class="h-10 w-10 rounded bg-bg-secondary" />
        <div class="flex-1">
          <div class="h-4 w-3/4 rounded bg-bg-secondary" />
          <div class="mt-1 h-3 w-1/2 rounded bg-bg-secondary" />
        </div>
        <div class="h-4 w-16 rounded bg-bg-secondary" />
      </div>
    </div>

    <div
      v-else-if="items.length === 0"
      class="py-8 text-center"
    >
      <svg
        class="mx-auto h-12 w-12 text-text-muted/50"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="1"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <p class="mt-3 text-text-muted">No listening history yet</p>
      <p class="mt-1 text-caption text-text-muted">Start playing some music!</p>
    </div>

    <div
      v-else
      class="space-y-6"
    >
      <!-- Date Groups -->
      <div
        v-for="[date, dateItems] in groupedHistory"
        :key="date"
        class="space-y-2"
      >
        <!-- Date Header -->
        <h3 class="text-small font-medium text-text-secondary">
          {{ getRelativeDate(date) }}
        </h3>

        <!-- History Items -->
        <div class="space-y-1">
          <button
            v-for="item in dateItems"
            :key="item.id"
            class="flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors hover:bg-bg-secondary group"
            @click="playSong(item)"
          >
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
                  class="h-4 w-4 text-white"
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

            <!-- Status Indicators -->
            <div class="flex shrink-0 items-center gap-2">
              <!-- Completed/Skipped indicator -->
              <span
                v-if="item.skipped"
                class="text-caption text-accent-warning"
                title="Skipped"
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
                    d="M11.25 4.5l7.5 7.5-7.5 7.5m-6-15l7.5 7.5-7.5 7.5"
                  />
                </svg>
              </span>
              <span
                v-else-if="item.completed"
                class="text-caption text-accent-success"
                title="Completed"
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
                    d="M4.5 12.75l6 6 9-13.5"
                  />
                </svg>
              </span>

              <!-- Time and Duration -->
              <div class="text-right">
                <p class="text-caption text-text-muted">
                  {{ formatTime(item.played_at) }}
                </p>
                <p class="text-caption text-text-muted">
                  {{ formatDuration(item.song.duration_seconds) }}
                </p>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- Load More Button -->
      <div
        v-if="hasMore"
        class="flex justify-center pt-4"
      >
        <button
          class="flex items-center gap-2 rounded-lg bg-bg-secondary px-4 py-2 text-small text-text-primary transition-colors hover:bg-bg-tertiary disabled:opacity-50"
          :disabled="isLoading"
          @click="handleLoadMore"
        >
          <Loader
            v-if="isLoading"
            size="sm"
          />
          <span>{{ isLoading ? 'Loading...' : 'Load More' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
