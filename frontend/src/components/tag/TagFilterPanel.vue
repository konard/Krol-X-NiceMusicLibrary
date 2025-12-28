<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useTagStore } from '@/stores/tag'
import type { Tag } from '@/types'
import TagBadge from './TagBadge.vue'

export interface TagFilterPanelProps {
  selectedTags: string[]
}

const props = defineProps<TagFilterPanelProps>()

const emit = defineEmits<{
  'update:selectedTags': [tagIds: string[]]
}>()

const tagStore = useTagStore()
const { sortedTags, isLoading } = storeToRefs(tagStore)

const isExpanded = ref(false)
const searchQuery = ref('')

const filteredTags = computed(() => {
  if (!searchQuery.value.trim()) {
    return sortedTags.value
  }

  const query = searchQuery.value.toLowerCase().trim()
  return sortedTags.value.filter((tag) =>
    tag.name.toLowerCase().includes(query)
  )
})

const selectedTagObjects = computed(() => {
  return sortedTags.value.filter((tag) => props.selectedTags.includes(tag.id))
})

const hasActiveFilters = computed(() => props.selectedTags.length > 0)

onMounted(() => {
  if (sortedTags.value.length === 0) {
    tagStore.fetchTags()
  }
})

function toggleTag(tag: Tag) {
  const newSelection = props.selectedTags.includes(tag.id)
    ? props.selectedTags.filter((id) => id !== tag.id)
    : [...props.selectedTags, tag.id]

  emit('update:selectedTags', newSelection)
}

function clearFilters() {
  emit('update:selectedTags', [])
}

function isSelected(tagId: string): boolean {
  return props.selectedTags.includes(tagId)
}
</script>

<template>
  <div class="rounded-lg border border-bg-tertiary bg-bg-secondary p-3">
    <!-- Header -->
    <div class="mb-2 flex items-center justify-between">
      <button
        type="button"
        class="flex items-center gap-2 text-small font-medium text-text-primary"
        @click="isExpanded = !isExpanded"
      >
        <svg
          :class="['h-4 w-4 transition-transform', isExpanded && 'rotate-90']"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M8.25 4.5l7.5 7.5-7.5 7.5"
          />
        </svg>
        Tags
        <span
          v-if="hasActiveFilters"
          class="rounded-full bg-accent-primary px-1.5 py-0.5 text-caption text-white"
        >
          {{ selectedTags.length }}
        </span>
      </button>

      <button
        v-if="hasActiveFilters"
        type="button"
        class="text-caption text-text-muted transition-colors hover:text-accent-primary"
        @click="clearFilters"
      >
        Clear
      </button>
    </div>

    <!-- Selected tags preview (when collapsed) -->
    <div
      v-if="!isExpanded && selectedTagObjects.length > 0"
      class="flex flex-wrap gap-1"
    >
      <TagBadge
        v-for="tag in selectedTagObjects"
        :key="tag.id"
        :tag="tag"
        :removable="true"
        size="sm"
        @remove="toggleTag(tag)"
      />
    </div>

    <!-- Expanded content -->
    <div
      v-if="isExpanded"
      class="mt-2 space-y-2"
    >
      <!-- Search input -->
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search tags..."
        class="w-full rounded-md border border-bg-tertiary bg-bg-primary px-2 py-1.5 text-small text-text-primary placeholder-text-muted focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary"
      />

      <!-- Loading state -->
      <div
        v-if="isLoading"
        class="flex justify-center py-4"
      >
        <svg
          class="h-5 w-5 animate-spin text-text-muted"
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
        v-else-if="filteredTags.length === 0"
        class="py-2 text-center text-small text-text-muted"
      >
        {{ searchQuery ? 'No tags found' : 'No tags available' }}
      </div>

      <!-- Tags list -->
      <div
        v-else
        class="flex max-h-48 flex-wrap gap-1.5 overflow-y-auto"
      >
        <button
          v-for="tag in filteredTags"
          :key="tag.id"
          type="button"
          :class="[
            'inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-caption font-medium transition-colors',
            isSelected(tag.id)
              ? 'border-accent-primary bg-accent-primary/10 text-accent-primary'
              : 'border-bg-tertiary text-text-secondary hover:border-text-muted hover:text-text-primary',
          ]"
          @click="toggleTag(tag)"
        >
          <span
            class="h-2 w-2 rounded-full"
            :style="{ backgroundColor: tag.color }"
          />
          {{ tag.name }}
          <svg
            v-if="isSelected(tag.id)"
            class="h-3 w-3"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fill-rule="evenodd"
              d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
              clip-rule="evenodd"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
