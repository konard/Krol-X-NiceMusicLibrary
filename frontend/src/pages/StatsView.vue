<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { Dropdown, Loader } from '@/components/ui'
import {
  ListeningChart,
  HourlyChart,
  TopSongsList,
  TopArtistsList,
  ListeningHistory,
} from '@/components/stats'
import { useStatsStore } from '@/stores/stats'
import { useUiStore } from '@/stores/ui'
import type { DropdownOption } from '@/components/ui/Dropdown.vue'
import type { StatsPeriod } from '@/types'

const statsStore = useStatsStore()
const uiStore = useUiStore()

// Extract reactive refs from store
const {
  overview,
  topSongs,
  topArtists,
  history,
  period,
  isLoadingOverview,
  isLoadingTopSongs,
  isLoadingTopArtists,
  isLoadingHistory,
  hasMoreHistory,
  historyTotal,
  totalHours,
  isLoading,
  error,
} = storeToRefs(statsStore)

// Tab state for mobile view
const activeTab = ref<'overview' | 'history'>('overview')

const periodOptions: DropdownOption[] = [
  { value: 'day', label: 'Today' },
  { value: 'week', label: 'This Week' },
  { value: 'month', label: 'This Month' },
  { value: 'year', label: 'This Year' },
  { value: 'all', label: 'All Time' },
]

// Computed values for display
const displayStats = computed(() => ({
  totalHours: totalHours.value,
  totalPlays: overview.value?.total_plays ?? 0,
  uniqueTracks: overview.value?.unique_songs ?? 0,
  uniqueArtists: overview.value?.unique_artists ?? 0,
  mostPlayedGenre: overview.value?.most_played_genre ?? null,
}))

const dailyActivity = computed(() => overview.value?.listening_by_day ?? [])
const hourlyActivity = computed(() => overview.value?.listening_by_hour ?? [])

// Handle period change
async function handlePeriodChange(newPeriod: string | number) {
  await statsStore.setPeriod(newPeriod as StatsPeriod)
}

// Handle loading more history
async function handleLoadMoreHistory() {
  await statsStore.loadMoreHistory()
}

// Watch for errors and show toast
watch(error, (newError) => {
  if (newError) {
    uiStore.showError(newError)
    statsStore.clearError()
  }
})

