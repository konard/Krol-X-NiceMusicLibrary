<script setup lang="ts">
import { ref, computed } from 'vue'
import { Button, Dropdown, Input, Loader } from '@/components/ui'
import type { DropdownOption } from '@/components/ui/Dropdown.vue'

type ViewMode = 'list' | 'grid'

const viewMode = ref<ViewMode>('list')
const searchQuery = ref('')
const sortBy = ref<string>('title')
const isLoading = ref(false)

const sortOptions: DropdownOption[] = [
  { value: 'title', label: 'Title' },
  { value: 'artist', label: 'Artist' },
  { value: 'date_added', label: 'Date Added' },
  { value: 'play_count', label: 'Most Played' },
  { value: 'last_played', label: 'Last Played' },
]

const trackCount = computed(() => 0) // Will be populated from API
</script>

<template>
  <div class="animate-fade-in">
    <!-- Header -->
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-h1 text-text-primary">Library</h1>
        <p class="text-text-secondary">{{ trackCount }} tracks</p>
      </div>
      <div class="flex items-center gap-3">
        <Button
          variant="primary"
          size="sm"
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
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
            />
          </svg>
          Upload
        </Button>
      </div>
    </div>

    <!-- Filters -->
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center">
      <div class="flex-1">
        <Input
          v-model="searchQuery"
          type="search"
          placeholder="Search tracks..."
        />
      </div>
      <div class="flex items-center gap-3">
        <div class="w-40">
          <Dropdown
            v-model="sortBy"
            :options="sortOptions"
            placeholder="Sort by"
          />
        </div>
        <!-- View toggle -->
        <div class="flex rounded-lg border border-bg-tertiary">
          <button
            type="button"
            :class="[
              'p-2 transition-colors',
              viewMode === 'list' ? 'bg-accent-primary text-white' : 'text-text-secondary hover:text-text-primary',
            ]"
            aria-label="List view"
            @click="viewMode = 'list'"
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
                d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z"
              />
            </svg>
          </button>
          <button
            type="button"
            :class="[
              'p-2 transition-colors',
              viewMode === 'grid' ? 'bg-accent-primary text-white' : 'text-text-secondary hover:text-text-primary',
            ]"
            aria-label="Grid view"
            @click="viewMode = 'grid'"
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
                d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div v-if="isLoading" class="flex items-center justify-center py-12">
      <Loader size="lg" />
    </div>

    <div v-else class="card">
      <!-- Empty state -->
      <div class="py-12 text-center">
        <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-bg-secondary">
          <svg
            class="h-8 w-8 text-text-muted"
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
        <h3 class="text-h3 text-text-primary mb-2">No tracks yet</h3>
        <p class="text-text-secondary mb-4">
          Upload your first track to get started
        </p>
        <Button variant="primary">
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
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
            />
          </svg>
          Upload Music
        </Button>
      </div>
    </div>
  </div>
</template>
