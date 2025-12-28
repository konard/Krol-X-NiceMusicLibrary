import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePlayerStore } from '@/stores/player'
import type { Track } from '@/types'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(global, 'localStorage', { value: localStorageMock })

// Mock tokenManager
vi.mock('@/services/api', () => ({
  tokenManager: {
    getAccessToken: vi.fn().mockReturnValue('test-token'),
  },
}))

// Mock Audio element
class MockAudio {
  src = ''
  volume = 1
  currentTime = 0
  duration = 180
  paused = true
  muted = false
  preload = 'auto'
  buffered = {
    length: 1,
    start: vi.fn().mockReturnValue(0),
    end: vi.fn().mockReturnValue(90),
  }
  error: MediaError | null = null

  private eventListeners: Record<string, ((event?: Event) => void)[]> = {}

  addEventListener(event: string, callback: (event?: Event) => void) {
    if (!this.eventListeners[event]) {
      this.eventListeners[event] = []
    }
    this.eventListeners[event].push(callback)
  }

  removeEventListener(event: string, callback: (event?: Event) => void) {
    if (this.eventListeners[event]) {
      this.eventListeners[event] = this.eventListeners[event].filter(cb => cb !== callback)
    }
  }

  dispatchEvent(event: string) {
    if (this.eventListeners[event]) {
      this.eventListeners[event].forEach(cb => cb())
    }
  }

  play = vi.fn().mockResolvedValue(undefined)
  pause = vi.fn()
  load = vi.fn()
}

// Mock window.Audio
global.Audio = MockAudio as unknown as typeof Audio

// Mock navigator.mediaSession
Object.defineProperty(navigator, 'mediaSession', {
  value: {
    metadata: null,
    setActionHandler: vi.fn(),
  },
  writable: true,
})

// Mock MediaMetadata
global.MediaMetadata = vi.fn().mockImplementation((data) => data) as unknown as typeof MediaMetadata

