/**
 * Statistics Service
 *
 * API client for statistics endpoints:
 * - Overview: aggregated stats by period
 * - Top Songs: most played songs
 * - Top Artists: most played artists
 * - History: listening history with pagination
 * - Play recording: track song plays
 */

import { apiService } from './api'
import type {
  StatsOverview,
  TopSongsResponse,
  TopArtistsResponse,
  ListeningHistoryResponse,
  PlayRecordRequest,
  PlayRecordResponse,
  StatsPeriod,
} from '@/types'

export interface HistoryFilters {
  from_date?: string
  to_date?: string
}

export const statsService = {
  /**
   * Get statistics overview for a period
   */
  async getOverview(period: StatsPeriod = 'all'): Promise<StatsOverview> {
    const response = await apiService.get<StatsOverview>('/stats/overview', { period })
    return response.data
  },

  /**
   * Get top songs for a period
   */
  async getTopSongs(period: StatsPeriod = 'all', limit: number = 10): Promise<TopSongsResponse> {
    const response = await apiService.get<TopSongsResponse>('/stats/top-songs', { period, limit })
    return response.data
  },

  /**
   * Get top artists for a period
   */
  async getTopArtists(period: StatsPeriod = 'all', limit: number = 10): Promise<TopArtistsResponse> {
    const response = await apiService.get<TopArtistsResponse>('/stats/top-artists', { period, limit })
    return response.data
  },

  /**
   * Get listening history with pagination
   */
  async getHistory(
    page: number = 1,
    limit: number = 20,
    filters?: HistoryFilters
  ): Promise<ListeningHistoryResponse> {
    const params: Record<string, unknown> = { page, limit }
    if (filters?.from_date) params.from_date = filters.from_date
    if (filters?.to_date) params.to_date = filters.to_date

    const response = await apiService.get<ListeningHistoryResponse>('/stats/history', params)
    return response.data
  },

  /**
   * Record a song play event
   */
  async recordPlay(data: PlayRecordRequest): Promise<PlayRecordResponse> {
    const response = await apiService.post<PlayRecordResponse>('/stats/play', data)
    return response.data
  },
}
