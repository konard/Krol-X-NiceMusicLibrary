<script setup lang="ts">
import { ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useTagStore, TAG_COLORS } from '@/stores/tag'
import type { Tag } from '@/types'
import { Modal, Button, Input } from '@/components/ui'

export interface ManageTagsModalProps {
  modelValue: boolean
}

const props = defineProps<ManageTagsModalProps>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  close: []
}>()

const tagStore = useTagStore()
const { sortedTags, isLoading } = storeToRefs(tagStore)

const newTagName = ref('')
const newTagColor = ref(TAG_COLORS[0])
const editingTag = ref<Tag | null>(null)
const editName = ref('')
const editColor = ref('')
const isCreating = ref(false)
const isSaving = ref(false)
const isDeleting = ref<string | null>(null)
const error = ref('')

// Fetch tags when modal opens
watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      tagStore.fetchTags()
      newTagName.value = ''
      newTagColor.value = TAG_COLORS[sortedTags.value.length % TAG_COLORS.length]
      editingTag.value = null
      error.value = ''
    }
  }
)

function handleClose() {
  emit('update:modelValue', false)
  emit('close')
}

async function handleCreateTag() {
  if (!newTagName.value.trim()) {
    error.value = 'Tag name is required'
    return
  }

  if (sortedTags.value.some((t) => t.name.toLowerCase() === newTagName.value.toLowerCase())) {
    error.value = 'A tag with this name already exists'
    return
  }

  isCreating.value = true
  error.value = ''

  try {
    await tagStore.createTag({
      name: newTagName.value.trim(),
      color: newTagColor.value,
    })
    newTagName.value = ''
    newTagColor.value = TAG_COLORS[(sortedTags.value.length + 1) % TAG_COLORS.length]
  } catch (e) {
    error.value = (e as { message: string }).message || 'Failed to create tag'
  } finally {
    isCreating.value = false
  }
}

function startEditing(tag: Tag) {
  editingTag.value = tag
  editName.value = tag.name
  editColor.value = tag.color
  error.value = ''
}

function cancelEditing() {
  editingTag.value = null
  editName.value = ''
  editColor.value = ''
}

async function handleSaveEdit() {
  if (!editingTag.value) return

  if (!editName.value.trim()) {
    error.value = 'Tag name is required'
    return
  }

  if (
    sortedTags.value.some(
      (t) =>
        t.id !== editingTag.value?.id &&
        t.name.toLowerCase() === editName.value.toLowerCase()
    )
  ) {
    error.value = 'A tag with this name already exists'
    return
  }

  isSaving.value = true
  error.value = ''

  try {
    await tagStore.updateTag(editingTag.value.id, {
      name: editName.value.trim(),
      color: editColor.value,
    })
    editingTag.value = null
    editName.value = ''
    editColor.value = ''
  } catch (e) {
    error.value = (e as { message: string }).message || 'Failed to update tag'
  } finally {
    isSaving.value = false
  }
}

async function handleDeleteTag(tagId: string) {
  isDeleting.value = tagId
  error.value = ''

  try {
    await tagStore.deleteTag(tagId)
  } catch (e) {
    error.value = (e as { message: string }).message || 'Failed to delete tag'
  } finally {
    isDeleting.value = null
  }
}
</script>