const mockTrack: Track = {
  id: 1,
  title: 'Test Song',
  artist: 'Test Artist',
  album: 'Test Album',
  duration: 180,
  file_path: '/music/test.mp3',
  cover_url: '/covers/test.jpg',
  genre: 'Rock',
  year: 2024,
  play_count: 10,
  is_favorite: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

const mockTrack2: Track = {
  id: 2,
  title: 'Another Song',
  artist: 'Another Artist',
  album: 'Another Album',
  duration: 240,
  file_path: '/music/another.mp3',
  cover_url: '/covers/another.jpg',
  genre: 'Pop',
  year: 2023,
  play_count: 5,
  is_favorite: true,
  created_at: '2024-01-02T00:00:00Z',
  updated_at: '2024-01-02T00:00:00Z',
}

const mockTrack3: Track = {
  id: 3,
  title: 'Third Song',
  artist: 'Third Artist',
  album: 'Third Album',
  duration: 200,
  file_path: '/music/third.mp3',
  genre: 'Jazz',
  year: 2022,
  play_count: 15,
  is_favorite: false,
  created_at: '2024-01-03T00:00:00Z',
  updated_at: '2024-01-03T00:00:00Z',
}

describe('usePlayerStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('starts with no current track', () => {
      const store = usePlayerStore()
      expect(store.currentTrack).toBeNull()
    })

    it('starts with empty queue', () => {
      const store = usePlayerStore()
      expect(store.queue).toHaveLength(0)
    })

    it('starts with queue index -1', () => {
      const store = usePlayerStore()
      expect(store.queueIndex).toBe(-1)
    })

    it('starts not playing', () => {
      const store = usePlayerStore()
      expect(store.isPlaying).toBe(false)
      expect(store.isPaused).toBe(false)
    })

    it('starts with default volume of 1', () => {
      const store = usePlayerStore()
      expect(store.volume).toBe(1)
    })

    it('starts not muted', () => {
      const store = usePlayerStore()
      expect(store.isMuted).toBe(false)
    })

    it('starts not shuffled', () => {
      const store = usePlayerStore()
      expect(store.isShuffled).toBe(false)
    })

    it('starts with repeat mode off', () => {
      const store = usePlayerStore()
      expect(store.repeatMode).toBe('off')
    })

    it('loads volume from localStorage', () => {
      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'player_volume') return '0.5'
        return null
      })
      setActivePinia(createPinia())
      const store = usePlayerStore()
      expect(store.volume).toBe(0.5)
    })

    it('loads muted state from localStorage', () => {
      localStorageMock.getItem.mockImplementation((key: string) => {
        if (key === 'player_muted') return 'true'
        return null
      })
      setActivePinia(createPinia())
      const store = usePlayerStore()
      expect(store.isMuted).toBe(true)
    })
  })

  describe('computed properties', () => {
    it('calculates progress correctly', () => {
      const store = usePlayerStore()
      store.currentTime = 90
      store.duration = 180
      expect(store.progress).toBe(50)
    })

    it('returns 0 progress when duration is 0', () => {
      const store = usePlayerStore()
      store.duration = 0
      expect(store.progress).toBe(0)
    })

    it('formats current time correctly', () => {
      const store = usePlayerStore()
      store.currentTime = 125
      expect(store.formattedCurrentTime).toBe('2:05')
    })

    it('formats duration correctly', () => {
      const store = usePlayerStore()
      store.duration = 180
      expect(store.formattedDuration).toBe('3:00')
    })

    it('hasNext returns true when there are more tracks', () => {
      const store = usePlayerStore()
      store.queue = [mockTrack, mockTrack2]
      store.queueIndex = 0
      expect(store.hasNext).toBe(true)
    })

    it('hasNext returns false at end of queue with repeat off', () => {
      const store = usePlayerStore()
      store.queue = [mockTrack, mockTrack2]
      store.queueIndex = 1
      store.repeatMode = 'off'
      expect(store.hasNext).toBe(false)
    })

    it('hasNext returns true at end of queue with repeat all', () => {
      const store = usePlayerStore()
      store.queue = [mockTrack, mockTrack2]
      store.queueIndex = 1
      store.repeatMode = 'all'
      expect(store.hasNext).toBe(true)
    })

    it('hasPrevious returns true when not at start', () => {
      const store = usePlayerStore()
      store.queue = [mockTrack, mockTrack2]
      store.queueIndex = 1
      expect(store.hasPrevious).toBe(true)
    })

    it('hasPrevious returns false at start with repeat off', () => {
      const store = usePlayerStore()
      store.queue = [mockTrack, mockTrack2]
      store.queueIndex = 0
      store.repeatMode = 'off'
      expect(store.hasPrevious).toBe(false)
    })
  })

  describe('audio initialization', () => {
    it('initializes audio element', () => {
      const store = usePlayerStore()
      const audio = store.initAudio()
      expect(audio).toBeDefined()
      expect(audio.preload).toBe('metadata')
    })

    it('returns same audio element on subsequent calls', () => {
      const store = usePlayerStore()
      const audio1 = store.initAudio()
      const audio2 = store.initAudio()
      expect(audio1).toBe(audio2)
    })
  })

  describe('play', () => {
    it('sets current track when playing a track', async () => {
      const store = usePlayerStore()
      await store.play(mockTrack)
      expect(store.currentTrack).toEqual(mockTrack)
    })

    it('adds track to queue if not present', async () => {
      const store = usePlayerStore()
      await store.play(mockTrack)
      expect(store.queue).toHaveLength(1)
      expect(store.queue[0].id).toBe(mockTrack.id)
    })

    it('sets queue index when playing a track', async () => {
      const store = usePlayerStore()
      await store.play(mockTrack)
      expect(store.queueIndex).toBe(0)
    })

    it('calls audio play method', async () => {
      const store = usePlayerStore()
      const audio = store.initAudio() as unknown as MockAudio
      await store.play(mockTrack)
      expect(audio.play).toHaveBeenCalled()
    })
  })

  describe('pause', () => {
    it('calls audio pause method', async () => {
      const store = usePlayerStore()
      const audio = store.initAudio() as unknown as MockAudio
      await store.play(mockTrack)
      store.pause()
      expect(audio.pause).toHaveBeenCalled()
    })
  })

  describe('stop', () => {
    it('pauses audio and resets time', async () => {
      const store = usePlayerStore()
      const audio = store.initAudio() as unknown as MockAudio
      await store.play(mockTrack)
      store.stop()
      expect(audio.pause).toHaveBeenCalled()
      expect(audio.currentTime).toBe(0)
    })

    it('resets playing state', async () => {
      const store = usePlayerStore()
      await store.play(mockTrack)
      store.isPlaying = true
      store.stop()
      expect(store.isPlaying).toBe(false)
      expect(store.isPaused).toBe(false)
    })
  })

  describe('togglePlay', () => {
    it('pauses when playing', async () => {
      const store = usePlayerStore()
      const audio = store.initAudio() as unknown as MockAudio
      await store.play(mockTrack)
      store.isPlaying = true
      store.togglePlay()
      expect(audio.pause).toHaveBeenCalled()
    })

    it('plays when paused', async () => {
      const store = usePlayerStore()
      const audio = store.initAudio() as unknown as MockAudio
      await store.play(mockTrack)
      store.isPlaying = false
      await store.togglePlay()
      expect(audio.play).toHaveBeenCalled()
    })
  })

  describe('seek', () => {
    it('sets currentTime on audio element', async () => {
      const store = usePlayerStore()
      const audio = store.initAudio() as unknown as MockAudio
      store.duration = 180
      store.seek(90)
      expect(audio.currentTime).toBe(90)
      expect(store.currentTime).toBe(90)
    })

    it('clamps to 0 for negative values', () => {
      const store = usePlayerStore()
      store.initAudio()
      store.duration = 180
      store.seek(-10)
      expect(store.currentTime).toBe(0)
    })

    it('clamps to duration for values exceeding duration', () => {
      const store = usePlayerStore()
      const audio = store.initAudio() as unknown as MockAudio
      store.duration = 180
      store.seek(200)
      expect(audio.currentTime).toBe(180)
    })
  })

  describe('seekByPercent', () => {
    it('seeks to correct time based on percentage', () => {
      const store = usePlayerStore()
      store.initAudio()
      store.duration = 200
      store.seekByPercent(50)
      expect(store.currentTime).toBe(100)
    })
  })

  describe('volume', () => {
    it('sets volume within bounds', () => {
      const store = usePlayerStore()
      store.setVolume(0.5)
      expect(store.volume).toBe(0.5)
    })

    it('clamps volume to 0 minimum', () => {
      const store = usePlayerStore()
      store.setVolume(-0.5)
      expect(store.volume).toBe(0)
    })

    it('clamps volume to 1 maximum', () => {
      const store = usePlayerStore()
      store.setVolume(1.5)
      expect(store.volume).toBe(1)
    })

    it('saves volume to localStorage', () => {
      const store = usePlayerStore()
      store.setVolume(0.7)
      expect(localStorageMock.setItem).toHaveBeenCalledWith('player_volume', '0.7')
    })
  })

  describe('mute', () => {
    it('toggles mute state', () => {
      const store = usePlayerStore()
      expect(store.isMuted).toBe(false)
      store.toggleMute()
      expect(store.isMuted).toBe(true)
      store.toggleMute()
      expect(store.isMuted).toBe(false)
    })

    it('saves mute state to localStorage', () => {
      const store = usePlayerStore()
      store.toggleMute()
      expect(localStorageMock.setItem).toHaveBeenCalledWith('player_muted', 'true')
    })
  })

  describe('shuffle', () => {
    it('toggles shuffle state', () => {
      const store = usePlayerStore()
      store.queue = [mockTrack, mockTrack2, mockTrack3]
      store.currentTrack = mockTrack
      store.queueIndex = 0
      expect(store.isShuffled).toBe(false)
      store.toggleShuffle()
      expect(store.isShuffled).toBe(true)
    })

    it('keeps current track at the beginning when shuffling', () => {
      const store = usePlayerStore()
      store.queue = [mockTrack, mockTrack2, mockTrack3]
      store.currentTrack = mockTrack
      store.queueIndex = 0
      store.toggleShuffle()
      expect(store.queue[0]).toEqual(mockTrack)
      expect(store.queueIndex).toBe(0)
    })
  })

  describe('repeat modes', () => {
    it('sets repeat mode', () => {
      const store = usePlayerStore()
      store.setRepeatMode('all')
      expect(store.repeatMode).toBe('all')
    })

    it('cycles through repeat modes', () => {
      const store = usePlayerStore()
      expect(store.repeatMode).toBe('off')
      store.cycleRepeatMode()
      expect(store.repeatMode).toBe('all')
      store.cycleRepeatMode()
      expect(store.repeatMode).toBe('one')
      store.cycleRepeatMode()
      expect(store.repeatMode).toBe('off')
    })
  })

  describe('queue management', () => {
    it('adds tracks to queue', () => {
      const store = usePlayerStore()
      store.addToQueue(mockTrack)
      expect(store.queue).toHaveLength(1)
      expect(store.queue[0]).toEqual(mockTrack)
    })

    it('adds multiple tracks to queue', () => {
      const store = usePlayerStore()
      store.addToQueue([mockTrack, mockTrack2])
      expect(store.queue).toHaveLength(2)
    })

    it('plays next adds track after current', async () => {
      const store = usePlayerStore()
      await store.play(mockTrack)
      store.playNext(mockTrack2)
      expect(store.queue[1]).toEqual(mockTrack2)
    })

    it('removes track from queue', () => {
      const store = usePlayerStore()
      store.queue = [mockTrack, mockTrack2, mockTrack3]
      store.queueIndex = 0
      store.removeFromQueue(1)
      expect(store.queue).toHaveLength(2)
      expect(store.queue).not.toContain(mockTrack2)
    })

    it('adjusts queue index when removing track before current', () => {
      const store = usePlayerStore()
      store.queue = [mockTrack, mockTrack2, mockTrack3]
      store.queueIndex = 2
      store.removeFromQueue(0)
      expect(store.queueIndex).toBe(1)
    })

    it('clears queue', async () => {
      const store = usePlayerStore()
      await store.play(mockTrack)
      store.addToQueue(mockTrack2)
      store.clearQueue()
      expect(store.queue).toHaveLength(0)
      expect(store.currentTrack).toBeNull()
      expect(store.queueIndex).toBe(-1)
    })

    it('reorders queue', () => {
      const store = usePlayerStore()
      store.queue = [mockTrack, mockTrack2, mockTrack3]
      store.queueIndex = 0
      store.reorderQueue(2, 0)
      expect(store.queue[0]).toEqual(mockTrack3)
      expect(store.queue[1]).toEqual(mockTrack)
    })

    it('sets queue and starts playback', async () => {
      const store = usePlayerStore()
      const tracks = [mockTrack, mockTrack2, mockTrack3]
      await store.setQueue(tracks, 1)
      expect(store.queue).toHaveLength(3)
      expect(store.queueIndex).toBe(1)
      expect(store.currentTrack).toEqual(mockTrack2)
    })
  })

  describe('navigation', () => {
    it('plays next track', async () => {
      const store = usePlayerStore()
      store.queue = [mockTrack, mockTrack2]
      store.queueIndex = 0
      store.currentTrack = mockTrack
      await store.next()
      expect(store.queueIndex).toBe(1)
    })

    it('wraps to start with repeat all', async () => {
      const store = usePlayerStore()
      store.queue = [mockTrack, mockTrack2]
      store.queueIndex = 1
      store.repeatMode = 'all'
      await store.next()
      expect(store.queueIndex).toBe(0)
    })

    it('stops at end with repeat off', async () => {
      const store = usePlayerStore()
      const audio = store.initAudio() as unknown as MockAudio
      store.queue = [mockTrack, mockTrack2]
      store.queueIndex = 1
      store.repeatMode = 'off'
      await store.next()
      expect(audio.pause).toHaveBeenCalled()
    })

    it('restarts track if more than 3 seconds in on previous', async () => {
      const store = usePlayerStore()
      const audio = store.initAudio() as unknown as MockAudio
      store.queue = [mockTrack, mockTrack2]
      store.queueIndex = 1
      store.currentTime = 5
      await store.previous()
      expect(audio.currentTime).toBe(0)
      expect(store.queueIndex).toBe(1) // Still on same track
    })

    it('goes to previous track if less than 3 seconds in', async () => {
      const store = usePlayerStore()
      store.queue = [mockTrack, mockTrack2]
      store.queueIndex = 1
      store.currentTime = 2
      await store.previous()
      expect(store.queueIndex).toBe(0)
    })

    it('wraps to end with repeat all on previous', async () => {
      const store = usePlayerStore()
      store.queue = [mockTrack, mockTrack2]
      store.queueIndex = 0
      store.currentTime = 1
      store.repeatMode = 'all'
      await store.previous()
      expect(store.queueIndex).toBe(1)
    })
  })

  describe('cleanup', () => {
    it('cleans up audio element', () => {
      const store = usePlayerStore()
      const audio = store.initAudio() as unknown as MockAudio
      store.cleanup()
      expect(audio.pause).toHaveBeenCalled()
    })
  })
})
