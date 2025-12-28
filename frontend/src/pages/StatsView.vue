<script setup lang="ts">
import { ref } from 'vue'
import { Dropdown, Loader } from '@/components/ui'
import type { DropdownOption } from '@/components/ui/Dropdown.vue'

const selectedPeriod = ref<string>('month')
const isLoading = ref(false)

const periodOptions: DropdownOption[] = [
  { value: 'week', label: 'This Week' },
  { value: 'month', label: 'This Month' },
  { value: 'year', label: 'This Year' },
  { value: 'all', label: 'All Time' },
]

// Placeholder stats - will be populated from API
const stats = ref({
  totalHours: 0,
  totalPlays: 0,
  uniqueTracks: 0,
})
</script>

<template>
  <div class="animate-fade-in">
    <!-- Header -->
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-h1 text-text-primary">Your Statistics</h1>
        <p class="text-text-secondary">Track your listening habits</p>
      </div>
      <div class="w-40">
        <Dropdown
          v-model="selectedPeriod"
          :options="periodOptions"
        />
      </div>
    </div>

    <div v-if="isLoading" class="flex items-center justify-center py-12">
      <Loader size="lg" />
    </div>

    <template v-else>
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3 mb-8">
        <div class="card">
          <div class="flex items-center gap-3">
            <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-accent-primary/10">
              <svg
                class="h-6 w-6 text-accent-primary"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div>
              <p class="text-caption text-text-muted">Time Listened</p>
              <p class="text-h2 text-text-primary">{{ stats.totalHours }}h</p>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center gap-3">
            <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-accent-secondary/10">
              <svg
                class="h-6 w-6 text-accent-secondary"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z"
                />
              </svg>
            </div>
            <div>
              <p class="text-caption text-text-muted">Tracks Played</p>
              <p class="text-h2 text-text-primary">{{ stats.totalPlays }}</p>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center gap-3">
            <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-accent-success/10">
              <svg
                class="h-6 w-6 text-accent-success"
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
            <div>
              <p class="text-caption text-text-muted">Unique Tracks</p>
              <p class="text-h2 text-text-primary">{{ stats.uniqueTracks }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Grid -->
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <!-- Top Tracks -->
        <div class="card">
          <h2 class="text-h3 text-text-primary mb-4">Top Tracks</h2>
          <div class="py-8 text-center text-text-muted">
            <p>No listening data yet</p>
          </div>
        </div>

        <!-- Top Artists -->
        <div class="card">
          <h2 class="text-h3 text-text-primary mb-4">Top Artists</h2>
          <div class="py-8 text-center text-text-muted">
            <p>No listening data yet</p>
          </div>
        </div>

        <!-- Genre Distribution -->
        <div class="card">
          <h2 class="text-h3 text-text-primary mb-4">Genres</h2>
          <div class="py-8 text-center text-text-muted">
            <p>No listening data yet</p>
          </div>
        </div>

        <!-- Activity -->
        <div class="card">
          <h2 class="text-h3 text-text-primary mb-4">Daily Activity</h2>
          <div class="py-8 text-center text-text-muted">
            <p>No listening data yet</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
