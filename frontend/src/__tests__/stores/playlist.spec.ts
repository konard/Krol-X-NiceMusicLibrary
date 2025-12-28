import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { usePlaylistStore } from '../../stores/playlist'
import { apiService } from '../../services/api'
import type { Playlist } from '../../types'

// Mock the API service
vi.mock('../../services/api', () => ({
  apiService: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockPlaylist: Playlist = {
  id: 'playlist-123',
  name: 'Test Playlist',
  description: 'A test playlist',
  cover_url: undefined,
  songs: [],
  song_ids: [],
  song_count: 0,
  total_duration: 0,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
}

const mockPlaylistListResponse = {
  items: [mockPlaylist],
  total: 1,
  page: 1,
  limit: 20,
  pages: 1,
}

describe('playlistStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('initial state', () => {
    it('has correct default values', () => {
      const store = usePlaylistStore()

      expect(store.playlists).toEqual([])
      expect(store.currentPlaylist).toBe(null)
      expect(store.isLoading).toBe(false)
      expect(store.error).toBe(null)
      expect(store.page).toBe(1)
      expect(store.limit).toBe(20)
      expect(store.total).toBe(0)
      expect(store.isCreateModalOpen).toBe(false)
      expect(store.isEditModalOpen).toBe(false)
    })
  })

  describe('getters', () => {
    it('playlistCount returns total', () => {
      const store = usePlaylistStore()
      store.total = 42

      expect(store.playlistCount).toBe(42)
    })

    it('hasMore returns true when more pages exist', () => {
      const store = usePlaylistStore()
      store.page = 1
      store.totalPages = 3

      expect(store.hasMore).toBe(true)
    })

    it('hasMore returns false on last page', () => {
      const store = usePlaylistStore()
      store.page = 3
      store.totalPages = 3

      expect(store.hasMore).toBe(false)
    })

    it('isEmpty returns true when no playlists and not loading', () => {
      const store = usePlaylistStore()
      store.playlists = []
      store.isLoading = false

      expect(store.isEmpty).toBe(true)
    })

    it('isEmpty returns false when loading', () => {
      const store = usePlaylistStore()
      store.playlists = []
      store.isLoading = true

      expect(store.isEmpty).toBe(false)
    })
  })

  describe('fetchPlaylists', () => {
    it('fetches playlists and updates state', async () => {
      const store = usePlaylistStore()
      vi.mocked(apiService.get).mockResolvedValue({ data: mockPlaylistListResponse })

      await store.fetchPlaylists(true)

      expect(apiService.get).toHaveBeenCalledWith('/playlists', { page: 1, limit: 20 })
      expect(store.playlists).toEqual([mockPlaylist])
      expect(store.total).toBe(1)
      expect(store.totalPages).toBe(1)
      expect(store.isLoading).toBe(false)
    })

    it('sets isLoading during fetch', async () => {
      const store = usePlaylistStore()
      let loadingDuringFetch = false

      vi.mocked(apiService.get).mockImplementation(async () => {
        loadingDuringFetch = store.isLoading
        return { data: mockPlaylistListResponse }
      })

      await store.fetchPlaylists(true)

      expect(loadingDuringFetch).toBe(true)
    })

    it('handles fetch error', async () => {
      const store = usePlaylistStore()
      vi.mocked(apiService.get).mockRejectedValue(new Error('Network error'))

      await expect(store.fetchPlaylists(true)).rejects.toThrow('Network error')
      expect(store.error).toBe('Network error')
      expect(store.isLoading).toBe(false)
    })

    it('resets page on reset=true', async () => {
      const store = usePlaylistStore()
      store.page = 5
      store.playlists = [mockPlaylist]

      vi.mocked(apiService.get).mockResolvedValue({ data: mockPlaylistListResponse })

      await store.fetchPlaylists(true)

      expect(store.page).toBe(1)
    })

    it('appends playlists on reset=false', async () => {
      const store = usePlaylistStore()
      const existingPlaylist = { ...mockPlaylist, id: 'existing-id' }
      store.playlists = [existingPlaylist]
      store.page = 2

      vi.mocked(apiService.get).mockResolvedValue({ data: mockPlaylistListResponse })

      await store.fetchPlaylists(false)

      expect(store.playlists).toHaveLength(2)
      expect(store.playlists[0]).toEqual(existingPlaylist)
      expect(store.playlists[1]).toEqual(mockPlaylist)
    })
  })

  describe('loadMore', () => {
    it('increments page and fetches', async () => {
      const store = usePlaylistStore()
      store.page = 1
      store.totalPages = 3

      vi.mocked(apiService.get).mockResolvedValue({ data: mockPlaylistListResponse })

      await store.loadMore()

      expect(store.page).toBe(2)
      expect(apiService.get).toHaveBeenCalled()
    })

    it('does not fetch if no more pages', async () => {
      const store = usePlaylistStore()
      store.page = 3
      store.totalPages = 3

      await store.loadMore()

      expect(apiService.get).not.toHaveBeenCalled()
    })
  })

  describe('fetchPlaylist', () => {
    it('fetches a single playlist and sets currentPlaylist', async () => {
      const store = usePlaylistStore()
      vi.mocked(apiService.get).mockResolvedValue({ data: mockPlaylist })

      const result = await store.fetchPlaylist('playlist-123')

      expect(apiService.get).toHaveBeenCalledWith('/playlists/playlist-123')
      expect(store.currentPlaylist).toEqual(mockPlaylist)
      expect(result).toEqual(mockPlaylist)
    })
  })

  describe('createPlaylist', () => {
    it('creates a playlist and adds it to the list', async () => {
      const store = usePlaylistStore()
      vi.mocked(apiService.post).mockResolvedValue({ data: mockPlaylist })

      const result = await store.createPlaylist({ name: 'Test Playlist' })

      expect(apiService.post).toHaveBeenCalledWith('/playlists', { name: 'Test Playlist' })
      expect(store.playlists).toContainEqual(mockPlaylist)
      expect(store.total).toBe(1)
      expect(result).toEqual(mockPlaylist)
    })
  })

  describe('updatePlaylist', () => {
    it('updates a playlist and updates the list', async () => {
      const store = usePlaylistStore()
      store.playlists = [mockPlaylist]

      const updatedPlaylist = { ...mockPlaylist, name: 'Updated Name' }
      vi.mocked(apiService.patch).mockResolvedValue({ data: updatedPlaylist })

      await store.updatePlaylist(mockPlaylist.id, { name: 'Updated Name' })

      expect(apiService.patch).toHaveBeenCalledWith('/playlists/playlist-123', { name: 'Updated Name' })
      expect(store.playlists[0].name).toBe('Updated Name')
    })

    it('updates currentPlaylist if it matches', async () => {
      const store = usePlaylistStore()
      store.currentPlaylist = mockPlaylist

      const updatedPlaylist = { ...mockPlaylist, name: 'Updated Name' }
      vi.mocked(apiService.patch).mockResolvedValue({ data: updatedPlaylist })

      await store.updatePlaylist(mockPlaylist.id, { name: 'Updated Name' })

      expect(store.currentPlaylist?.name).toBe('Updated Name')
    })
  })

  describe('deletePlaylist', () => {
    it('deletes a playlist and removes it from the list', async () => {
      const store = usePlaylistStore()
      store.playlists = [mockPlaylist]
      store.total = 1

      vi.mocked(apiService.delete).mockResolvedValue({})

      await store.deletePlaylist(mockPlaylist.id)

      expect(apiService.delete).toHaveBeenCalledWith('/playlists/playlist-123')
      expect(store.playlists).toHaveLength(0)
      expect(store.total).toBe(0)
    })

    it('clears currentPlaylist if it was deleted', async () => {
      const store = usePlaylistStore()
      store.currentPlaylist = mockPlaylist

      vi.mocked(apiService.delete).mockResolvedValue({})

      await store.deletePlaylist(mockPlaylist.id)

      expect(store.currentPlaylist).toBe(null)
    })
  })

  describe('addSongToPlaylist', () => {
    it('adds a song to a playlist', async () => {
      const store = usePlaylistStore()
      store.playlists = [{ ...mockPlaylist, song_count: 0 }]

      vi.mocked(apiService.post).mockResolvedValue({})

      await store.addSongToPlaylist('playlist-123', 'song-456')

      expect(apiService.post).toHaveBeenCalledWith('/playlists/playlist-123/songs', { song_id: 'song-456' })
      expect(store.playlists[0].song_count).toBe(1)
    })
  })

  describe('removeSongFromPlaylist', () => {
    it('removes a song from a playlist', async () => {
      const store = usePlaylistStore()
      store.playlists = [{ ...mockPlaylist, song_count: 1 }]

      vi.mocked(apiService.delete).mockResolvedValue({})

      await store.removeSongFromPlaylist('playlist-123', 'song-456')

      expect(apiService.delete).toHaveBeenCalledWith('/playlists/playlist-123/songs/song-456')
      expect(store.playlists[0].song_count).toBe(0)
    })
  })

  describe('reorderSongs', () => {
    it('reorders songs in a playlist', async () => {
      const store = usePlaylistStore()
      vi.mocked(apiService.put).mockResolvedValue({})

      await store.reorderSongs('playlist-123', ['song-1', 'song-2', 'song-3'])

      expect(apiService.put).toHaveBeenCalledWith('/playlists/playlist-123/songs/reorder', {
        song_ids: ['song-1', 'song-2', 'song-3'],
      })
    })
  })

  describe('modal state', () => {
    it('opens and closes create modal', () => {
      const store = usePlaylistStore()

      expect(store.isCreateModalOpen).toBe(false)

      store.openCreateModal()
      expect(store.isCreateModalOpen).toBe(true)

      store.closeCreateModal()
      expect(store.isCreateModalOpen).toBe(false)
    })

    it('opens and closes edit modal', () => {
      const store = usePlaylistStore()

      expect(store.isEditModalOpen).toBe(false)
      expect(store.editingPlaylist).toBe(null)

      store.openEditModal(mockPlaylist)
      expect(store.isEditModalOpen).toBe(true)
      expect(store.editingPlaylist).toEqual(mockPlaylist)

      store.closeEditModal()
      expect(store.isEditModalOpen).toBe(false)
      expect(store.editingPlaylist).toBe(null)
    })
  })

  describe('utility methods', () => {
    it('clears error', () => {
      const store = usePlaylistStore()
      store.error = 'Some error'

      store.clearError()

      expect(store.error).toBe(null)
    })

    it('clears current playlist', () => {
      const store = usePlaylistStore()
      store.currentPlaylist = mockPlaylist

      store.clearCurrentPlaylist()

      expect(store.currentPlaylist).toBe(null)
    })
  })
})
