// User types
export interface User {
  id: number
  email: string
  username: string
  created_at: string
  updated_at: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterCredentials {
  email: string
  username: string
  password: string
}

// Track types
export interface Track {
  id: number
  title: string
  artist: string
  album?: string
  duration: number // in seconds
  file_path: string
  cover_url?: string
  genre?: string
  year?: number
  play_count: number
  is_favorite: boolean
  created_at: string
  updated_at: string
}

// Playlist types
export interface Playlist {
  id: number
  name: string
  description?: string
  cover_url?: string
  tracks: Track[]
  track_count: number
  total_duration: number
  created_at: string
  updated_at: string
}

// Mood chain types
export interface MoodChain {
  id: number
  name: string
  description?: string
  tags: string[]
  transition_style: 'smooth' | 'energetic' | 'random'
  tracks: MoodChainTrack[]
  created_at: string
  updated_at: string
}

export interface MoodChainTrack {
  track: Track
  position: number
  transition_weight: number
}

// Player types
export interface PlayerState {
  currentTrack: Track | null
  isPlaying: boolean
  currentTime: number
  duration: number
  volume: number
  isMuted: boolean
  isShuffled: boolean
  repeatMode: 'off' | 'all' | 'one'
  queue: Track[]
  queueIndex: number
}

// Statistics types
export interface ListeningStats {
  total_hours: number
  total_plays: number
  unique_tracks: number
  top_tracks: TrackStat[]
  top_artists: ArtistStat[]
  genres_distribution: GenreStat[]
  daily_activity: DailyActivity[]
  hourly_heatmap: HourlyActivity[]
}

export interface TrackStat {
  track: Track
  play_count: number
}

export interface ArtistStat {
  artist: string
  play_count: number
}

export interface GenreStat {
  genre: string
  percentage: number
}

export interface DailyActivity {
  date: string
  play_count: number
}

export interface HourlyActivity {
  hour: number
  day_of_week: number
  play_count: number
}

// UI types
export interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  duration?: number
}

export interface ModalState {
  isOpen: boolean
  component: string | null
  props?: Record<string, unknown>
}

export type Theme = 'light' | 'dark' | 'system'

// API types
export interface ApiError {
  message: string
  status: number
  details?: Record<string, string[]>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// Route meta types
export interface RouteMeta extends Record<string, unknown> {
  requiresAuth?: boolean
  title?: string
}
