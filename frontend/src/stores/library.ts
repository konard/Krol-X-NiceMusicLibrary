/**
 * Library Store (Pinia)
 *
 * Manages the music library state including:
 * - Songs list with pagination
 * - Filters and sorting
 * - Upload state and progress
 * - View mode preferences
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Song, SongDetail, SongFilters, SongUpdate } from '@/types'
import { songService } from '@/services/songs'

export type ViewMode = 'table' | 'grid'
export type SortField = 'title' | 'artist' | 'album' | 'created_at' | 'play_count' | 'last_played_at'
export type SortOrder = 'asc' | 'desc'

export interface UploadItem {
  id: string
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
  song?: Song
}

export const useLibraryStore = defineStore('library', () => {
  // State
  const songs = ref<Song[]>([])
  const selectedSong = ref<SongDetail | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Pagination
  const page = ref(1)
  const limit = ref(20)
  const total = ref(0)
  const totalPages = ref(0)

  // Filters
  const filters = ref<SongFilters>({
    search: '',
    artist: '',
    album: '',
    genre: '',
    is_favorite: undefined,
    year_from: undefined,
    year_to: undefined,
    sort: 'created_at',
    order: 'desc',
  })

  // View preferences
  const viewMode = ref<ViewMode>('table')

  // Upload state
  const uploadQueue = ref<UploadItem[]>([])
  const isUploading = ref(false)
  const isUploadModalOpen = ref(false)

  // Getters
  const trackCount = computed(() => total.value)
  const hasMore = computed(() => page.value < totalPages.value)
  const isEmpty = computed(() => songs.value.length === 0 && !isLoading.value)
  const activeFiltersCount = computed(() => {
    let count = 0
    if (filters.value.search) count++
    if (filters.value.artist) count++
    if (filters.value.album) count++
    if (filters.value.genre) count++
    if (filters.value.is_favorite !== undefined) count++
    if (filters.value.year_from !== undefined) count++
    if (filters.value.year_to !== undefined) count++
    return count
  })

  const uploadProgress = computed(() => {
    if (uploadQueue.value.length === 0) return 0
    const total = uploadQueue.value.reduce((acc, item) => acc + item.progress, 0)
    return Math.round(total / uploadQueue.value.length)
  })

  const pendingUploads = computed(() =>
    uploadQueue.value.filter((item) => item.status === 'pending' || item.status === 'uploading')
  )

  const completedUploads = computed(() =>
    uploadQueue.value.filter((item) => item.status === 'success')
  )

  const failedUploads = computed(() =>
    uploadQueue.value.filter((item) => item.status === 'error')
  )

  // Actions

  /**
   * Fetch songs with current filters and pagination
   */
  async function fetchSongs(reset = false): Promise<void> {
    if (reset) {
      page.value = 1
      songs.value = []
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await songService.getSongs(page.value, limit.value, filters.value)
      if (reset) {
        songs.value = response.items
      } else {
        songs.value = [...songs.value, ...response.items]
      }
      total.value = response.total
      totalPages.value = response.pages
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to load songs'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Load next page of songs (for infinite scroll)
   */
  async function loadMore(): Promise<void> {
    if (hasMore.value && !isLoading.value) {
      page.value++
      await fetchSongs(false)
    }
  }

  /**
   * Refresh the song list with current filters
   */
  async function refresh(): Promise<void> {
    await fetchSongs(true)
  }

  /**
   * Get detailed information about a song
   */
  async function fetchSongDetail(songId: string): Promise<SongDetail> {
    try {
      const song = await songService.getSongById(songId)
      selectedSong.value = song
      return song
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to load song details'
      throw e
    }
  }

  /**
   * Update song metadata
   */
  async function updateSong(songId: string, data: SongUpdate): Promise<Song> {
    try {
      const updatedSong = await songService.updateSong(songId, data)
      // Update the song in the local list
      const index = songs.value.findIndex((s) => s.id === songId)
      if (index !== -1) {
        songs.value[index] = updatedSong
      }
      // Update selected song if it's the same
      if (selectedSong.value?.id === songId) {
        selectedSong.value = { ...selectedSong.value, ...updatedSong }
      }
      return updatedSong
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to update song'
      throw e
    }
  }

  /**
   * Delete a song
   */
  async function deleteSong(songId: string): Promise<void> {
    try {
      await songService.deleteSong(songId)
      // Remove from local list
      songs.value = songs.value.filter((s) => s.id !== songId)
      total.value = Math.max(0, total.value - 1)
      // Clear selected if it was this song
      if (selectedSong.value?.id === songId) {
        selectedSong.value = null
      }
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to delete song'
      throw e
    }
  }

  /**
   * Toggle favorite status
   */
  async function toggleFavorite(songId: string): Promise<void> {
    const song = songs.value.find((s) => s.id === songId)
    if (song) {
      await updateSong(songId, { is_favorite: !song.is_favorite })
    }
  }

  /**
   * Set filters and refresh
   */
  function setFilters(newFilters: Partial<SongFilters>): void {
    filters.value = { ...filters.value, ...newFilters }
    fetchSongs(true)
  }

  /**
   * Clear all filters
   */
  function clearFilters(): void {
    filters.value = {
      search: '',
      artist: '',
      album: '',
      genre: '',
      is_favorite: undefined,
      year_from: undefined,
      year_to: undefined,
      sort: 'created_at',
      order: 'desc',
    }
    fetchSongs(true)
  }

  /**
   * Set sort field and order
   */
  function setSort(field: SortField, order?: SortOrder): void {
    // Toggle order if same field
    if (filters.value.sort === field && order === undefined) {
      filters.value.order = filters.value.order === 'asc' ? 'desc' : 'asc'
    } else {
      filters.value.sort = field
      if (order) {
        filters.value.order = order
      }
    }
    fetchSongs(true)
  }

  /**
   * Set view mode
   */
  function setViewMode(mode: ViewMode): void {
    viewMode.value = mode
  }

  /**
   * Add files to upload queue
   */
  function addToUploadQueue(files: File[]): void {
    const newItems: UploadItem[] = files
      .filter((file) => songService.isValidAudioFile(file))
      .map((file) => ({
        id: `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        file,
        progress: 0,
        status: 'pending' as const,
      }))

    uploadQueue.value = [...uploadQueue.value, ...newItems]
  }

  /**
   * Upload a single file from the queue
   */
  async function uploadFile(uploadId: string): Promise<void> {
    const item = uploadQueue.value.find((i) => i.id === uploadId)
    if (!item || item.status !== 'pending') return

    item.status = 'uploading'

    try {
      const result = await songService.uploadSong(item.file, undefined, (progress) => {
        item.progress = progress
      })
      item.status = 'success'
      item.progress = 100
      // Add the new song to the list
      const newSong = await songService.getSongById(result.id)
      songs.value = [newSong, ...songs.value]
      total.value++
    } catch (e) {
      item.status = 'error'
      item.error = (e as { message: string }).message || 'Upload failed'
    }
  }

  /**
   * Process all pending uploads
   */
  async function processUploadQueue(): Promise<void> {
    if (isUploading.value) return

    isUploading.value = true

    try {
      for (const item of uploadQueue.value) {
        if (item.status === 'pending') {
          await uploadFile(item.id)
        }
      }
    } finally {
      isUploading.value = false
    }
  }

  /**
   * Remove item from upload queue
   */
  function removeFromUploadQueue(uploadId: string): void {
    uploadQueue.value = uploadQueue.value.filter((i) => i.id !== uploadId)
  }

  /**
   * Clear completed uploads from queue
   */
  function clearCompletedUploads(): void {
    uploadQueue.value = uploadQueue.value.filter(
      (item) => item.status === 'pending' || item.status === 'uploading'
    )
  }

  /**
   * Clear all uploads from queue
   */
  function clearUploadQueue(): void {
    uploadQueue.value = []
    isUploading.value = false
  }

  /**
   * Open upload modal
   */
  function openUploadModal(): void {
    isUploadModalOpen.value = true
  }

  /**
   * Close upload modal
   */
  function closeUploadModal(): void {
    isUploadModalOpen.value = false
  }

  /**
   * Clear error
   */
  function clearError(): void {
    error.value = null
  }

  return {
    // State
    songs,
    selectedSong,
    isLoading,
    error,
    page,
    limit,
    total,
    totalPages,
    filters,
    viewMode,
    uploadQueue,
    isUploading,
    isUploadModalOpen,

    // Getters
    trackCount,
    hasMore,
    isEmpty,
    activeFiltersCount,
    uploadProgress,
    pendingUploads,
    completedUploads,
    failedUploads,

    // Actions
    fetchSongs,
    loadMore,
    refresh,
    fetchSongDetail,
    updateSong,
    deleteSong,
    toggleFavorite,
    setFilters,
    clearFilters,
    setSort,
    setViewMode,
    addToUploadQueue,
    uploadFile,
    processUploadQueue,
    removeFromUploadQueue,
    clearCompletedUploads,
    clearUploadQueue,
    openUploadModal,
    closeUploadModal,
    clearError,
  }
})
