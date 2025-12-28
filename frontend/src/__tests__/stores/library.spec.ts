import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useLibraryStore } from '../../stores/library'
import * as songService from '../../services/songs'
import type { Song, SongListResponse } from '../../types'

// Mock the song service
vi.mock('../../services/songs', () => ({
  songService: {
    getSongs: vi.fn(),
    getSongById: vi.fn(),
    uploadSong: vi.fn(),
    updateSong: vi.fn(),
    deleteSong: vi.fn(),
    isValidAudioFile: vi.fn(() => true),
  },
  isValidAudioFile: vi.fn(() => true),
}))

const mockSong: Song = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  title: 'Test Song',
  artist: 'Test Artist',
  album: 'Test Album',
  genre: 'Rock',
  year: 2023,
  duration_seconds: 180,
  file_format: 'mp3',
  play_count: 10,
  last_played_at: null,
  is_favorite: false,
  rating: null,
  cover_art_path: null,
  created_at: '2023-01-01T00:00:00Z',
}

const mockSongListResponse: SongListResponse = {
  items: [mockSong],
  total: 1,
  page: 1,
  limit: 20,
  pages: 1,
}

describe('libraryStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('initial state', () => {
    it('has correct default values', () => {
      const store = useLibraryStore()

      expect(store.songs).toEqual([])
      expect(store.isLoading).toBe(false)
      expect(store.error).toBe(null)
      expect(store.page).toBe(1)
      expect(store.limit).toBe(20)
      expect(store.total).toBe(0)
      expect(store.viewMode).toBe('table')
      expect(store.uploadQueue).toEqual([])
    })

    it('has correct default filters', () => {
      const store = useLibraryStore()

      expect(store.filters).toEqual({
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
    })
  })

  describe('getters', () => {
    it('trackCount returns total', () => {
      const store = useLibraryStore()
      store.total = 42

      expect(store.trackCount).toBe(42)
    })

    it('hasMore returns true when more pages exist', () => {
      const store = useLibraryStore()
      store.page = 1
      store.totalPages = 3

      expect(store.hasMore).toBe(true)
    })

    it('hasMore returns false on last page', () => {
      const store = useLibraryStore()
      store.page = 3
      store.totalPages = 3

      expect(store.hasMore).toBe(false)
    })

    it('isEmpty returns true when no songs and not loading', () => {
      const store = useLibraryStore()
      store.songs = []
      store.isLoading = false

      expect(store.isEmpty).toBe(true)
    })

    it('isEmpty returns false when loading', () => {
      const store = useLibraryStore()
      store.songs = []
      store.isLoading = true

      expect(store.isEmpty).toBe(false)
    })

    it('activeFiltersCount counts active filters', () => {
      const store = useLibraryStore()

      expect(store.activeFiltersCount).toBe(0)

      store.filters.search = 'test'
      expect(store.activeFiltersCount).toBe(1)

      store.filters.artist = 'Artist'
      expect(store.activeFiltersCount).toBe(2)

      store.filters.is_favorite = true
      expect(store.activeFiltersCount).toBe(3)
    })
  })

  describe('fetchSongs', () => {
    it('fetches songs and updates state', async () => {
      const store = useLibraryStore()
      vi.mocked(songService.songService.getSongs).mockResolvedValue(mockSongListResponse)

      await store.fetchSongs(true)

      expect(songService.songService.getSongs).toHaveBeenCalledWith(1, 20, store.filters)
      expect(store.songs).toEqual([mockSong])
      expect(store.total).toBe(1)
      expect(store.totalPages).toBe(1)
      expect(store.isLoading).toBe(false)
    })

    it('sets isLoading during fetch', async () => {
      const store = useLibraryStore()
      let loadingDuringFetch = false

      vi.mocked(songService.songService.getSongs).mockImplementation(async () => {
        loadingDuringFetch = store.isLoading
        return mockSongListResponse
      })

      await store.fetchSongs(true)

      expect(loadingDuringFetch).toBe(true)
    })

    it('handles fetch error', async () => {
      const store = useLibraryStore()
      vi.mocked(songService.songService.getSongs).mockRejectedValue(
        new Error('Network error')
      )

      await expect(store.fetchSongs(true)).rejects.toThrow('Network error')
      expect(store.error).toBe('Network error')
      expect(store.isLoading).toBe(false)
    })

    it('resets page on reset=true', async () => {
      const store = useLibraryStore()
      store.page = 5
      store.songs = [mockSong]

      vi.mocked(songService.songService.getSongs).mockResolvedValue(mockSongListResponse)

      await store.fetchSongs(true)

      expect(store.page).toBe(1)
    })

    it('appends songs on reset=false', async () => {
      const store = useLibraryStore()
      const existingSong = { ...mockSong, id: 'existing-id' }
      store.songs = [existingSong]
      store.page = 2

      vi.mocked(songService.songService.getSongs).mockResolvedValue(mockSongListResponse)

      await store.fetchSongs(false)

      expect(store.songs).toHaveLength(2)
      expect(store.songs[0]).toEqual(existingSong)
      expect(store.songs[1]).toEqual(mockSong)
    })
  })

  describe('loadMore', () => {
    it('increments page and fetches', async () => {
      const store = useLibraryStore()
      store.page = 1
      store.totalPages = 3

      vi.mocked(songService.songService.getSongs).mockResolvedValue(mockSongListResponse)

      await store.loadMore()

      expect(store.page).toBe(2)
      expect(songService.songService.getSongs).toHaveBeenCalled()
    })

    it('does not fetch if no more pages', async () => {
      const store = useLibraryStore()
      store.page = 3
      store.totalPages = 3

      await store.loadMore()

      expect(songService.songService.getSongs).not.toHaveBeenCalled()
    })
  })

  describe('updateSong', () => {
    it('updates song in list', async () => {
      const store = useLibraryStore()
      store.songs = [mockSong]

      const updatedSong = { ...mockSong, title: 'Updated Title' }
      vi.mocked(songService.songService.updateSong).mockResolvedValue(updatedSong)

      await store.updateSong(mockSong.id, { title: 'Updated Title' })

      expect(store.songs[0].title).toBe('Updated Title')
    })
  })

  describe('deleteSong', () => {
    it('removes song from list', async () => {
      const store = useLibraryStore()
      store.songs = [mockSong]
      store.total = 1

      vi.mocked(songService.songService.deleteSong).mockResolvedValue()

      await store.deleteSong(mockSong.id)

      expect(store.songs).toHaveLength(0)
      expect(store.total).toBe(0)
    })
  })

  describe('toggleFavorite', () => {
    it('toggles favorite status', async () => {
      const store = useLibraryStore()
      store.songs = [mockSong]

      const updatedSong = { ...mockSong, is_favorite: true }
      vi.mocked(songService.songService.updateSong).mockResolvedValue(updatedSong)

      await store.toggleFavorite(mockSong.id)

      expect(songService.songService.updateSong).toHaveBeenCalledWith(mockSong.id, {
        is_favorite: true,
      })
    })
  })

  describe('setFilters', () => {
    it('updates filters and refetches', async () => {
      const store = useLibraryStore()
      vi.mocked(songService.songService.getSongs).mockResolvedValue(mockSongListResponse)

      store.setFilters({ search: 'test query' })

      expect(store.filters.search).toBe('test query')
      expect(songService.songService.getSongs).toHaveBeenCalled()
    })
  })

  describe('clearFilters', () => {
    it('resets all filters', async () => {
      const store = useLibraryStore()
      store.filters = {
        search: 'test',
        artist: 'Artist',
        album: 'Album',
        genre: 'Rock',
        is_favorite: true,
        year_from: 2020,
        year_to: 2023,
        sort: 'title',
        order: 'asc',
      }

      vi.mocked(songService.songService.getSongs).mockResolvedValue(mockSongListResponse)

      store.clearFilters()

      expect(store.filters).toEqual({
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
    })
  })

  describe('setSort', () => {
    it('sets sort field and order', async () => {
      const store = useLibraryStore()
      vi.mocked(songService.songService.getSongs).mockResolvedValue(mockSongListResponse)

      store.setSort('title', 'asc')

      expect(store.filters.sort).toBe('title')
      expect(store.filters.order).toBe('asc')
    })

    it('toggles order when same field is clicked', async () => {
      const store = useLibraryStore()
      store.filters.sort = 'title'
      store.filters.order = 'asc'

      vi.mocked(songService.songService.getSongs).mockResolvedValue(mockSongListResponse)

      store.setSort('title')

      expect(store.filters.order).toBe('desc')
    })
  })

  describe('setViewMode', () => {
    it('sets view mode', () => {
      const store = useLibraryStore()

      store.setViewMode('grid')
      expect(store.viewMode).toBe('grid')

      store.setViewMode('table')
      expect(store.viewMode).toBe('table')
    })
  })

  describe('upload queue', () => {
    it('adds files to upload queue', () => {
      const store = useLibraryStore()
      const file = new File([''], 'test.mp3', { type: 'audio/mpeg' })

      // The store uses songService.isValidAudioFile which is mocked to return true
      store.addToUploadQueue([file])

      expect(store.uploadQueue).toHaveLength(1)
      expect(store.uploadQueue[0].file).toBe(file)
      expect(store.uploadQueue[0].status).toBe('pending')
    })

    it('removes item from upload queue', () => {
      const store = useLibraryStore()
      const file = new File([''], 'test.mp3', { type: 'audio/mpeg' })

      // The store uses songService.isValidAudioFile which is mocked to return true
      store.addToUploadQueue([file])
      expect(store.uploadQueue.length).toBeGreaterThan(0)
      const uploadId = store.uploadQueue[0].id

      store.removeFromUploadQueue(uploadId)

      expect(store.uploadQueue).toHaveLength(0)
    })

    it('clears completed uploads', () => {
      const store = useLibraryStore()

      store.uploadQueue = [
        { id: '1', file: new File([''], 'a.mp3'), progress: 100, status: 'success' },
        { id: '2', file: new File([''], 'b.mp3'), progress: 50, status: 'uploading' },
        { id: '3', file: new File([''], 'c.mp3'), progress: 0, status: 'pending' },
      ]

      store.clearCompletedUploads()

      expect(store.uploadQueue).toHaveLength(2)
      expect(store.uploadQueue.every((i) => i.status !== 'success')).toBe(true)
    })

    it('clears all uploads', () => {
      const store = useLibraryStore()

      store.uploadQueue = [
        { id: '1', file: new File([''], 'a.mp3'), progress: 100, status: 'success' },
        { id: '2', file: new File([''], 'b.mp3'), progress: 0, status: 'pending' },
      ]

      store.clearUploadQueue()

      expect(store.uploadQueue).toHaveLength(0)
    })
  })

  describe('upload modal', () => {
    it('opens and closes upload modal', () => {
      const store = useLibraryStore()

      expect(store.isUploadModalOpen).toBe(false)

      store.openUploadModal()
      expect(store.isUploadModalOpen).toBe(true)

      store.closeUploadModal()
      expect(store.isUploadModalOpen).toBe(false)
    })
  })
})
