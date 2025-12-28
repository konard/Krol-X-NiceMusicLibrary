/**
 * Mood Chains API Service
 * Handles all API calls related to mood chain operations
 */
import { apiService } from './api'
import type {
  MoodChain,
  MoodChainDetail,
  MoodChainListResponse,
  MoodChainCreate,
  MoodChainUpdate,
  MoodChainFromHistoryRequest,
  AddSongToMoodChainRequest,
  UpdateTransitionsRequest,
  NextSongResponse,
} from '@/types'

const MOOD_CHAINS_BASE_URL = '/mood-chains'

/**
 * Get paginated list of user's mood chains
 */
export async function getMoodChains(
  page = 1,
  limit = 20
): Promise<MoodChainListResponse> {
  const response = await apiService.get<MoodChainListResponse>(MOOD_CHAINS_BASE_URL, {
    page,
    limit,
  })
  return response.data
}

/**
 * Get a single mood chain by ID with songs and transitions
 */
export async function getMoodChain(id: string): Promise<MoodChainDetail> {
  const response = await apiService.get<MoodChainDetail>(`${MOOD_CHAINS_BASE_URL}/${id}`)
  return response.data
}

/**
 * Create a new mood chain
 */
export async function createMoodChain(data: MoodChainCreate): Promise<MoodChain> {
  const response = await apiService.post<MoodChain>(MOOD_CHAINS_BASE_URL, data)
  return response.data
}

/**
 * Update a mood chain's metadata
 */
export async function updateMoodChain(
  id: string,
  data: MoodChainUpdate
): Promise<MoodChain> {
  const response = await apiService.patch<MoodChain>(`${MOOD_CHAINS_BASE_URL}/${id}`, data)
  return response.data
}

/**
 * Delete a mood chain
 */
export async function deleteMoodChain(id: string): Promise<void> {
  await apiService.delete(`${MOOD_CHAINS_BASE_URL}/${id}`)
}

/**
 * Add a song to a mood chain
 */
export async function addSongToMoodChain(
  moodChainId: string,
  data: AddSongToMoodChainRequest
): Promise<MoodChainDetail> {
  const response = await apiService.post<MoodChainDetail>(
    `${MOOD_CHAINS_BASE_URL}/${moodChainId}/songs`,
    data
  )
  return response.data
}

/**
 * Remove a song from a mood chain
 */
export async function removeSongFromMoodChain(
  moodChainId: string,
  songId: string
): Promise<MoodChainDetail> {
  const response = await apiService.delete<MoodChainDetail>(
    `${MOOD_CHAINS_BASE_URL}/${moodChainId}/songs/${songId}`
  )
  return response.data
}

/**
 * Reorder songs in a mood chain
 */
export async function reorderMoodChainSongs(
  moodChainId: string,
  songIds: string[]
): Promise<MoodChainDetail> {
  const response = await apiService.put<MoodChainDetail>(
    `${MOOD_CHAINS_BASE_URL}/${moodChainId}/songs/order`,
    { song_ids: songIds }
  )
  return response.data
}

/**
 * Update transitions in a mood chain
 */
export async function updateTransitions(
  moodChainId: string,
  data: UpdateTransitionsRequest
): Promise<MoodChainDetail> {
  const response = await apiService.put<MoodChainDetail>(
    `${MOOD_CHAINS_BASE_URL}/${moodChainId}/transitions`,
    data
  )
  return response.data
}

/**
 * Create a mood chain from listening history
 */
export async function createFromHistory(
  data: MoodChainFromHistoryRequest
): Promise<MoodChainDetail> {
  const response = await apiService.post<MoodChainDetail>(
    `${MOOD_CHAINS_BASE_URL}/from-history`,
    data
  )
  return response.data
}

/**
 * Get next song suggestions for mood chain playback
 */
export async function getNextSongSuggestions(
  moodChainId: string,
  currentSongId: string,
  excludeRecent = 0
): Promise<NextSongResponse> {
  const response = await apiService.get<NextSongResponse>(
    `${MOOD_CHAINS_BASE_URL}/${moodChainId}/next`,
    {
      current_song_id: currentSongId,
      exclude_recent: excludeRecent,
    }
  )
  return response.data
}

/**
 * Record that a transition was played (for learning)
 */
export async function recordTransitionPlayed(
  moodChainId: string,
  fromSongId: string,
  toSongId: string
): Promise<{ success: boolean }> {
  const response = await apiService.post<{ success: boolean }>(
    `${MOOD_CHAINS_BASE_URL}/${moodChainId}/transition-played`,
    {
      from_song_id: fromSongId,
      to_song_id: toSongId,
    }
  )
  return response.data
}

/**
 * Format duration in seconds to MM:SS format
 */
export function formatDuration(seconds: number): string {
  if (!seconds || !isFinite(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

/**
 * Get cover image URL with fallback
 */
export function getCoverUrl(coverArtPath: string | null): string | null {
  if (!coverArtPath) return null
  const baseUrl = import.meta.env.VITE_API_URL || '/api/v1'
  return `${baseUrl}${coverArtPath}`
}
