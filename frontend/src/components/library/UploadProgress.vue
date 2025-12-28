<script setup lang="ts">
import { computed } from 'vue'
import type { UploadItem } from '@/stores/library'
import { formatFileSize } from '@/services/songs'

export interface UploadProgressProps {
  item: UploadItem
  showRemove?: boolean
}

const props = withDefaults(defineProps<UploadProgressProps>(), {
  showRemove: true,
})

const emit = defineEmits<{
  remove: [id: string]
  retry: [id: string]
}>()

const fileSize = computed(() => formatFileSize(props.item.file.size))

const statusText = computed(() => {
  switch (props.item.status) {
    case 'pending':
      return 'Waiting...'
    case 'uploading':
      return `${props.item.progress}%`
    case 'success':
      return 'Uploaded'
    case 'error':
      return props.item.error || 'Failed'
    default:
      return ''
  }
})

const statusColor = computed(() => {
  switch (props.item.status) {
    case 'success':
      return 'text-green-500'
    case 'error':
      return 'text-accent-error'
    default:
      return 'text-text-secondary'
  }
})

function handleRemove() {
  emit('remove', props.item.id)
}

function handleRetry() {
  emit('retry', props.item.id)
}
</script>

<template>
  <div class="flex items-center gap-3 rounded-lg bg-bg-secondary p-3">
    <!-- File icon -->
    <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-bg-tertiary">
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

    <!-- File info -->
    <div class="min-w-0 flex-1">
      <div class="flex items-center justify-between">
        <p class="truncate text-small font-medium text-text-primary">
          {{ item.file.name }}
        </p>
        <span :class="['text-caption', statusColor]">
          {{ statusText }}
        </span>
      </div>

      <!-- Progress bar -->
      <div
        v-if="item.status === 'uploading' || item.status === 'pending'"
        class="mt-2"
      >
        <div class="h-1 overflow-hidden rounded-full bg-bg-tertiary">
          <div
            class="h-full rounded-full bg-accent-primary transition-all duration-normal"
            :style="{ width: `${item.progress}%` }"
          />
        </div>
      </div>

      <!-- File size -->
      <p class="mt-1 text-caption text-text-muted">
        {{ fileSize }}
      </p>
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-1">
      <!-- Success icon -->
      <div
        v-if="item.status === 'success'"
        class="flex h-8 w-8 items-center justify-center"
      >
        <svg
          class="h-5 w-5 text-green-500"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z"
            clip-rule="evenodd"
          />
        </svg>
      </div>

      <!-- Retry button -->
      <button
        v-if="item.status === 'error'"
        type="button"
        class="flex h-8 w-8 items-center justify-center rounded-lg text-text-secondary transition-colors hover:bg-bg-tertiary hover:text-text-primary"
        aria-label="Retry upload"
        @click="handleRetry"
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
            d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
          />
        </svg>
      </button>

      <!-- Remove button -->
      <button
        v-if="showRemove && item.status !== 'uploading'"
        type="button"
        class="flex h-8 w-8 items-center justify-center rounded-lg text-text-secondary transition-colors hover:bg-bg-tertiary hover:text-accent-error"
        aria-label="Remove"
        @click="handleRemove"
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

      <!-- Uploading spinner -->
      <div
        v-if="item.status === 'uploading'"
        class="flex h-8 w-8 items-center justify-center"
      >
        <svg
          class="h-5 w-5 animate-spin text-accent-primary"
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
      </div>
    </div>
  </div>
</template>
