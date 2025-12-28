// User types
export interface User {
  id: string
  email: string
  username: string
  avatar_url?: string | null
  created_at: string
}

export interface UserMe extends User {
  preferences?: Record<string, unknown> | null
  last_login_at?: string | null
  is_active: boolean
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  expires_in: number
}

export interface AuthResponse {
  user: User
  tokens: AuthTokens
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

// Song/Track types - matches backend SongResponse schema
export interface Song {
  id: string // UUID
  title: string
  artist: string | null
  album: string | null
  genre: string | null
  year: number | null
  duration_seconds: number
  file_format: string
  play_count: number
  last_played_at: string | null
  is_favorite: boolean
  rating: number | null
  cover_art_path: string | null
  created_at: string
}

// Extended song details - matches backend SongDetailResponse schema
export interface SongDetail extends Song {
  album_artist: string | null
  track_number: number | null
  disc_number: number | null
  file_size_bytes: number
  bitrate: number | null
  sample_rate: number | null
  lyrics: string | null
  bpm: number | null
  energy: number | null
  valence: number | null
}

// Song update - matches backend SongUpdate schema
export interface SongUpdate {
  title?: string
  artist?: string
  album?: string
  genre?: string
  year?: number
  lyrics?: string
  is_favorite?: boolean
  rating?: number
}

// Song upload response - matches backend SongUploadResponse schema
export interface SongUploadResponse {
  id: string
  title: string
  artist: string | null
  status?: string
  message?: string
}

// Batch upload response - matches backend SongBatchUploadResponse schema
export interface SongBatchUploadResponse {
  songs: SongUploadResponse[]
  errors: Array<{ filename: string; error: string }>
  total_files: number
  successful: number
  failed: number
}

// Song list response - matches backend SongListResponse schema
export interface SongListResponse {
  items: Song[]
  total: number
  page: number
  limit: number
  pages: number
}

// Song filters - matches backend SongFilters schema
export interface SongFilters {
  search?: string
  artist?: string
  album?: string
  genre?: string
  is_favorite?: boolean
  year_from?: number
  year_to?: number
  sort?: 'title' | 'artist' | 'album' | 'created_at' | 'play_count' | 'last_played_at'
  order?: 'asc' | 'desc'
}

// Legacy Track alias for backward compatibility
export type Track = Song

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

// Mood chain types - matches backend schemas/mood_chain.py
export type TransitionStyle = 'smooth' | 'random' | 'energy_flow' | 'genre_match'

export interface MoodChainSong {
  song_id: string
  position: number
  transition_weight: number
  added_at: string
  title: string
  artist: string | null
  album: string | null
  duration_seconds: number
  cover_art_path: string | null
  energy: number | null
  valence: number | null
  bpm: number | null
  genre: string | null
}

export interface MoodChainTransition {
  id: string
  from_song_id: string
  to_song_id: string
  weight: number
  play_count: number
}

export interface MoodChain {
  id: string
  name: string
  description: string | null
  cover_image_path: string | null
  transition_style: TransitionStyle
  auto_advance: boolean
  auto_advance_delay_seconds: number
  is_auto_generated: boolean
  song_count: number
  play_count: number
  last_played_at: string | null
  created_at: string
  updated_at: string
}

export interface MoodChainDetail extends MoodChain {
  songs: MoodChainSong[]
  transitions: MoodChainTransition[]
}

export interface MoodChainListResponse {
  items: MoodChain[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface MoodChainCreate {
  name: string
  description?: string | null
  transition_style?: TransitionStyle
  auto_advance?: boolean
  auto_advance_delay_seconds?: number
  song_ids?: string[]
}

export interface MoodChainUpdate {
  name?: string
  description?: string | null
  transition_style?: TransitionStyle
  auto_advance?: boolean
  auto_advance_delay_seconds?: number
  cover_image_path?: string | null
}

export interface MoodChainFromHistoryRequest {
  name: string
  description?: string | null
  from_date?: string
  to_date?: string
  min_plays?: number
}

export interface AddSongToMoodChainRequest {
  song_id: string
  position?: number
}

export interface TransitionUpdate {
  from_song_id: string
  to_song_id: string
  weight: number
}

export interface UpdateTransitionsRequest {
  transitions: TransitionUpdate[]
}

export interface NextSongSuggestion {
  song_id: string
  title: string
  artist: string | null
  album: string | null
  duration_seconds: number
  cover_art_path: string | null
  weight: number
  reason: string
}

export interface NextSongResponse {
  suggestions: NextSongSuggestion[]
}

export interface TransitionPlayedRequest {
  from_song_id: string
  to_song_id: string
}

// Legacy types for backward compatibility
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

// Statistics types - matches backend schemas/stats.py

export type StatsPeriod = 'day' | 'week' | 'month' | 'year' | 'all'

export type ContextType = 'library' | 'playlist' | 'mood_chain' | 'search' | 'recommendation'

export interface HourlyListeningCount {
  hour: number
  count: number
}

export interface DailyListeningCount {
  day: string // ISO format date string (YYYY-MM-DD)
  count: number
}

export interface StatsOverview {
  total_plays: number
  total_duration_seconds: number
  unique_songs: number
  unique_artists: number
  most_played_genre: string | null
  listening_by_hour: HourlyListeningCount[]
  listening_by_day: DailyListeningCount[]
}

export interface TopSongItem {
  song: Song
  play_count: number
}

export interface TopSongsResponse {
  items: TopSongItem[]
}

export interface TopArtistItem {
  artist: string
  play_count: number
  songs: Song[]
}

export interface TopArtistsResponse {
  items: TopArtistItem[]
}

export interface ListeningHistoryItem {
  id: string
  song_id: string
  played_at: string
  played_duration_seconds: number | null
  completed: boolean
  skipped: boolean
  context_type: ContextType | null
  context_id: string | null
  device_type: string | null
  song: Song
}

export interface ListeningHistoryResponse {
  items: ListeningHistoryItem[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface PlayRecordRequest {
  song_id: string
  duration_listened_seconds: number
  completed?: boolean
  context_type?: ContextType
  context_id?: string
  device_type?: string
}

export interface PlayRecordResponse {
  success: boolean
  id: string
  played_at: string
}

// Legacy types for backward compatibility
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
