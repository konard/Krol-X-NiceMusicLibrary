import { defineStore } from 'pinia'
import { ref, computed, watch, shallowRef } from 'vue'
import type { Track } from '@/types'
import { tokenManager } from '@/services/api'

export type RepeatMode = 'off' | 'all' | 'one'

// Volume persistence key
const VOLUME_STORAGE_KEY = 'player_volume'
const MUTED_STORAGE_KEY = 'player_muted'

export const usePlayerStore = defineStore('player', () => {
  // Audio element (shallowRef to avoid deep reactivity)
  const audio = shallowRef<HTMLAudioElement | null>(null)

  // State
  const currentTrack = ref<Track | null>(null)
  const queue = ref<Track[]>([])
  const queueIndex = ref(-1)
  const originalQueue = ref<Track[]>([]) // For unshuffle

  const isPlaying = ref(false)
  const isPaused = ref(false)
  const isLoading = ref(false)
  const hasError = ref(false)
  const errorMessage = ref<string | null>(null)

  const currentTime = ref(0)
  const duration = ref(0)
  const buffered = ref(0)

  const volume = ref(parseFloat(localStorage.getItem(VOLUME_STORAGE_KEY) || '1'))
  const isMuted = ref(localStorage.getItem(MUTED_STORAGE_KEY) === 'true')

  const isShuffled = ref(false)
  const repeatMode = ref<RepeatMode>('off')

  // Getters
  const progress = computed(() => {
    if (duration.value === 0) return 0
    return (currentTime.value / duration.value) * 100
  })

  const bufferedProgress = computed(() => {
    if (duration.value === 0) return 0
    return (buffered.value / duration.value) * 100
  })

  const formattedCurrentTime = computed(() => formatTime(currentTime.value))
  const formattedDuration = computed(() => formatTime(duration.value))

  const hasNext = computed(() => {
    if (repeatMode.value === 'all') return queue.value.length > 0
    return queueIndex.value < queue.value.length - 1
  })

  const hasPrevious = computed(() => {
    if (repeatMode.value === 'all') return queue.value.length > 0
    return queueIndex.value > 0
  })

  const currentTrackInQueue = computed(() => {
    if (queueIndex.value >= 0 && queueIndex.value < queue.value.length) {
      return queue.value[queueIndex.value]
    }
    return null
  })

  // Initialize audio element
  function initAudio(): HTMLAudioElement {
    if (!audio.value) {
      audio.value = new Audio()
      audio.value.preload = 'metadata'

      // Event listeners
      audio.value.addEventListener('timeupdate', handleTimeUpdate)
      audio.value.addEventListener('loadedmetadata', handleLoadedMetadata)
      audio.value.addEventListener('ended', handleEnded)
      audio.value.addEventListener('error', handleError)
      audio.value.addEventListener('waiting', () => { isLoading.value = true })
      audio.value.addEventListener('canplay', () => { isLoading.value = false })
      audio.value.addEventListener('playing', () => {
        isPlaying.value = true
        isPaused.value = false
        isLoading.value = false
      })
      audio.value.addEventListener('pause', () => {
        isPlaying.value = false
        isPaused.value = true
      })
      audio.value.addEventListener('progress', handleProgress)

      // Apply initial volume
      audio.value.volume = isMuted.value ? 0 : volume.value
    }
    return audio.value
  }

  // Event handlers
  function handleTimeUpdate() {
    if (audio.value) {
      currentTime.value = audio.value.currentTime
    }
  }

  function handleLoadedMetadata() {
    if (audio.value) {
      duration.value = audio.value.duration
      isLoading.value = false
    }
  }

  function handleProgress() {
    if (audio.value && audio.value.buffered.length > 0) {
      buffered.value = audio.value.buffered.end(audio.value.buffered.length - 1)
    }
  }

  function handleEnded() {
    if (repeatMode.value === 'one') {
      // Repeat current track
      seek(0)
      const audioEl = initAudio()
      audioEl.play().catch(handlePlayError)
    } else {
      next()
    }
  }

  function handleError(event: Event) {
    const audioEl = event.target as HTMLAudioElement
    hasError.value = true
    isLoading.value = false
    isPlaying.value = false

    if (audioEl.error) {
      switch (audioEl.error.code) {
        case MediaError.MEDIA_ERR_ABORTED:
          errorMessage.value = 'Playback aborted'
          break
        case MediaError.MEDIA_ERR_NETWORK:
          errorMessage.value = 'Network error'
          break
        case MediaError.MEDIA_ERR_DECODE:
          errorMessage.value = 'Decoding error'
          break
        case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
          errorMessage.value = 'Format not supported'
          break
        default:
          errorMessage.value = 'Unknown error'
      }
    }
  }

  function handlePlayError(error: Error) {
    console.error('Play error:', error)
    hasError.value = true
    errorMessage.value = error.message
    isPlaying.value = false
  }

  // Get streaming URL with auth
  function getStreamUrl(track: Track): string {
    const baseUrl = import.meta.env.VITE_API_URL || '/api/v1'
    const token = tokenManager.getAccessToken()
    // For audio elements, we need to include the token in the URL
    // since we can't set headers on the audio element directly
    return `${baseUrl}/songs/${track.id}/stream?token=${token}`
  }

  // Actions
  async function play(track?: Track): Promise<void> {
    hasError.value = false
    errorMessage.value = null

    const audioEl = initAudio()

    if (track) {
      // Play specific track
      currentTrack.value = track

      // Check if track is in queue
      const trackIndexInQueue = queue.value.findIndex(t => t.id === track.id)
      if (trackIndexInQueue !== -1) {
        queueIndex.value = trackIndexInQueue
      } else {
        // Add to queue if not present
        queue.value.push(track)
        queueIndex.value = queue.value.length - 1
      }

      isLoading.value = true
      audioEl.src = getStreamUrl(track)
      audioEl.load()

      try {
        await audioEl.play()
        updateMediaSession()
      } catch (error) {
        handlePlayError(error as Error)
      }
    } else if (currentTrack.value) {
      // Resume current track
      try {
        await audioEl.play()
      } catch (error) {
        handlePlayError(error as Error)
      }
    }
  }

  function pause(): void {
    const audioEl = audio.value
    if (audioEl) {
      audioEl.pause()
    }
  }

  function resume(): void {
    play()
  }

  function stop(): void {
    const audioEl = audio.value
    if (audioEl) {
      audioEl.pause()
      audioEl.currentTime = 0
    }
    isPlaying.value = false
    isPaused.value = false
    currentTime.value = 0
  }

  function togglePlay(): void {
    if (isPlaying.value) {
      pause()
    } else {
      play()
    }
  }

  async function next(): Promise<void> {
    if (queue.value.length === 0) return

    let nextIndex = queueIndex.value + 1

    if (nextIndex >= queue.value.length) {
      if (repeatMode.value === 'all') {
        nextIndex = 0
      } else {
        // End of queue
        stop()
        return
      }
    }

    queueIndex.value = nextIndex
    const nextTrack = queue.value[nextIndex]
    if (nextTrack) {
      await play(nextTrack)
    }
  }

  async function previous(): Promise<void> {
    // If more than 3 seconds into track, restart it
    if (currentTime.value > 3) {
      seek(0)
      return
    }

    if (queue.value.length === 0) return

    let prevIndex = queueIndex.value - 1

    if (prevIndex < 0) {
      if (repeatMode.value === 'all') {
        prevIndex = queue.value.length - 1
      } else {
        // Beginning of queue, restart current
        seek(0)
        return
      }
    }

    queueIndex.value = prevIndex
    const prevTrack = queue.value[prevIndex]
    if (prevTrack) {
      await play(prevTrack)
    }
  }

  function seek(time: number): void {
    const audioEl = audio.value
    if (audioEl) {
      audioEl.currentTime = Math.max(0, Math.min(time, duration.value))
      currentTime.value = audioEl.currentTime
    }
  }

  function seekByPercent(percent: number): void {
    const time = (percent / 100) * duration.value
    seek(time)
  }

  function setVolume(newVolume: number): void {
    volume.value = Math.max(0, Math.min(1, newVolume))
    localStorage.setItem(VOLUME_STORAGE_KEY, volume.value.toString())

    if (audio.value && !isMuted.value) {
      audio.value.volume = volume.value
    }
  }

  function toggleMute(): void {
    isMuted.value = !isMuted.value
    localStorage.setItem(MUTED_STORAGE_KEY, isMuted.value.toString())

    if (audio.value) {
      audio.value.volume = isMuted.value ? 0 : volume.value
    }
  }

  function toggleShuffle(): void {
    if (isShuffled.value) {
      // Restore original order
      const currentTrackId = currentTrack.value?.id
      queue.value = [...originalQueue.value]
      if (currentTrackId) {
        queueIndex.value = queue.value.findIndex(t => t.id === currentTrackId)
      }
    } else {
      // Save original and shuffle
      originalQueue.value = [...queue.value]
      const currentTrackItem = currentTrack.value
      const remaining = queue.value.filter(t => t.id !== currentTrackItem?.id)

      // Fisher-Yates shuffle
      for (let i = remaining.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        ;[remaining[i], remaining[j]] = [remaining[j], remaining[i]]
      }

      // Current track stays at the beginning
      if (currentTrackItem) {
        queue.value = [currentTrackItem, ...remaining]
        queueIndex.value = 0
      } else {
        queue.value = remaining
      }
    }
    isShuffled.value = !isShuffled.value
  }

  function setRepeatMode(mode: RepeatMode): void {
    repeatMode.value = mode
  }

  function cycleRepeatMode(): void {
    const modes: RepeatMode[] = ['off', 'all', 'one']
    const currentIndex = modes.indexOf(repeatMode.value)
    repeatMode.value = modes[(currentIndex + 1) % modes.length]
  }

  // Queue management
  function addToQueue(tracks: Track | Track[]): void {
    const tracksArray = Array.isArray(tracks) ? tracks : [tracks]
    queue.value.push(...tracksArray)
    if (!isShuffled.value) {
      originalQueue.value.push(...tracksArray)
    }
  }

  function playNext(track: Track): void {
    const insertIndex = queueIndex.value + 1
    queue.value.splice(insertIndex, 0, track)
    if (!isShuffled.value) {
      originalQueue.value.splice(insertIndex, 0, track)
    }
  }

  function removeFromQueue(index: number): void {
    if (index < 0 || index >= queue.value.length) return

    queue.value.splice(index, 1)
    if (!isShuffled.value && index < originalQueue.value.length) {
      originalQueue.value.splice(index, 1)
    }

    // Adjust queue index if needed
    if (index < queueIndex.value) {
      queueIndex.value--
    } else if (index === queueIndex.value) {
      // Current track was removed
      if (queue.value.length === 0) {
        stop()
        currentTrack.value = null
        queueIndex.value = -1
      } else if (queueIndex.value >= queue.value.length) {
        queueIndex.value = queue.value.length - 1
        play(queue.value[queueIndex.value])
      } else {
        play(queue.value[queueIndex.value])
      }
    }
  }

  function clearQueue(): void {
    stop()
    queue.value = []
    originalQueue.value = []
    queueIndex.value = -1
    currentTrack.value = null
  }

  function reorderQueue(fromIndex: number, toIndex: number): void {
    if (fromIndex < 0 || fromIndex >= queue.value.length) return
    if (toIndex < 0 || toIndex >= queue.value.length) return

    const [item] = queue.value.splice(fromIndex, 1)
    queue.value.splice(toIndex, 0, item)

    // Update queue index
    if (fromIndex === queueIndex.value) {
      queueIndex.value = toIndex
    } else if (fromIndex < queueIndex.value && toIndex >= queueIndex.value) {
      queueIndex.value--
    } else if (fromIndex > queueIndex.value && toIndex <= queueIndex.value) {
      queueIndex.value++
    }
  }

  function playFromQueue(index: number): void {
    if (index < 0 || index >= queue.value.length) return
    queueIndex.value = index
    play(queue.value[index])
  }

  function setQueue(tracks: Track[], startIndex = 0): void {
    queue.value = [...tracks]
    originalQueue.value = [...tracks]
    queueIndex.value = startIndex
    isShuffled.value = false

    if (tracks.length > 0 && startIndex >= 0 && startIndex < tracks.length) {
      play(tracks[startIndex])
    }
  }

  // Media Session API
  function updateMediaSession(): void {
    if (!('mediaSession' in navigator) || !currentTrack.value) return

    navigator.mediaSession.metadata = new MediaMetadata({
      title: currentTrack.value.title,
      artist: currentTrack.value.artist ?? undefined,
      album: currentTrack.value.album || '',
      artwork: currentTrack.value.cover_art_path ? [
        { src: currentTrack.value.cover_art_path, sizes: '512x512', type: 'image/jpeg' }
      ] : []
    })

    navigator.mediaSession.setActionHandler('play', () => play())
    navigator.mediaSession.setActionHandler('pause', () => pause())
    navigator.mediaSession.setActionHandler('previoustrack', () => previous())
    navigator.mediaSession.setActionHandler('nexttrack', () => next())
    navigator.mediaSession.setActionHandler('seekto', (details) => {
      if (details.seekTime !== undefined) {
        seek(details.seekTime)
      }
    })
  }

  // Watch for volume changes
  watch([volume, isMuted], () => {
    if (audio.value) {
      audio.value.volume = isMuted.value ? 0 : volume.value
    }
  })

  // Cleanup on unmount
  function cleanup(): void {
    if (audio.value) {
      audio.value.pause()
      audio.value.src = ''
      audio.value.removeEventListener('timeupdate', handleTimeUpdate)
      audio.value.removeEventListener('loadedmetadata', handleLoadedMetadata)
      audio.value.removeEventListener('ended', handleEnded)
      audio.value.removeEventListener('error', handleError)
      audio.value.removeEventListener('progress', handleProgress)
      audio.value = null
    }
  }

  return {
    // State
    currentTrack,
    queue,
    queueIndex,
    isPlaying,
    isPaused,
    isLoading,
    hasError,
    errorMessage,
    currentTime,
    duration,
    buffered,
    volume,
    isMuted,
    isShuffled,
    repeatMode,

    // Getters
    progress,
    bufferedProgress,
    formattedCurrentTime,
    formattedDuration,
    hasNext,
    hasPrevious,
    currentTrackInQueue,

    // Actions
    initAudio,
    play,
    pause,
    resume,
    stop,
    togglePlay,
    next,
    previous,
    seek,
    seekByPercent,
    setVolume,
    toggleMute,
    toggleShuffle,
    setRepeatMode,
    cycleRepeatMode,

    // Queue
    addToQueue,
    playNext,
    removeFromQueue,
    clearQueue,
    reorderQueue,
    playFromQueue,
    setQueue,

    // Cleanup
    cleanup,
  }
})

// Utility function
function formatTime(seconds: number): string {
  if (!isFinite(seconds) || isNaN(seconds)) return '0:00'

  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
