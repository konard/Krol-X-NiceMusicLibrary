<script setup lang="ts">
import { ref } from 'vue'
import { isValidAudioFile } from '@/services/songs'

export interface UploadZoneProps {
  disabled?: boolean
  accept?: string
  multiple?: boolean
}

const props = withDefaults(defineProps<UploadZoneProps>(), {
  disabled: false,
  accept: '.mp3,.flac,.ogg,.wav,.m4a,.aac,audio/*',
  multiple: true,
})

const emit = defineEmits<{
  files: [files: File[]]
}>()

const isDragging = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)

function handleDragEnter(event: DragEvent) {
  event.preventDefault()
  if (!props.disabled) {
    isDragging.value = true
  }
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
}

function handleDragLeave(event: DragEvent) {
  event.preventDefault()
  // Only set to false if we're leaving the zone entirely
  const relatedTarget = event.relatedTarget as Node | null
  const currentTarget = event.currentTarget as HTMLElement
  if (!currentTarget.contains(relatedTarget)) {
    isDragging.value = false
  }
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  isDragging.value = false

  if (props.disabled) return

  const items = event.dataTransfer?.files
  if (items) {
    processFiles(Array.from(items))
  }
}

function handleInputChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files) {
    processFiles(Array.from(target.files))
  }
  // Reset input so same file can be selected again
  target.value = ''
}

function processFiles(files: File[]) {
  const validFiles = files.filter(isValidAudioFile)
  if (validFiles.length > 0) {
    emit('files', validFiles)
  }
}

function openFileDialog() {
  if (!props.disabled) {
    inputRef.value?.click()
  }
}

// Expose method to parent
defineExpose({
  openFileDialog,
})
</script>

<template>
  <div
    :class="[
      'relative rounded-lg border-2 border-dashed p-8 text-center transition-colors duration-fast',
      isDragging
        ? 'border-accent-primary bg-accent-primary/5'
        : 'border-bg-tertiary hover:border-accent-primary/50',
      disabled && 'cursor-not-allowed opacity-50',
    ]"
    @dragenter="handleDragEnter"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
    @click="openFileDialog"
  >
    <input
      ref="inputRef"
      type="file"
      class="hidden"
      :accept="accept"
      :multiple="multiple"
      :disabled="disabled"
      @change="handleInputChange"
    >

    <div class="pointer-events-none">
      <!-- Upload icon -->
      <div
        :class="[
          'mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full transition-colors',
          isDragging ? 'bg-accent-primary/10' : 'bg-bg-secondary',
        ]"
      >
        <svg
          :class="[
            'h-8 w-8 transition-colors',
            isDragging ? 'text-accent-primary' : 'text-text-muted',
          ]"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
          />
        </svg>
      </div>

      <!-- Text -->
      <p
        :class="[
          'mb-2 text-body font-medium transition-colors',
          isDragging ? 'text-accent-primary' : 'text-text-primary',
        ]"
      >
        <span v-if="isDragging">Drop files here</span>
        <span v-else>Drag and drop audio files here</span>
      </p>
      <p class="text-small text-text-secondary">
        or <span class="cursor-pointer text-accent-primary hover:underline">browse files</span>
      </p>
      <p class="mt-2 text-caption text-text-muted">
        Supported formats: MP3, FLAC, OGG, WAV, M4A, AAC
      </p>
    </div>
  </div>
</template>