<template>
  <Modal
    :model-value="modelValue"
    title="Manage Tags"
    size="lg"
    @update:model-value="emit('update:modelValue', $event)"
    @close="handleClose"
  >
    <div class="space-y-4">
      <!-- Error message -->
      <div
        v-if="error"
        class="rounded-lg bg-accent-error/10 px-3 py-2 text-small text-accent-error"
      >
        {{ error }}
      </div>

      <!-- Create new tag form -->
      <div class="flex items-end gap-2">
        <div class="flex-1">
          <label class="mb-1 block text-small font-medium text-text-primary">
            New Tag
          </label>
          <Input
            v-model="newTagName"
            placeholder="Tag name"
            :disabled="isCreating"
            @keydown.enter="handleCreateTag"
          />
        </div>

        <!-- Color picker -->
        <div>
          <label class="mb-1 block text-small font-medium text-text-primary">
            Color
          </label>
          <div class="flex gap-1">
            <button
              v-for="color in TAG_COLORS"
              :key="color"
              type="button"
              :class="[
                'h-8 w-8 rounded-md border-2 transition-transform hover:scale-110',
                newTagColor === color ? 'border-text-primary' : 'border-transparent',
              ]"
              :style="{ backgroundColor: color }"
              :disabled="isCreating"
              @click="newTagColor = color"
            />
          </div>
        </div>

        <Button
          variant="primary"
          :disabled="isCreating || !newTagName.trim()"
          @click="handleCreateTag"
        >
          <svg
            v-if="isCreating"
            class="mr-1 h-4 w-4 animate-spin"
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
          Add
        </Button>
      </div>

      <!-- Tags list -->
      <div class="rounded-lg border border-bg-tertiary">
        <!-- Loading state -->
        <div
          v-if="isLoading && sortedTags.length === 0"
          class="flex justify-center py-8"
        >
          <svg
            class="h-6 w-6 animate-spin text-text-muted"
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

        <!-- Empty state -->
        <div
          v-else-if="sortedTags.length === 0"
          class="py-8 text-center text-text-muted"
        >
          No tags yet. Create your first tag above.
        </div>

        <!-- Tags list -->
        <div
          v-else
          class="max-h-64 divide-y divide-bg-tertiary overflow-y-auto"
        >
          <div
            v-for="tag in sortedTags"
            :key="tag.id"
            class="flex items-center gap-3 p-3"
          >
            <!-- Editing mode -->
            <template v-if="editingTag?.id === tag.id">
              <input
                v-model="editName"
                type="text"
                class="flex-1 rounded-md border border-bg-tertiary bg-bg-secondary px-2 py-1 text-small text-text-primary focus:border-accent-primary focus:outline-none"
                :disabled="isSaving"
              />

              <div class="flex gap-1">
                <button
                  v-for="color in TAG_COLORS"
                  :key="color"
                  type="button"
                  :class="[
                    'h-6 w-6 rounded border-2 transition-transform hover:scale-110',
                    editColor === color ? 'border-text-primary' : 'border-transparent',
                  ]"
                  :style="{ backgroundColor: color }"
                  :disabled="isSaving"
                  @click="editColor = color"
                />
              </div>

              <Button
                variant="primary"
                size="sm"
                :disabled="isSaving"
                @click="handleSaveEdit"
              >
                Save
              </Button>
              <Button
                variant="ghost"
                size="sm"
                :disabled="isSaving"
                @click="cancelEditing"
              >
                Cancel
              </Button>
            </template>

            <!-- View mode -->
            <template v-else>
              <span
                class="h-4 w-4 flex-shrink-0 rounded-full"
                :style="{ backgroundColor: tag.color }"
              />
              <span class="flex-1 text-small text-text-primary">
                {{ tag.name }}
              </span>

              <button
                type="button"
                class="rounded p-1 text-text-muted transition-colors hover:bg-bg-secondary hover:text-text-primary"
                aria-label="Edit tag"
                :disabled="isDeleting !== null"
                @click="startEditing(tag)"
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
                    d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125"
                  />
                </svg>
              </button>

              <button
                type="button"
                class="rounded p-1 text-text-muted transition-colors hover:bg-accent-error/10 hover:text-accent-error"
                aria-label="Delete tag"
                :disabled="isDeleting !== null"
                @click="handleDeleteTag(tag.id)"
              >
                <svg
                  v-if="isDeleting === tag.id"
                  class="h-4 w-4 animate-spin"
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
                    d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
                  />
                </svg>
              </button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <Button
        variant="ghost"
        @click="handleClose"
      >
        Close
      </Button>
    </template>
  </Modal>
</template>
