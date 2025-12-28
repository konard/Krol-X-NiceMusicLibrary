/**
 * Stats Store (Pinia)
 *
 * Manages the statistics state including:
 * - Overview statistics (total plays, duration, etc.)
 * - Top songs and artists
 * - Listening history with pagination
 * - Period selection
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  StatsOverview,
  TopSongItem,
  TopArtistItem,
  ListeningHistoryItem,
  StatsPeriod,
  PlayRecordRequest,
} from '@/types'
import { statsService, type HistoryFilters } from '@/services/stats'

export const useStatsStore = defineStore('stats', () => {
  // State
  const overview = ref<StatsOverview | null>(null)
  const topSongs = ref<TopSongItem[]>([])
  const topArtists = ref<TopArtistItem[]>([])
  const history = ref<ListeningHistoryItem[]>([])
  const period = ref<StatsPeriod>('month')

  // Loading states
  const isLoadingOverview = ref(false)
  const isLoadingTopSongs = ref(false)
  const isLoadingTopArtists = ref(false)
  const isLoadingHistory = ref(false)

  // History pagination
  const historyPage = ref(1)
  const historyLimit = ref(20)
  const historyTotal = ref(0)
  const historyTotalPages = ref(0)

  // Error states
  const error = ref<string | null>(null)

  // Getters
  const totalHours = computed(() => {
    if (!overview.value) return 0
    return Math.round((overview.value.total_duration_seconds / 3600) * 10) / 10
  })

  const hasMoreHistory = computed(() => historyPage.value < historyTotalPages.value)

  const isLoading = computed(() =>
    isLoadingOverview.value ||
    isLoadingTopSongs.value ||
    isLoadingTopArtists.value ||
    isLoadingHistory.value
  )

  // Actions

  /**
   * Fetch overview statistics for current period
   */
  async function fetchOverview(): Promise<void> {
    isLoadingOverview.value = true
    error.value = null

    try {
      overview.value = await statsService.getOverview(period.value)
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to load statistics'
      throw e
    } finally {
      isLoadingOverview.value = false
    }
  }

  /**
   * Fetch top songs for current period
   */
  async function fetchTopSongs(limit: number = 10): Promise<void> {
    isLoadingTopSongs.value = true
    error.value = null

    try {
      const response = await statsService.getTopSongs(period.value, limit)
      topSongs.value = response.items
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to load top songs'
      throw e
    } finally {
      isLoadingTopSongs.value = false
    }
  }

  /**
   * Fetch top artists for current period
   */
  async function fetchTopArtists(limit: number = 10): Promise<void> {
    isLoadingTopArtists.value = true
    error.value = null

    try {
      const response = await statsService.getTopArtists(period.value, limit)
      topArtists.value = response.items
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to load top artists'
      throw e
    } finally {
      isLoadingTopArtists.value = false
    }
  }

  /**
   * Fetch listening history with pagination
   */
  async function fetchHistory(reset = false, filters?: HistoryFilters): Promise<void> {
    if (reset) {
      historyPage.value = 1
      history.value = []
    }

    isLoadingHistory.value = true
    error.value = null

    try {
      const response = await statsService.getHistory(
        historyPage.value,
        historyLimit.value,
        filters
      )

      if (reset) {
        history.value = response.items
      } else {
        history.value = [...history.value, ...response.items]
      }

      historyTotal.value = response.total
      historyTotalPages.value = response.pages
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to load listening history'
      throw e
    } finally {
      isLoadingHistory.value = false
    }
  }

  /**
   * Load more history items (for infinite scroll)
   */
  async function loadMoreHistory(filters?: HistoryFilters): Promise<void> {
    if (hasMoreHistory.value && !isLoadingHistory.value) {
      historyPage.value++
      await fetchHistory(false, filters)
    }
  }

  /**
   * Fetch all statistics at once for current period
   */
  async function fetchAllStats(): Promise<void> {
    await Promise.all([
      fetchOverview(),
      fetchTopSongs(),
      fetchTopArtists(),
    ])
  }

  /**
   * Set the statistics period and refresh data
   */
  async function setPeriod(newPeriod: StatsPeriod): Promise<void> {
    if (period.value === newPeriod) return
    period.value = newPeriod
    await fetchAllStats()
  }

  /**
   * Record a play event
   */
  async function recordPlay(data: PlayRecordRequest): Promise<void> {
    try {
      await statsService.recordPlay(data)
      // Optionally refresh stats after recording a play
    } catch (e) {
      console.error('Failed to record play:', e)
    }
  }

  /**
   * Clear error
   */
  function clearError(): void {
    error.value = null
  }

  /**
   * Reset store to initial state
   */
  function reset(): void {
    overview.value = null
    topSongs.value = []
    topArtists.value = []
    history.value = []
    period.value = 'month'
    historyPage.value = 1
    historyTotal.value = 0
    historyTotalPages.value = 0
    error.value = null
  }

  return {
    // State
    overview,
    topSongs,
    topArtists,
    history,
    period,
    isLoadingOverview,
    isLoadingTopSongs,
    isLoadingTopArtists,
    isLoadingHistory,
    historyPage,
    historyLimit,
    historyTotal,
    historyTotalPages,
    error,

    // Getters
    totalHours,
    hasMoreHistory,
    isLoading,

    // Actions
    fetchOverview,
    fetchTopSongs,
    fetchTopArtists,
    fetchHistory,
    loadMoreHistory,
    fetchAllStats,
    setPeriod,
    recordPlay,
    clearError,
    reset,
  }
})
