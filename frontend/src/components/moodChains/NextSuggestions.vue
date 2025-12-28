<script setup lang="ts">
import { computed } from 'vue'
import type { NextSongSuggestion } from '@/types'
import { getCoverUrl } from '@/services/moodChains'

const props = defineProps<{
  suggestions: NextSongSuggestion[]
  countdown: number
  autoAdvance: boolean
}>()

const emit = defineEmits<{
  select: [songId: string]
}>()

const topSuggestion = computed(() => props.suggestions[0])
const otherSuggestions = computed(() => props.suggestions.slice(1, 3))

function handleSelect(songId: string) {
  emit('select', songId)
}

function getMatchPercent(weight: number): number {
  return Math.round(weight * 100)
}
</script>

<template>
  <div class="next-suggestions">
    <div class="suggestions-header">
      <h3>Next Song</h3>
      <span v-if="autoAdvance && countdown > 0" class="countdown">
        Auto-selecting in {{ countdown }}s
      </span>
    </div>

    <div class="suggestions-grid">
      <!-- Top suggestion (featured) -->
      <div
        v-if="topSuggestion"
        class="suggestion-card featured"
        @click="handleSelect(topSuggestion.song_id)"
      >
        <div class="card-cover">
          <img
            v-if="topSuggestion.cover_art_path"
            :src="getCoverUrl(topSuggestion.cover_art_path) || ''"
            :alt="topSuggestion.title"
          />
          <div v-else class="cover-placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M9 18V5l12-2v13" />
              <circle cx="6" cy="18" r="3" />
              <circle cx="18" cy="16" r="3" />
            </svg>
          </div>
          <div class="play-overlay">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5,3 19,12 5,21" />
            </svg>
          </div>
        </div>
        <div class="card-content">
          <span class="song-title">{{ topSuggestion.title }}</span>
          <span class="song-artist">{{ topSuggestion.artist || 'Unknown' }}</span>
          <div class="song-meta">
            <span class="match-score">{{ getMatchPercent(topSuggestion.weight) }}% match</span>
            <span class="match-reason">{{ topSuggestion.reason }}</span>
          </div>
        </div>
        <div v-if="autoAdvance && countdown > 0" class="countdown-bar">
          <div
            class="countdown-progress"
            :style="{ width: `${(countdown / 10) * 100}%` }"
          />
        </div>
      </div>

      <!-- Other suggestions -->
      <div
        v-for="suggestion in otherSuggestions"
        :key="suggestion.song_id"
        class="suggestion-card compact"
        @click="handleSelect(suggestion.song_id)"
      >
        <div class="card-cover small">
          <img
            v-if="suggestion.cover_art_path"
            :src="getCoverUrl(suggestion.cover_art_path) || ''"
            :alt="suggestion.title"
          />
          <div v-else class="cover-placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M9 18V5l12-2v13" />
              <circle cx="6" cy="18" r="3" />
              <circle cx="18" cy="16" r="3" />
            </svg>
          </div>
        </div>
        <div class="card-content">
          <span class="song-title">{{ suggestion.title }}</span>
          <span class="song-artist">{{ suggestion.artist || 'Unknown' }}</span>
        </div>
        <div class="match-badge">{{ getMatchPercent(suggestion.weight) }}%</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.next-suggestions {
  position: fixed;
  bottom: 100px;
  right: 2rem;
  width: 320px;
  background: var(--color-bg-primary, #fff);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--color-border, #e5e7eb);
  overflow: hidden;
  z-index: 50;
}

.suggestions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}

.suggestions-header h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-primary, #1f2937);
  margin: 0;
}

.countdown {
  font-size: 0.75rem;
  color: var(--color-accent-primary, #3b82f6);
  font-weight: 500;
}

.suggestions-grid {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* Featured suggestion card */
.suggestion-card {
  cursor: pointer;
  transition: all 0.15s ease;
}

.suggestion-card.featured {
  background: var(--color-bg-secondary, #f9fafb);
  border-radius: 10px;
  overflow: hidden;
}

.suggestion-card.featured:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.suggestion-card.featured .card-cover {
  position: relative;
  height: 140px;
}

.suggestion-card.featured .card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.suggestion-card.featured .cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: rgba(255, 255, 255, 0.7);
}

.suggestion-card.featured .cover-placeholder svg {
  width: 40px;
  height: 40px;
}

.play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  color: white;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.suggestion-card.featured:hover .play-overlay {
  opacity: 1;
}

.play-overlay svg {
  width: 40px;
  height: 40px;
}

.suggestion-card.featured .card-content {
  padding: 0.875rem;
}

.suggestion-card.featured .song-title {
  display: block;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text-primary, #1f2937);
  margin-bottom: 0.125rem;
}

.suggestion-card.featured .song-artist {
  display: block;
  font-size: 0.8rem;
  color: var(--color-text-secondary, #6b7280);
  margin-bottom: 0.5rem;
}

.song-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.match-score {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-accent-success, #22c55e);
}

.match-reason {
  font-size: 0.7rem;
  color: var(--color-text-muted, #9ca3af);
}

.countdown-bar {
  height: 3px;
  background: var(--color-bg-tertiary, #e5e7eb);
}

.countdown-progress {
  height: 100%;
  background: var(--color-accent-primary, #3b82f6);
  transition: width 1s linear;
}

/* Compact suggestion cards */
.suggestion-card.compact {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  background: var(--color-bg-secondary, #f9fafb);
  border-radius: 8px;
}

.suggestion-card.compact:hover {
  background: var(--color-bg-tertiary, #e5e7eb);
}

.suggestion-card.compact .card-cover.small {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
}

.suggestion-card.compact .card-cover.small img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.suggestion-card.compact .cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: rgba(255, 255, 255, 0.7);
}

.suggestion-card.compact .cover-placeholder svg {
  width: 20px;
  height: 20px;
}

.suggestion-card.compact .card-content {
  flex: 1;
  min-width: 0;
}

.suggestion-card.compact .song-title {
  display: block;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-primary, #1f2937);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.suggestion-card.compact .song-artist {
  display: block;
  font-size: 0.7rem;
  color: var(--color-text-secondary, #6b7280);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.match-badge {
  padding: 0.25rem 0.5rem;
  background: rgba(34, 197, 94, 0.1);
  color: var(--color-accent-success, #22c55e);
  font-size: 0.7rem;
  font-weight: 600;
  border-radius: 4px;
}

/* Dark mode */
:root.dark .next-suggestions {
  background: var(--color-bg-primary, #1f2937);
  border-color: var(--color-border, #4b5563);
}

:root.dark .suggestions-header {
  border-color: var(--color-border, #4b5563);
}

:root.dark .suggestions-header h3 {
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .suggestion-card.featured {
  background: var(--color-bg-secondary, #374151);
}

:root.dark .suggestion-card.featured .song-title,
:root.dark .suggestion-card.compact .song-title {
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .suggestion-card.compact {
  background: var(--color-bg-secondary, #374151);
}

:root.dark .suggestion-card.compact:hover {
  background: var(--color-bg-tertiary, #4b5563);
}

:root.dark .countdown-bar {
  background: var(--color-bg-tertiary, #4b5563);
}
</style>
