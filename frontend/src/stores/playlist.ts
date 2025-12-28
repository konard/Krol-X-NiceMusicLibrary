/**
 * Playlist Store (Pinia)
 *
 * Manages the playlist state including:
 * - Playlists list with pagination
 * - Current playlist details
 * - Create, update, delete operations
 * - Add/remove songs from playlists
 * - Song reordering
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Playlist, PlaylistCreate, PlaylistUpdate, Song } from '@/types'
import { apiService } from '@/services/api'

export const usePlaylistStore = defineStore('playlist', () => {
  // State
  const playlists = ref<Playlist[]>([])
  const currentPlaylist = ref<Playlist | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Pagination
  const page = ref(1)
  const limit = ref(20)
  const total = ref(0)
  const totalPages = ref(0)

  // Modal state
  const isCreateModalOpen = ref(false)
  const isEditModalOpen = ref(false)
  const editingPlaylist = ref<Playlist | null>(null)

  // Getters
  const playlistCount = computed(() => total.value)
  const hasMore = computed(() => page.value < totalPages.value)
  const isEmpty = computed(() => playlists.value.length === 0 && !isLoading.value)

  // Actions

  /**
   * Fetch all playlists with pagination
   */
  async function fetchPlaylists(reset = false): Promise<void> {
    if (reset) {
      page.value = 1
      playlists.value = []
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await apiService.get<{
        items: Playlist[]
        total: number
        page: number
        limit: number
        pages: number
      }>('/playlists', {
        page: page.value,
        limit: limit.value,
      })

      if (reset) {
        playlists.value = response.data.items
      } else {
        playlists.value = [...playlists.value, ...response.data.items]
      }
      total.value = response.data.total
      totalPages.value = response.data.pages
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to load playlists'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Load next page of playlists
   */
  async function loadMore(): Promise<void> {
    if (hasMore.value && !isLoading.value) {
      page.value++
      await fetchPlaylists(false)
    }
  }

  /**
   * Refresh the playlists list
   */
  async function refresh(): Promise<void> {
    await fetchPlaylists(true)
  }

  /**
   * Fetch a single playlist by ID
   */
  async function fetchPlaylist(id: string): Promise<Playlist> {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiService.get<Playlist>(`/playlists/${id}`)
      currentPlaylist.value = response.data
      return response.data
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to load playlist'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create a new playlist
   */
  async function createPlaylist(data: PlaylistCreate): Promise<Playlist> {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiService.post<Playlist>('/playlists', data)
      const newPlaylist = response.data
      playlists.value = [newPlaylist, ...playlists.value]
      total.value++
      return newPlaylist
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to create playlist'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update an existing playlist
   */
  async function updatePlaylist(id: string, data: PlaylistUpdate): Promise<Playlist> {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiService.patch<Playlist>(`/playlists/${id}`, data)
      const updatedPlaylist = response.data

      // Update in the list
      const index = playlists.value.findIndex((p) => p.id === id)
      if (index !== -1) {
        playlists.value[index] = updatedPlaylist
      }

      // Update current playlist if it's the same
      if (currentPlaylist.value?.id === id) {
        currentPlaylist.value = updatedPlaylist
      }

      return updatedPlaylist
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to update playlist'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete a playlist
   */
  async function deletePlaylist(id: string): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      await apiService.delete(`/playlists/${id}`)
      playlists.value = playlists.value.filter((p) => p.id !== id)
      total.value = Math.max(0, total.value - 1)

      // Clear current playlist if it was deleted
      if (currentPlaylist.value?.id === id) {
        currentPlaylist.value = null
      }
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to delete playlist'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Add a song to a playlist
   */
  async function addSongToPlaylist(playlistId: string, songId: string): Promise<void> {
    error.value = null

    try {
      await apiService.post(`/playlists/${playlistId}/songs`, { song_id: songId })

      // Refresh the playlist if it's the current one
      if (currentPlaylist.value?.id === playlistId) {
        await fetchPlaylist(playlistId)
      }

      // Update song count in the list
      const playlist = playlists.value.find((p) => p.id === playlistId)
      if (playlist) {
        playlist.song_count++
      }
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to add song to playlist'
      throw e
    }
  }

  /**
   * Remove a song from a playlist
   */
  async function removeSongFromPlaylist(playlistId: string, songId: string): Promise<void> {
    error.value = null

    try {
      await apiService.delete(`/playlists/${playlistId}/songs/${songId}`)

      // Update local state
      if (currentPlaylist.value?.id === playlistId) {
        currentPlaylist.value.songs = currentPlaylist.value.songs.filter((s) => s.id !== songId)
        currentPlaylist.value.song_ids = currentPlaylist.value.song_ids.filter((id) => id !== songId)
        currentPlaylist.value.song_count = Math.max(0, currentPlaylist.value.song_count - 1)
      }

      // Update song count in the list
      const playlist = playlists.value.find((p) => p.id === playlistId)
      if (playlist) {
        playlist.song_count = Math.max(0, playlist.song_count - 1)
      }
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to remove song from playlist'
      throw e
    }
  }

  /**
   * Reorder songs in a playlist
   */
  async function reorderSongs(playlistId: string, songIds: string[]): Promise<void> {
    error.value = null

    try {
      await apiService.put(`/playlists/${playlistId}/songs/reorder`, { song_ids: songIds })

      // Update local state optimistically
      if (currentPlaylist.value?.id === playlistId) {
        const songsMap = new Map(currentPlaylist.value.songs.map((s) => [s.id, s]))
        currentPlaylist.value.songs = songIds
          .map((id) => songsMap.get(id))
          .filter((s): s is Song => s !== undefined)
        currentPlaylist.value.song_ids = songIds
      }
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to reorder songs'
      // Revert by refetching
      if (currentPlaylist.value?.id === playlistId) {
        await fetchPlaylist(playlistId)
      }
      throw e
    }
  }

  /**
   * Open create playlist modal
   */
  function openCreateModal(): void {
    isCreateModalOpen.value = true
  }

  /**
   * Close create playlist modal
   */
  function closeCreateModal(): void {
    isCreateModalOpen.value = false
  }

  /**
   * Open edit playlist modal
   */
  function openEditModal(playlist: Playlist): void {
    editingPlaylist.value = playlist
    isEditModalOpen.value = true
  }

  /**
   * Close edit playlist modal
   */
  function closeEditModal(): void {
    isEditModalOpen.value = false
    editingPlaylist.value = null
  }

  /**
   * Clear error
   */
  function clearError(): void {
    error.value = null
  }

  /**
   * Clear current playlist
   */
  function clearCurrentPlaylist(): void {
    currentPlaylist.value = null
  }

  return {
    // State
    playlists,
    currentPlaylist,
    isLoading,
    error,
    page,
    limit,
    total,
    totalPages,
    isCreateModalOpen,
    isEditModalOpen,
    editingPlaylist,

    // Getters
    playlistCount,
    hasMore,
    isEmpty,

    // Actions
    fetchPlaylists,
    loadMore,
    refresh,
    fetchPlaylist,
    createPlaylist,
    updatePlaylist,
    deletePlaylist,
    addSongToPlaylist,
    removeSongFromPlaylist,
    reorderSongs,
    openCreateModal,
    closeCreateModal,
    openEditModal,
    closeEditModal,
    clearError,
    clearCurrentPlaylist,
  }
})
