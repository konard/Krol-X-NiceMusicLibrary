<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useLibraryStore } from '@/stores/library'
import { Modal, Button } from '@/components/ui'
import UploadZone from './UploadZone.vue'
import UploadProgress from './UploadProgress.vue'

const libraryStore = useLibraryStore()
const {
  isUploadModalOpen,
  uploadQueue,
  isUploading,
  uploadProgress,
  pendingUploads,
  completedUploads,
  failedUploads,
} = storeToRefs(libraryStore)

const hasFiles = computed(() => uploadQueue.value.length > 0)
const canUpload = computed(() => pendingUploads.value.length > 0 && !isUploading.value)
const canClear = computed(() => completedUploads.value.length > 0 || failedUploads.value.length > 0)

function handleClose() {
  libraryStore.closeUploadModal()
}

function handleFiles(files: File[]) {
  libraryStore.addToUploadQueue(files)
}

function handleRemove(id: string) {
  libraryStore.removeFromUploadQueue(id)
}

function handleRetry(id: string) {
  // Reset item status and upload again
  const item = uploadQueue.value.find((i) => i.id === id)
  if (item) {
    item.status = 'pending'
    item.progress = 0
    item.error = undefined
    libraryStore.uploadFile(id)
  }
}

function handleUploadAll() {
  libraryStore.processUploadQueue()
}

function handleClearCompleted() {
  libraryStore.clearCompletedUploads()
}

function handleClearAll() {
  libraryStore.clearUploadQueue()
  libraryStore.closeUploadModal()
}
</script>

<template>
  <Modal
    v-model="isUploadModalOpen"
    title="Upload Music"
    size="lg"
    @close="handleClose"
  >
    <div class="space-y-4">
      <!-- Upload zone -->
      <UploadZone
        :disabled="isUploading"
        @files="handleFiles"
      />

      <!-- Upload queue -->
      <div
        v-if="hasFiles"
        class="space-y-2"
      >
        <div class="flex items-center justify-between">
          <h3 class="text-small font-medium text-text-primary">
            Upload Queue ({{ uploadQueue.length }})
          </h3>
          <div class="flex items-center gap-2">
            <button
              v-if="canClear"
              type="button"
              class="text-caption text-text-secondary hover:text-text-primary"
              @click="handleClearCompleted"
            >
              Clear completed
            </button>
          </div>
        </div>

        <!-- Overall progress -->
        <div
          v-if="isUploading"
          class="rounded-lg bg-bg-secondary p-3"
        >
          <div class="flex items-center justify-between text-small">
            <span class="text-text-secondary">Overall progress</span>
            <span class="font-medium text-text-primary">{{ uploadProgress }}%</span>
          </div>
          <div class="mt-2 h-2 overflow-hidden rounded-full bg-bg-tertiary">
            <div
              class="h-full rounded-full bg-accent-primary transition-all duration-normal"
              :style="{ width: `${uploadProgress}%` }"
            />
          </div>
        </div>

        <!-- File list -->
        <div class="max-h-64 space-y-2 overflow-y-auto">
          <UploadProgress
            v-for="item in uploadQueue"
            :key="item.id"
            :item="item"
            @remove="handleRemove"
            @retry="handleRetry"
          />
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-else
        class="py-4 text-center text-text-secondary"
      >
        No files selected
      </div>
    </div>

    <template #footer>
      <Button
        variant="ghost"
        @click="handleClearAll"
      >
        Cancel
      </Button>
      <Button
        variant="primary"
        :disabled="!canUpload"
        @click="handleUploadAll"
      >
        <svg
          v-if="isUploading"
          class="mr-2 h-4 w-4 animate-spin"
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
        {{ isUploading ? 'Uploading...' : `Upload ${pendingUploads.length} file(s)` }}
      </Button>
    </template>
  </Modal>
</template>
