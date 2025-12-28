/**
 * Song API Service
 *
 * Handles all API calls related to song management including:
 * - CRUD operations for songs
 * - File uploads (single and batch)
 * - Audio streaming
 * - Cover art retrieval
 */

import { apiService } from './api'
import type {
  Song,
  SongDetail,
  SongUpdate,
  SongUploadResponse,
  SongBatchUploadResponse,
  SongListResponse,
  SongFilters,
} from '@/types'

const BASE_URL = '/songs'

/**
 * Get a paginated list of songs with optional filters
 */
export async function getSongs(
  page = 1,
  limit = 20,
  filters?: SongFilters
): Promise<SongListResponse> {
  const params: Record<string, unknown> = {
    page,
    limit,
    ...filters,
  }

  // Remove undefined values
  Object.keys(params).forEach((key) => {
    if (params[key] === undefined || params[key] === null || params[key] === '') {
      delete params[key]
    }
  })

  const response = await apiService.get<SongListResponse>(BASE_URL, params)
  return response.data
}

/**
 * Get detailed information about a specific song
 */
export async function getSongById(songId: string): Promise<SongDetail> {
  const response = await apiService.get<SongDetail>(`${BASE_URL}/${songId}`)
  return response.data
}

/**
 * Upload a single song file
 *
 * @param file - The audio file to upload
 * @param metadata - Optional metadata overrides (title, artist, album)
 * @param onProgress - Callback for upload progress (0-100)
 */
export async function uploadSong(
  file: File,
  metadata?: {
    title?: string
    artist?: string
    album?: string
  },
  onProgress?: (progress: number) => void
): Promise<SongUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  if (metadata?.title) {
    formData.append('title', metadata.title)
  }
  if (metadata?.artist) {
    formData.append('artist', metadata.artist)
  }
  if (metadata?.album) {
    formData.append('album', metadata.album)
  }

  const response = await apiService.upload<SongUploadResponse>(
    BASE_URL,
    formData,
    onProgress
  )
  return response.data
}

/**
 * Upload multiple song files at once
 *
 * @param files - Array of audio files to upload
 * @param onProgress - Callback for overall progress (0-100)
 */
export async function uploadSongsBatch(
  files: File[],
  onProgress?: (progress: number) => void
): Promise<SongBatchUploadResponse> {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })

  const response = await apiService.upload<SongBatchUploadResponse>(
    `${BASE_URL}/batch`,
    formData,
    onProgress
  )
  return response.data
}

/**
 * Update song metadata
 */
export async function updateSong(
  songId: string,
  data: SongUpdate
): Promise<Song> {
  const response = await apiService.patch<Song>(`${BASE_URL}/${songId}`, data)
  return response.data
}

/**
 * Delete a song and its associated files
 */
export async function deleteSong(songId: string): Promise<void> {
  await apiService.delete(`${BASE_URL}/${songId}`)
}

/**
 * Toggle favorite status for a song
 */
export async function toggleFavorite(songId: string, isFavorite: boolean): Promise<Song> {
  return updateSong(songId, { is_favorite: isFavorite })
}

/**
 * Get the streaming URL for a song
 * Note: This returns the URL, not the actual stream data
 */
export function getStreamUrl(songId: string): string {
  const baseUrl = import.meta.env.VITE_API_URL || '/api/v1'
  return `${baseUrl}${BASE_URL}/${songId}/stream`
}

/**
 * Get the cover art URL for a song
 * Note: This returns the URL, not the actual image data
 */
export function getCoverUrl(songId: string): string {
  const baseUrl = import.meta.env.VITE_API_URL || '/api/v1'
  return `${baseUrl}${BASE_URL}/${songId}/cover`
}

/**
 * Format duration from seconds to MM:SS or HH:MM:SS
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

/**
 * Validate if a file is a supported audio format
 */
export function isValidAudioFile(file: File): boolean {
  const supportedTypes = [
    'audio/mpeg', // mp3
    'audio/mp3',
    'audio/flac',
    'audio/ogg',
    'audio/wav',
    'audio/x-wav',
    'audio/mp4', // m4a
    'audio/x-m4a',
    'audio/aac',
  ]

  const supportedExtensions = ['.mp3', '.flac', '.ogg', '.wav', '.m4a', '.aac']
  const extension = '.' + file.name.split('.').pop()?.toLowerCase()

  return supportedTypes.includes(file.type) || supportedExtensions.includes(extension)
}

/**
 * Get human-readable file size
 */
export function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }

  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`
}

// Export all functions as a service object for consistency
export const songService = {
  getSongs,
  getSongById,
  uploadSong,
  uploadSongsBatch,
  updateSong,
  deleteSong,
  toggleFavorite,
  getStreamUrl,
  getCoverUrl,
  formatDuration,
  isValidAudioFile,
  formatFileSize,
}

export default songService
