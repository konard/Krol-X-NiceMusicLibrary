/**
 * Mood Chain Store
 * Manages mood chain state, playback, and suggestions
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  MoodChain,
  MoodChainDetail,
  MoodChainSong,
  MoodChainCreate,
  MoodChainUpdate,
  MoodChainFromHistoryRequest,
  NextSongSuggestion,
  TransitionUpdate,
} from '@/types'
import * as moodChainsApi from '@/services/moodChains'
import { usePlayerStore } from './player'
import { useUiStore } from './ui'

export const useMoodChainStore = defineStore('moodChain', () => {
  // State
  const chains = ref<MoodChain[]>([])
  const currentChain = ref<MoodChainDetail | null>(null)
  const isLoading = ref(false)
  const isLoadingChain = ref(false)
  const error = ref<string | null>(null)

  // Pagination state
  const currentPage = ref(1)
  const totalPages = ref(0)
  const totalItems = ref(0)
  const pageSize = ref(20)

  // Chain playback state
  const isPlayingChain = ref(false)
  const currentSongInChain = ref<MoodChainSong | null>(null)
  const suggestions = ref<NextSongSuggestion[]>([])
  const isLoadingSuggestions = ref(false)
  const autoAdvanceTimer = ref<ReturnType<typeof setTimeout> | null>(null)
  const autoAdvanceCountdown = ref(0)
  const recentlyPlayed = ref<string[]>([]) // Track IDs

  // Edit mode state
  const isEditing = ref(false)

  // Getters
  const hasChains = computed(() => chains.value.length > 0)
  const hasMorePages = computed(() => currentPage.value < totalPages.value)
  const chainSongIds = computed(() =>
    currentChain.value?.songs.map(s => s.song_id) || []
  )

  // Actions

  /**
   * Fetch paginated list of mood chains
   */
  async function fetchChains(page = 1, limit = pageSize.value): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      const response = await moodChainsApi.getMoodChains(page, limit)
      chains.value = response.items
      currentPage.value = response.page
      totalPages.value = response.pages
      totalItems.value = response.total
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch mood chains'
      const uiStore = useUiStore()
      uiStore.showError(error.value)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Load more chains (pagination)
   */
  async function loadMoreChains(): Promise<void> {
    if (!hasMorePages.value || isLoading.value) return

    isLoading.value = true
    error.value = null

    try {
      const response = await moodChainsApi.getMoodChains(currentPage.value + 1, pageSize.value)
      chains.value = [...chains.value, ...response.items]
      currentPage.value = response.page
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load more chains'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch a single mood chain with songs and transitions
   */
  async function fetchChain(id: string): Promise<MoodChainDetail | null> {
    isLoadingChain.value = true
    error.value = null

    try {
      const chain = await moodChainsApi.getMoodChain(id)
      currentChain.value = chain
      return chain
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch mood chain'
      const uiStore = useUiStore()
      uiStore.showError(error.value)
      return null
    } finally {
      isLoadingChain.value = false
    }
  }

  /**
   * Create a new mood chain
   */
  async function createChain(data: MoodChainCreate): Promise<MoodChain | null> {
    isLoading.value = true
    error.value = null

    try {
      const chain = await moodChainsApi.createMoodChain(data)
      chains.value = [chain, ...chains.value]
      totalItems.value++
      const uiStore = useUiStore()
      uiStore.showSuccess('Mood chain created successfully')
      return chain
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create mood chain'
      const uiStore = useUiStore()
      uiStore.showError(error.value)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update a mood chain's metadata
   */
  async function updateChain(id: string, data: MoodChainUpdate): Promise<MoodChain | null> {
    error.value = null

    try {
      const updated = await moodChainsApi.updateMoodChain(id, data)

      // Update in list
      const index = chains.value.findIndex(c => c.id === id)
      if (index !== -1) {
        chains.value[index] = updated
      }

      // Update current chain if it matches
      if (currentChain.value?.id === id) {
        currentChain.value = { ...currentChain.value, ...updated }
      }

      const uiStore = useUiStore()
      uiStore.showSuccess('Mood chain updated')
      return updated
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update mood chain'
      const uiStore = useUiStore()
      uiStore.showError(error.value)
      return null
    }
  }

  /**
   * Delete a mood chain
   */
  async function deleteChain(id: string): Promise<boolean> {
    error.value = null

    try {
      await moodChainsApi.deleteMoodChain(id)
      chains.value = chains.value.filter(c => c.id !== id)
      totalItems.value--

      if (currentChain.value?.id === id) {
        currentChain.value = null
        stopChainPlayback()
      }

      const uiStore = useUiStore()
      uiStore.showSuccess('Mood chain deleted')
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete mood chain'
      const uiStore = useUiStore()
      uiStore.showError(error.value)
      return false
    }
  }

  /**
   * Create a mood chain from listening history
   */
  async function createFromHistory(data: MoodChainFromHistoryRequest): Promise<MoodChainDetail | null> {
    isLoading.value = true
    error.value = null

    try {
      const chain = await moodChainsApi.createFromHistory(data)
      // Add to chains list (only the basic info)
      const { songs: _songs, transitions: _transitions, ...basicInfo } = chain
      void _songs
      void _transitions
      chains.value = [basicInfo, ...chains.value]
      totalItems.value++
      currentChain.value = chain

      const uiStore = useUiStore()
      uiStore.showSuccess(`Created mood chain with ${chain.song_count} songs from history`)
      return chain
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create from history'
      const uiStore = useUiStore()
      uiStore.showError(error.value)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Add a song to the current mood chain
   */
  async function addSong(songId: string, position?: number): Promise<boolean> {
    if (!currentChain.value) return false
    error.value = null

    try {
      const updated = await moodChainsApi.addSongToMoodChain(
        currentChain.value.id,
        { song_id: songId, position }
      )
      currentChain.value = updated

      // Update song count in list
      const index = chains.value.findIndex(c => c.id === currentChain.value?.id)
      if (index !== -1) {
        chains.value[index].song_count = updated.song_count
      }

      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to add song'
      const uiStore = useUiStore()
      uiStore.showError(error.value)
      return false
    }
  }

  /**
   * Remove a song from the current mood chain
   */
  async function removeSong(songId: string): Promise<boolean> {
    if (!currentChain.value) return false
    error.value = null

    try {
      const updated = await moodChainsApi.removeSongFromMoodChain(
        currentChain.value.id,
        songId
      )
      currentChain.value = updated

      // Update song count in list
      const index = chains.value.findIndex(c => c.id === currentChain.value?.id)
      if (index !== -1) {
        chains.value[index].song_count = updated.song_count
      }

      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to remove song'
      const uiStore = useUiStore()
      uiStore.showError(error.value)
      return false
    }
  }

  /**
   * Reorder songs in the current mood chain
   */
  async function reorderSongs(songIds: string[]): Promise<boolean> {
    if (!currentChain.value) return false
    error.value = null

    try {
      const updated = await moodChainsApi.reorderMoodChainSongs(
        currentChain.value.id,
        songIds
      )
      currentChain.value = updated
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to reorder songs'
      const uiStore = useUiStore()
      uiStore.showError(error.value)
      return false
    }
  }

  /**
   * Update transitions in the current mood chain
   */
  async function updateTransitions(transitions: TransitionUpdate[]): Promise<boolean> {
    if (!currentChain.value) return false
    error.value = null

    try {
      const updated = await moodChainsApi.updateTransitions(
        currentChain.value.id,
        { transitions }
      )
      currentChain.value = updated
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update transitions'
      const uiStore = useUiStore()
      uiStore.showError(error.value)
      return false
    }
  }

  // Chain Playback Actions

  /**
   * Start chain playback from a specific song
   */
  async function startChainPlayback(startSongId?: string): Promise<void> {
    if (!currentChain.value || currentChain.value.songs.length === 0) return

    const playerStore = usePlayerStore()
    isPlayingChain.value = true
    recentlyPlayed.value = []

    // Find the starting song
    let startSong: MoodChainSong
    if (startSongId) {
      const found = currentChain.value.songs.find(s => s.song_id === startSongId)
      startSong = found || currentChain.value.songs[0]
    } else {
      startSong = currentChain.value.songs[0]
    }

    currentSongInChain.value = startSong
    recentlyPlayed.value.push(startSong.song_id)

    // Convert to Track format and play
    const track = moodChainSongToTrack(startSong)
    await playerStore.play(track)

    // Fetch suggestions for next song
    await fetchNextSuggestions()
  }

  /**
   * Fetch next song suggestions based on current song
   */
  async function fetchNextSuggestions(): Promise<void> {
    if (!currentChain.value || !currentSongInChain.value) return

    isLoadingSuggestions.value = true

    try {
      const response = await moodChainsApi.getNextSongSuggestions(
        currentChain.value.id,
        currentSongInChain.value.song_id,
        recentlyPlayed.value.length
      )
      suggestions.value = response.suggestions

      // Start auto-advance timer if enabled
      if (currentChain.value.auto_advance && suggestions.value.length > 0) {
        startAutoAdvanceTimer()
      }
    } catch (err) {
      console.error('Failed to fetch suggestions:', err)
      suggestions.value = []
    } finally {
      isLoadingSuggestions.value = false
    }
  }

  /**
   * Select and play the next song from suggestions
   */
  async function selectNextSong(songId: string): Promise<void> {
    if (!currentChain.value) return

    clearAutoAdvanceTimer()

    // Find the song in chain
    const song = currentChain.value.songs.find(s => s.song_id === songId)
    if (!song) return

    // Record the transition for learning
    if (currentSongInChain.value) {
      await recordTransition(currentSongInChain.value.song_id, songId)
    }

    // Update current song and recently played
    currentSongInChain.value = song
    recentlyPlayed.value.push(songId)
    if (recentlyPlayed.value.length > 5) {
      recentlyPlayed.value.shift()
    }

    // Play the song
    const playerStore = usePlayerStore()
    const track = moodChainSongToTrack(song)
    await playerStore.play(track)

    // Fetch new suggestions
    await fetchNextSuggestions()
  }

  /**
   * Record a transition was played (for learning)
   */
  async function recordTransition(fromSongId: string, toSongId: string): Promise<void> {
    if (!currentChain.value) return

    try {
      await moodChainsApi.recordTransitionPlayed(
        currentChain.value.id,
        fromSongId,
        toSongId
      )
    } catch (err) {
      console.error('Failed to record transition:', err)
    }
  }

  /**
   * Start auto-advance countdown timer
   */
  function startAutoAdvanceTimer(): void {
    if (!currentChain.value) return

    clearAutoAdvanceTimer()
    autoAdvanceCountdown.value = currentChain.value.auto_advance_delay_seconds

    const tick = () => {
      autoAdvanceCountdown.value--
      if (autoAdvanceCountdown.value <= 0) {
        // Auto-select first suggestion
        if (suggestions.value.length > 0) {
          selectNextSong(suggestions.value[0].song_id)
        }
      } else {
        autoAdvanceTimer.value = setTimeout(tick, 1000)
      }
    }

    autoAdvanceTimer.value = setTimeout(tick, 1000)
  }

  /**
   * Clear auto-advance timer
   */
  function clearAutoAdvanceTimer(): void {
    if (autoAdvanceTimer.value) {
      clearTimeout(autoAdvanceTimer.value)
      autoAdvanceTimer.value = null
    }
    autoAdvanceCountdown.value = 0
  }

  /**
   * Stop chain playback
   */
  function stopChainPlayback(): void {
    clearAutoAdvanceTimer()
    isPlayingChain.value = false
    currentSongInChain.value = null
    suggestions.value = []
    recentlyPlayed.value = []
  }

  /**
   * Toggle edit mode
   */
  function setEditing(editing: boolean): void {
    isEditing.value = editing
  }

  /**
   * Clear current chain
   */
  function clearCurrentChain(): void {
    currentChain.value = null
    stopChainPlayback()
    isEditing.value = false
  }

  /**
   * Reset store state
   */
  function $reset(): void {
    chains.value = []
    currentChain.value = null
    isLoading.value = false
    isLoadingChain.value = false
    error.value = null
    currentPage.value = 1
    totalPages.value = 0
    totalItems.value = 0
    stopChainPlayback()
    isEditing.value = false
  }

  // Helper function to convert MoodChainSong to Track format
  function moodChainSongToTrack(song: MoodChainSong) {
    return {
      id: song.song_id,
      title: song.title,
      artist: song.artist,
      album: song.album,
      duration_seconds: song.duration_seconds,
      cover_art_path: song.cover_art_path,
      genre: song.genre,
      // Default values for required Track fields
      year: null,
      file_format: 'mp3',
      play_count: 0,
      last_played_at: null,
      is_favorite: false,
      rating: null,
      created_at: song.added_at,
    }
  }

  return {
    // State
    chains,
    currentChain,
    isLoading,
    isLoadingChain,
    error,
    currentPage,
    totalPages,
    totalItems,
    pageSize,
    isPlayingChain,
    currentSongInChain,
    suggestions,
    isLoadingSuggestions,
    autoAdvanceCountdown,
    recentlyPlayed,
    isEditing,

    // Getters
    hasChains,
    hasMorePages,
    chainSongIds,

    // Actions
    fetchChains,
    loadMoreChains,
    fetchChain,
    createChain,
    updateChain,
    deleteChain,
    createFromHistory,
    addSong,
    removeSong,
    reorderSongs,
    updateTransitions,

    // Playback
    startChainPlayback,
    fetchNextSuggestions,
    selectNextSong,
    recordTransition,
    startAutoAdvanceTimer,
    clearAutoAdvanceTimer,
    stopChainPlayback,

    // UI
    setEditing,
    clearCurrentChain,
    $reset,

    // Helpers
    moodChainSongToTrack,
  }
})
