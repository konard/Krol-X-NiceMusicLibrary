<script setup lang="ts">
import { ref, watch } from 'vue'
import { Modal, Button, Input } from '@/components/ui'
import type { Playlist, PlaylistUpdate } from '@/types'

export interface EditPlaylistModalProps {
  modelValue: boolean
  playlist: Playlist | null
  isLoading?: boolean
}

const props = withDefaults(defineProps<EditPlaylistModalProps>(), {
  isLoading: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [id: string, data: PlaylistUpdate]
  close: []
}>()

const name = ref('')
const description = ref('')
const nameError = ref('')

function validate(): boolean {
  nameError.value = ''

  if (!name.value.trim()) {
    nameError.value = 'Playlist name is required'
    return false
  }

  if (name.value.trim().length < 1) {
    nameError.value = 'Playlist name must be at least 1 character'
    return false
  }

  if (name.value.trim().length > 100) {
    nameError.value = 'Playlist name must be less than 100 characters'
    return false
  }

  return true
}

function handleSubmit() {
  if (!validate() || !props.playlist) return

  emit('save', props.playlist.id, {
    name: name.value.trim(),
    description: description.value.trim() || undefined,
  })
}

function handleClose() {
  emit('update:modelValue', false)
  emit('close')
}

// Populate form when playlist changes
watch(
  () => props.playlist,
  (playlist) => {
    if (playlist) {
      name.value = playlist.name
      description.value = playlist.description || ''
      nameError.value = ''
    }
  },
  { immediate: true }
)
</script>

<template>
  <Modal
    :model-value="modelValue"
    title="Edit Playlist"
    size="md"
    @update:model-value="emit('update:modelValue', $event)"
    @close="handleClose"
  >
    <form
      class="space-y-4"
      @submit.prevent="handleSubmit"
    >
      <div>
        <label
          for="edit-playlist-name"
          class="mb-1 block text-small font-medium text-text-primary"
        >
          Name
        </label>
        <Input
          id="edit-playlist-name"
          v-model="name"
          placeholder="My Playlist"
          :error="nameError"
          :disabled="isLoading"
          autofocus
        />
      </div>

      <div>
        <label
          for="edit-playlist-description"
          class="mb-1 block text-small font-medium text-text-primary"
        >
          Description (optional)
        </label>
        <textarea
          id="edit-playlist-description"
          v-model="description"
          rows="3"
          placeholder="Add an optional description..."
          :disabled="isLoading"
          class="w-full rounded-lg border border-bg-tertiary bg-bg-secondary px-3 py-2 text-body text-text-primary placeholder-text-muted transition-colors focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary disabled:cursor-not-allowed disabled:opacity-50"
        />
      </div>
    </form>

    <template #footer>
      <Button
        variant="ghost"
        :disabled="isLoading"
        @click="handleClose"
      >
        Cancel
      </Button>
      <Button
        variant="primary"
        :disabled="isLoading || !name.trim()"
        @click="handleSubmit"
      >
        <svg
          v-if="isLoading"
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
        Save
      </Button>
    </template>
  </Modal>
</template>
