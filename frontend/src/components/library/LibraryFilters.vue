<script setup lang="ts">
import { ref, watch } from 'vue'
import type { SongFilters } from '@/types'
import { Input, Button, Dropdown } from '@/components/ui'
import type { DropdownOption } from '@/components/ui/Dropdown.vue'

export interface LibraryFiltersProps {
  filters: SongFilters
  activeCount?: number
}

const props = withDefaults(defineProps<LibraryFiltersProps>(), {
  activeCount: 0,
})

const emit = defineEmits<{
  'update:filters': [filters: Partial<SongFilters>]
  clear: []
}>()

// Local state for debounced search
const searchQuery = ref(props.filters.search || '')
let searchTimeout: ReturnType<typeof setTimeout> | null = null

// Sync search with external filter changes
watch(
  () => props.filters.search,
  (newValue) => {
    if (newValue !== searchQuery.value) {
      searchQuery.value = newValue || ''
    }
  }
)

// Debounced search
watch(searchQuery, (value) => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    emit('update:filters', { search: value })
  }, 300)
})

const isExpanded = ref(false)

const sortOptions: DropdownOption[] = [
  { value: 'created_at', label: 'Date Added' },
  { value: 'title', label: 'Title' },
  { value: 'artist', label: 'Artist' },
  { value: 'album', label: 'Album' },
  { value: 'play_count', label: 'Most Played' },
  { value: 'last_played_at', label: 'Last Played' },
]

const orderOptions: DropdownOption[] = [
  { value: 'desc', label: 'Descending' },
  { value: 'asc', label: 'Ascending' },
]

const favoriteOptions: DropdownOption[] = [
  { value: '', label: 'All' },
  { value: 'true', label: 'Favorites Only' },
  { value: 'false', label: 'Non-Favorites' },
]

function handleSortChange(value: string | number) {
  emit('update:filters', { sort: value as SongFilters['sort'] })
}

function handleOrderChange(value: string | number) {
  emit('update:filters', { order: value as SongFilters['order'] })
}

function handleFavoriteChange(value: string | number) {
  const val = value === '' ? undefined : value === 'true'
  emit('update:filters', { is_favorite: val })
}

function handleClear() {
  searchQuery.value = ''
  emit('clear')
}

function toggleExpanded() {
  isExpanded.value = !isExpanded.value
}
</script>

<template>
  <div class="space-y-4">
    <!-- Main row: Search + Sort + Toggle -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center">
      <!-- Search -->
      <div class="flex-1">
        <Input
          v-model="searchQuery"
          type="search"
          placeholder="Search by title, artist, or album..."
        >
          <template #prefix>
            <svg
              class="h-4 w-4 text-text-muted"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
              />
            </svg>
          </template>
        </Input>
      </div>

      <!-- Sort by -->
      <div class="flex items-center gap-2">
        <div class="w-40">
          <Dropdown
            :model-value="filters.sort"
            :options="sortOptions"
            placeholder="Sort by"
            @update:model-value="handleSortChange"
          />
        </div>
        <div class="w-32">
          <Dropdown
            :model-value="filters.order"
            :options="orderOptions"
            placeholder="Order"
            @update:model-value="handleOrderChange"
          />
        </div>
      </div>

      <!-- Expand filters button -->
      <Button
        variant="ghost"
        size="sm"
        :class="{ 'ring-1 ring-accent-primary': isExpanded || activeCount > 0 }"
        @click="toggleExpanded"
      >
        <svg
          class="mr-1 h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75"
          />
        </svg>
        Filters
        <span
          v-if="activeCount > 0"
          class="ml-1 inline-flex h-5 w-5 items-center justify-center rounded-full bg-accent-primary text-xs text-white"
        >
          {{ activeCount }}
        </span>
      </Button>
    </div>

    <!-- Expanded filters -->
    <Transition
      enter-active-class="transition-all duration-normal"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition-all duration-normal"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div
        v-if="isExpanded"
        class="rounded-lg border border-bg-tertiary bg-bg-secondary p-4"
      >
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <!-- Artist -->
          <Input
            :model-value="filters.artist || ''"
            label="Artist"
            placeholder="Filter by artist"
            @update:model-value="$emit('update:filters', { artist: $event || undefined })"
          />

          <!-- Album -->
          <Input
            :model-value="filters.album || ''"
            label="Album"
            placeholder="Filter by album"
            @update:model-value="$emit('update:filters', { album: $event || undefined })"
          />

          <!-- Genre -->
          <Input
            :model-value="filters.genre || ''"
            label="Genre"
            placeholder="Filter by genre"
            @update:model-value="$emit('update:filters', { genre: $event || undefined })"
          />

          <!-- Favorites -->
          <Dropdown
            :model-value="filters.is_favorite === undefined ? '' : String(filters.is_favorite)"
            :options="favoriteOptions"
            label="Favorites"
            placeholder="All"
            @update:model-value="handleFavoriteChange"
          />

          <!-- Year from -->
          <Input
            :model-value="filters.year_from ? String(filters.year_from) : ''"
            label="Year From"
            type="number"
            placeholder="e.g., 2000"
            @update:model-value="$emit('update:filters', { year_from: $event ? Number($event) : undefined })"
          />

          <!-- Year to -->
          <Input
            :model-value="filters.year_to ? String(filters.year_to) : ''"
            label="Year To"
            type="number"
            placeholder="e.g., 2024"
            @update:model-value="$emit('update:filters', { year_to: $event ? Number($event) : undefined })"
          />
        </div>

        <!-- Clear filters button -->
        <div class="mt-4 flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            :disabled="activeCount === 0"
            @click="handleClear"
          >
            Clear All Filters
          </Button>
        </div>
      </div>
    </Transition>
  </div>
</template>
