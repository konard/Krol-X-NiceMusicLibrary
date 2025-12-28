<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { useTagStore } from '@/stores/tag'
import type { Tag } from '@/types'
import TagBadge from './TagBadge.vue'

export interface TagEditorProps {
  songId: string
  songTags: Tag[]
}

const props = defineProps<TagEditorProps>()

const emit = defineEmits<{
  'update:songTags': [tags: Tag[]]
  tagAdded: [tag: Tag]
  tagRemoved: [tag: Tag]
}>()

const tagStore = useTagStore()
const { tags: allTags, isLoading } = storeToRefs(tagStore)

const isEditing = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
const inputValue = ref('')
const isAddingTag = ref(false)

const filteredTags = computed(() => {
  if (!inputValue.value.trim()) {
    return allTags.value.filter(
      (tag) => !props.songTags.some((st) => st.id === tag.id)
    )
  }

  const searchTerm = inputValue.value.toLowerCase().trim()
  return allTags.value.filter(
    (tag) =>
      tag.name.toLowerCase().includes(searchTerm) &&
      !props.songTags.some((st) => st.id === tag.id)
  )
})

const canCreateNew = computed(() => {
  if (!inputValue.value.trim()) return false
  const searchTerm = inputValue.value.toLowerCase().trim()
  return !allTags.value.some((tag) => tag.name.toLowerCase() === searchTerm)
})

watch(isEditing, async (editing) => {
  if (editing) {
    await nextTick()
    inputRef.value?.focus()
    // Fetch tags if not loaded
    if (allTags.value.length === 0) {
      tagStore.fetchTags()
    }
  } else {
    inputValue.value = ''
  }
})

function startEditing() {
  isEditing.value = true
}

function stopEditing() {
  isEditing.value = false
}

async function handleAddTag(tag: Tag) {
  if (isAddingTag.value) return

  isAddingTag.value = true
  try {
    await tagStore.addTagToSong(props.songId, tag.id)
    const newTags = [...props.songTags, tag]
    emit('update:songTags', newTags)
    emit('tagAdded', tag)
    inputValue.value = ''
  } catch {
    // Error handled by store
  } finally {
    isAddingTag.value = false
  }
}

async function handleRemoveTag(tag: Tag) {
  try {
    await tagStore.removeTagFromSong(props.songId, tag.id)
    const newTags = props.songTags.filter((t) => t.id !== tag.id)
    emit('update:songTags', newTags)
    emit('tagRemoved', tag)
  } catch {
    // Error handled by store
  }
}

async function handleCreateAndAddTag() {
  if (!canCreateNew.value || isAddingTag.value) return

  isAddingTag.value = true
  try {
    const newTag = await tagStore.createTag({ name: inputValue.value.trim() })
    await tagStore.addTagToSong(props.songId, newTag.id)
    const newTags = [...props.songTags, newTag]
    emit('update:songTags', newTags)
    emit('tagAdded', newTag)
    inputValue.value = ''
  } catch {
    // Error handled by store
  } finally {
    isAddingTag.value = false
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    stopEditing()
  } else if (event.key === 'Enter' && canCreateNew.value) {
    handleCreateAndAddTag()
  }
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-1.5">
    <!-- Existing tags -->
    <TagBadge
      v-for="tag in songTags"
      :key="tag.id"
      :tag="tag"
      :removable="true"
      size="sm"
      @remove="handleRemoveTag"
    />

    <!-- Add tag button / input -->
    <div
      v-if="isEditing"
      class="relative"
    >
      <input
        ref="inputRef"
        v-model="inputValue"
        type="text"
        placeholder="Type to add..."
        class="h-6 w-32 rounded border border-bg-tertiary bg-bg-secondary px-2 text-caption text-text-primary placeholder-text-muted focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary"
        :disabled="isAddingTag"
        @keydown="handleKeydown"
        @blur="stopEditing"
      />

      <!-- Dropdown suggestions -->
      <div
        v-if="filteredTags.length > 0 || canCreateNew"
        class="absolute left-0 top-full z-10 mt-1 max-h-40 w-48 overflow-y-auto rounded-lg border border-bg-tertiary bg-bg-primary py-1 shadow-lg"
      >
        <!-- Loading indicator -->
        <div
          v-if="isLoading"
          class="px-3 py-2 text-center"
        >
          <svg
            class="mx-auto h-4 w-4 animate-spin text-text-muted"
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

        <template v-else>
          <!-- Create new option -->
          <button
            v-if="canCreateNew"
            type="button"
            class="flex w-full items-center gap-2 px-3 py-1.5 text-left text-caption text-accent-primary hover:bg-bg-secondary"
            @mousedown.prevent="handleCreateAndAddTag"
          >
            <svg
              class="h-3 w-3"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 4.5v15m7.5-7.5h-15"
              />
            </svg>
            Create "{{ inputValue.trim() }}"
          </button>

          <!-- Divider -->
          <div
            v-if="canCreateNew && filteredTags.length > 0"
            class="my-1 h-px bg-bg-tertiary"
          />

          <!-- Existing tags -->
          <button
            v-for="tag in filteredTags"
            :key="tag.id"
            type="button"
            class="flex w-full items-center gap-2 px-3 py-1.5 text-left text-caption text-text-primary hover:bg-bg-secondary"
            @mousedown.prevent="handleAddTag(tag)"
          >
            <span
              class="h-2 w-2 rounded-full"
              :style="{ backgroundColor: tag.color }"
            />
            {{ tag.name }}
          </button>
        </template>
      </div>
    </div>

    <!-- Add button -->
    <button
      v-else
      type="button"
      class="inline-flex h-6 items-center gap-1 rounded-full border border-dashed border-bg-tertiary px-2 text-caption text-text-muted transition-colors hover:border-accent-primary hover:text-accent-primary"
      @click="startEditing"
    >
      <svg
        class="h-3 w-3"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M12 4.5v15m7.5-7.5h-15"
        />
      </svg>
      Add tag
    </button>
  </div>
</template>
