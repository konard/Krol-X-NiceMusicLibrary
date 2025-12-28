import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useTagStore, TAG_COLORS } from '../../stores/tag'
import { apiService } from '../../services/api'
import type { Tag } from '../../types'

// Mock the API service
vi.mock('../../services/api', () => ({
  apiService: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockTag: Tag = {
  id: 'tag-123',
  name: 'Rock',
  color: '#ef4444',
  created_at: '2023-01-01T00:00:00Z',
}

const mockTag2: Tag = {
  id: 'tag-456',
  name: 'Jazz',
  color: '#3b82f6',
  created_at: '2023-01-02T00:00:00Z',
}

describe('tagStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('TAG_COLORS constant', () => {
    it('exports an array of color strings', () => {
      expect(Array.isArray(TAG_COLORS)).toBe(true)
      expect(TAG_COLORS.length).toBeGreaterThan(0)
      expect(TAG_COLORS[0]).toMatch(/^#[0-9a-f]{6}$/i)
    })
  })

  describe('initial state', () => {
    it('has correct default values', () => {
      const store = useTagStore()

      expect(store.tags).toEqual([])
      expect(store.isLoading).toBe(false)
      expect(store.error).toBe(null)
      expect(store.isManageModalOpen).toBe(false)
    })
  })

  describe('getters', () => {
    it('tagCount returns tags length', () => {
      const store = useTagStore()
      store.tags = [mockTag, mockTag2]

      expect(store.tagCount).toBe(2)
    })

    it('isEmpty returns true when no tags and not loading', () => {
      const store = useTagStore()
      store.tags = []
      store.isLoading = false

      expect(store.isEmpty).toBe(true)
    })

    it('isEmpty returns false when loading', () => {
      const store = useTagStore()
      store.tags = []
      store.isLoading = true

      expect(store.isEmpty).toBe(false)
    })

    it('sortedTags returns tags sorted alphabetically', () => {
      const store = useTagStore()
      store.tags = [mockTag, mockTag2] // Rock, Jazz

      const sorted = store.sortedTags
      expect(sorted[0].name).toBe('Jazz')
      expect(sorted[1].name).toBe('Rock')
    })
  })

  describe('fetchTags', () => {
    it('fetches tags and updates state', async () => {
      const store = useTagStore()
      vi.mocked(apiService.get).mockResolvedValue({ data: [mockTag, mockTag2] })

      await store.fetchTags()

      expect(apiService.get).toHaveBeenCalledWith('/tags')
      expect(store.tags).toEqual([mockTag, mockTag2])
      expect(store.isLoading).toBe(false)
    })

    it('sets isLoading during fetch', async () => {
      const store = useTagStore()
      let loadingDuringFetch = false

      vi.mocked(apiService.get).mockImplementation(async () => {
        loadingDuringFetch = store.isLoading
        return { data: [mockTag] }
      })

      await store.fetchTags()

      expect(loadingDuringFetch).toBe(true)
    })

    it('handles fetch error', async () => {
      const store = useTagStore()
      vi.mocked(apiService.get).mockRejectedValue(new Error('Network error'))

      await expect(store.fetchTags()).rejects.toThrow('Network error')
      expect(store.error).toBe('Network error')
      expect(store.isLoading).toBe(false)
    })
  })

  describe('createTag', () => {
    it('creates a tag and adds it to the list', async () => {
      const store = useTagStore()
      vi.mocked(apiService.post).mockResolvedValue({ data: mockTag })

      const result = await store.createTag({ name: 'Rock' })

      expect(apiService.post).toHaveBeenCalledWith('/tags', { name: 'Rock', color: TAG_COLORS[0] })
      expect(store.tags).toContainEqual(mockTag)
      expect(result).toEqual(mockTag)
    })

    it('uses provided color if specified', async () => {
      const store = useTagStore()
      vi.mocked(apiService.post).mockResolvedValue({ data: mockTag })

      await store.createTag({ name: 'Rock', color: '#ff0000' })

      expect(apiService.post).toHaveBeenCalledWith('/tags', { name: 'Rock', color: '#ff0000' })
    })

    it('cycles through default colors based on existing tags count', async () => {
      const store = useTagStore()
      store.tags = [mockTag, mockTag2] // 2 existing tags

      vi.mocked(apiService.post).mockResolvedValue({ data: mockTag })

      await store.createTag({ name: 'New Tag' })

      expect(apiService.post).toHaveBeenCalledWith('/tags', { name: 'New Tag', color: TAG_COLORS[2] })
    })
  })

  describe('updateTag', () => {
    it('updates a tag and updates the list', async () => {
      const store = useTagStore()
      store.tags = [mockTag]

      const updatedTag = { ...mockTag, name: 'Updated Rock' }
      vi.mocked(apiService.patch).mockResolvedValue({ data: updatedTag })

      await store.updateTag(mockTag.id, { name: 'Updated Rock' })

      expect(apiService.patch).toHaveBeenCalledWith('/tags/tag-123', { name: 'Updated Rock' })
      expect(store.tags[0].name).toBe('Updated Rock')
    })
  })

  describe('deleteTag', () => {
    it('deletes a tag and removes it from the list', async () => {
      const store = useTagStore()
      store.tags = [mockTag, mockTag2]

      vi.mocked(apiService.delete).mockResolvedValue({})

      await store.deleteTag(mockTag.id)

      expect(apiService.delete).toHaveBeenCalledWith('/tags/tag-123')
      expect(store.tags).toHaveLength(1)
      expect(store.tags[0].id).toBe('tag-456')
    })
  })

  describe('addTagToSong', () => {
    it('adds a tag to a song', async () => {
      const store = useTagStore()
      vi.mocked(apiService.post).mockResolvedValue({})

      await store.addTagToSong('song-123', 'tag-456')

      expect(apiService.post).toHaveBeenCalledWith('/songs/song-123/tags', { tag_id: 'tag-456' })
    })
  })

  describe('removeTagFromSong', () => {
    it('removes a tag from a song', async () => {
      const store = useTagStore()
      vi.mocked(apiService.delete).mockResolvedValue({})

      await store.removeTagFromSong('song-123', 'tag-456')

      expect(apiService.delete).toHaveBeenCalledWith('/songs/song-123/tags/tag-456')
    })
  })

  describe('getSongTags', () => {
    it('gets tags for a song', async () => {
      const store = useTagStore()
      vi.mocked(apiService.get).mockResolvedValue({ data: [mockTag] })

      const result = await store.getSongTags('song-123')

      expect(apiService.get).toHaveBeenCalledWith('/songs/song-123/tags')
      expect(result).toEqual([mockTag])
    })
  })

  describe('findTagByName', () => {
    it('finds a tag by name (case insensitive)', () => {
      const store = useTagStore()
      store.tags = [mockTag, mockTag2]

      expect(store.findTagByName('rock')).toEqual(mockTag)
      expect(store.findTagByName('ROCK')).toEqual(mockTag)
      expect(store.findTagByName('Rock')).toEqual(mockTag)
    })

    it('returns undefined if tag not found', () => {
      const store = useTagStore()
      store.tags = [mockTag]

      expect(store.findTagByName('Pop')).toBeUndefined()
    })
  })

  describe('modal state', () => {
    it('opens and closes manage modal', () => {
      const store = useTagStore()

      expect(store.isManageModalOpen).toBe(false)

      store.openManageModal()
      expect(store.isManageModalOpen).toBe(true)

      store.closeManageModal()
      expect(store.isManageModalOpen).toBe(false)
    })
  })

  describe('utility methods', () => {
    it('clears error', () => {
      const store = useTagStore()
      store.error = 'Some error'

      store.clearError()

      expect(store.error).toBe(null)
    })
  })
})
