<script setup lang="ts">
import { computed } from 'vue'
import type { MoodChain, TransitionStyle } from '@/types'
import { getCoverUrl } from '@/services/moodChains'

const props = defineProps<{
  chain: MoodChain
}>()

const emit = defineEmits<{
  click: []
}>()

const coverUrl = computed(() => getCoverUrl(props.chain.cover_image_path))

const transitionStyleLabel = computed(() => {
  const labels: Record<TransitionStyle, string> = {
    smooth: 'Smooth',
    random: 'Random',
    energy_flow: 'Energy Flow',
    genre_match: 'Genre Match',
  }
  return labels[props.chain.transition_style]
})

const transitionStyleIcon = computed(() => {
  const icons: Record<TransitionStyle, string> = {
    smooth: '🌊',
    random: '🎲',
    energy_flow: '⚡',
    genre_match: '🎵',
  }
  return icons[props.chain.transition_style]
})

const formattedDate = computed(() => {
  const date = new Date(props.chain.created_at)
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
})

function handleClick() {
  emit('click')
}
</script>

<template>
  <div
    class="mood-chain-card"
    @click="handleClick"
    role="button"
    tabindex="0"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
  >
    <!-- Cover Image -->
    <div class="card-cover">
      <img
        v-if="coverUrl"
        :src="coverUrl"
        :alt="chain.name"
        class="cover-image"
      />
      <div v-else class="cover-placeholder">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M9 18V5l12-2v13" />
          <circle cx="6" cy="18" r="3" />
          <circle cx="18" cy="16" r="3" />
        </svg>
      </div>
      <!-- Play overlay -->
      <div class="play-overlay">
        <button class="play-button" @click.stop="handleClick">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5,3 19,12 5,21" />
          </svg>
        </button>
      </div>
      <!-- Auto-generated badge -->
      <span v-if="chain.is_auto_generated" class="auto-badge">
        Auto
      </span>
    </div>

    <!-- Card Content -->
    <div class="card-content">
      <h3 class="chain-name">{{ chain.name }}</h3>
      <p v-if="chain.description" class="chain-description">
        {{ chain.description }}
      </p>

      <!-- Meta info -->
      <div class="chain-meta">
        <span class="meta-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 18V5l12-2v13" />
            <circle cx="6" cy="18" r="3" />
            <circle cx="18" cy="16" r="3" />
          </svg>
          {{ chain.song_count }} {{ chain.song_count === 1 ? 'song' : 'songs' }}
        </span>
        <span class="meta-item">
          <span class="style-icon">{{ transitionStyleIcon }}</span>
          {{ transitionStyleLabel }}
        </span>
      </div>

      <!-- Stats row -->
      <div class="chain-stats">
        <span v-if="chain.play_count > 0" class="stat-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5,3 19,12 5,21" />
          </svg>
          {{ chain.play_count }} plays
        </span>
        <span class="stat-item date">
          {{ formattedDate }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mood-chain-card {
  background: var(--color-bg-secondary, #f9fafb);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border: 1px solid var(--color-border, #e5e7eb);
}

.mood-chain-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px -5px rgba(0, 0, 0, 0.1);
}

.mood-chain-card:focus {
  outline: 2px solid var(--color-accent-primary, #3b82f6);
  outline-offset: 2px;
}

.card-cover {
  position: relative;
  aspect-ratio: 1;
  background: var(--color-bg-tertiary, #e5e7eb);
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: rgba(255, 255, 255, 0.7);
}

.cover-placeholder svg {
  width: 40%;
  height: 40%;
}

.play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.mood-chain-card:hover .play-overlay {
  opacity: 1;
}

.play-button {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--color-accent-primary, #3b82f6);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
  transition: transform 0.15s ease, background 0.15s ease;
}

.play-button:hover {
  transform: scale(1.1);
  background: var(--color-accent-secondary, #2563eb);
}

.play-button svg {
  width: 24px;
  height: 24px;
  margin-left: 4px;
}

.auto-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.card-content {
  padding: 1rem;
}

.chain-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary, #1f2937);
  margin: 0 0 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chain-description {
  font-size: 0.8rem;
  color: var(--color-text-secondary, #6b7280);
  margin: 0 0 0.75rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.chain-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  color: var(--color-text-secondary, #6b7280);
}

.meta-item svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.style-icon {
  font-size: 0.875rem;
}

.chain-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border, #e5e7eb);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  color: var(--color-text-muted, #9ca3af);
}

.stat-item svg {
  width: 12px;
  height: 12px;
}

.stat-item.date {
  margin-left: auto;
}

/* Dark mode */
:root.dark .mood-chain-card {
  background: var(--color-bg-secondary, #374151);
  border-color: var(--color-border, #4b5563);
}

:root.dark .card-cover {
  background: var(--color-bg-tertiary, #4b5563);
}

:root.dark .chain-name {
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .chain-stats {
  border-color: var(--color-border, #4b5563);
}
</style>