// Load initial data
onMounted(async () => {
  try {
    await Promise.all([
      statsStore.fetchAllStats(),
      statsStore.fetchHistory(true),
    ])
  } catch {
    // Error is handled by the watch
  }
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
          :model-value="period"
          :options="periodOptions"
          @update:model-value="handlePeriodChange"
        />
      </div>
    </div>

    <!-- Mobile Tab Switcher -->
    <div class="mb-6 flex gap-2 lg:hidden">
      <button
        :class="[
          'flex-1 rounded-lg py-2 text-small font-medium transition-colors',
          activeTab === 'overview'
            ? 'bg-accent-primary text-white'
            : 'bg-bg-secondary text-text-secondary hover:bg-bg-tertiary',
        ]"
        @click="activeTab = 'overview'"
      >
        Overview
      </button>
      <button
        :class="[
          'flex-1 rounded-lg py-2 text-small font-medium transition-colors',
          activeTab === 'history'
            ? 'bg-accent-primary text-white'
            : 'bg-bg-secondary text-text-secondary hover:bg-bg-tertiary',
        ]"
        @click="activeTab = 'history'"
      >
        History
      </button>
    </div>

    <!-- Loading State -->
    <div
      v-if="isLoading && !overview"
      class="flex items-center justify-center py-12"
    >
      <Loader size="lg" />
    </div>

    <template v-else>
      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <!-- Left Column - Overview (visible on desktop or when overview tab active on mobile) -->
        <div
          class="lg:col-span-2"
          :class="{ 'hidden lg:block': activeTab === 'history' }"
        >
          <!-- Summary Cards -->
          <div class="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <!-- Time Listened -->
            <div class="card">
              <div class="flex items-center gap-3">
                <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent-primary/10">
                  <svg
                    class="h-5 w-5 text-accent-primary"
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
                <div class="min-w-0">
                  <p class="text-caption text-text-muted">Time Listened</p>
                  <p class="truncate text-h3 text-text-primary">
                    <span v-if="isLoadingOverview" class="animate-pulse">--</span>
                    <span v-else>{{ displayStats.totalHours }}h</span>
                  </p>
                </div>
              </div>
            </div>

            <!-- Tracks Played -->
            <div class="card">
              <div class="flex items-center gap-3">
                <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent-secondary/10">
                  <svg
                    class="h-5 w-5 text-accent-secondary"
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
                <div class="min-w-0">
                  <p class="text-caption text-text-muted">Plays</p>
                  <p class="truncate text-h3 text-text-primary">
                    <span v-if="isLoadingOverview" class="animate-pulse">--</span>
                    <span v-else>{{ displayStats.totalPlays }}</span>
                  </p>
                </div>
              </div>
            </div>

            <!-- Unique Tracks -->
            <div class="card">
              <div class="flex items-center gap-3">
                <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent-success/10">
                  <svg
                    class="h-5 w-5 text-accent-success"
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
                <div class="min-w-0">
                  <p class="text-caption text-text-muted">Tracks</p>
                  <p class="truncate text-h3 text-text-primary">
                    <span v-if="isLoadingOverview" class="animate-pulse">--</span>
                    <span v-else>{{ displayStats.uniqueTracks }}</span>
                  </p>
                </div>
              </div>
            </div>

            <!-- Unique Artists -->
            <div class="card">
              <div class="flex items-center gap-3">
                <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent-warning/10">
                  <svg
                    class="h-5 w-5 text-accent-warning"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    stroke-width="1.5"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
                    />
                  </svg>
                </div>
                <div class="min-w-0">
                  <p class="text-caption text-text-muted">Artists</p>
                  <p class="truncate text-h3 text-text-primary">
                    <span v-if="isLoadingOverview" class="animate-pulse">--</span>
                    <span v-else>{{ displayStats.uniqueArtists }}</span>
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Most Played Genre Badge -->
          <div
            v-if="displayStats.mostPlayedGenre"
            class="mb-6"
          >
            <div class="inline-flex items-center gap-2 rounded-full bg-accent-primary/10 px-4 py-2">
              <svg
                class="h-4 w-4 text-accent-primary"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"
                />
              </svg>
              <span class="text-small text-accent-primary">
                Favorite Genre: <strong>{{ displayStats.mostPlayedGenre }}</strong>
              </span>
            </div>
          </div>

          <!-- Charts Grid -->
          <div class="space-y-6">
            <!-- Daily Activity Chart -->
            <ListeningChart
              :data="dailyActivity"
              :is-loading="isLoadingOverview"
            />

            <!-- Hourly Activity Chart -->
            <HourlyChart
              :data="hourlyActivity"
              :is-loading="isLoadingOverview"
            />

            <!-- Top Lists (side by side on larger screens) -->
            <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
              <TopSongsList
                :songs="topSongs"
                :is-loading="isLoadingTopSongs"
                :limit="5"
              />

              <TopArtistsList
                :artists="topArtists"
                :is-loading="isLoadingTopArtists"
                :limit="5"
              />
            </div>
          </div>
        </div>

        <!-- Right Column - History (visible on desktop or when history tab active on mobile) -->
        <div
          class="lg:col-span-1"
          :class="{ 'hidden lg:block': activeTab === 'overview' }"
        >
          <ListeningHistory
            :items="history"
            :is-loading="isLoadingHistory"
            :has-more="hasMoreHistory"
            :total="historyTotal"
            @load-more="handleLoadMoreHistory"
          />
        </div>
      </div>
    </template>
  </div>
</template>
