<script setup lang="ts">
import { ref, computed } from 'vue'
import type { MoodChainDetail, MoodChainSong } from '@/types'
import { useMoodChainStore } from '@/stores/moodChain'
import { formatDuration, getCoverUrl } from '@/services/moodChains'
import Button from '@/components/ui/Button.vue'
import TransitionWeightSlider from '@/components/moodChains/TransitionWeightSlider.vue'

const props = defineProps<{
  chain: MoodChainDetail
  isEditing?: boolean
  currentSongId?: string
}>()

const moodChainStore = useMoodChainStore()

const showAddSongSearch = ref(false)
const expandedTransitions = ref<string | null>(null)

const sortedSongs = computed(() => {
  return [...props.chain.songs].sort((a, b) => a.position - b.position)
})

// Get transitions from a specific song
function getTransitionsFrom(songId: string) {
  return props.chain.transitions.filter(t => t.from_song_id === songId)
}

// Get song by ID
function getSong(songId: string) {
  return props.chain.songs.find(s => s.song_id === songId)
}

// Handle play song
function handlePlaySong(song: MoodChainSong) {
  moodChainStore.startChainPlayback(song.song_id)
}

// Handle remove song
async function handleRemoveSong(songId: string) {
  await moodChainStore.removeSong(songId)
}

// Toggle transition expansion
function toggleTransitions(songId: string) {
  expandedTransitions.value = expandedTransitions.value === songId ? null : songId
}

// Handle transition weight update
async function handleWeightUpdate(fromId: string, toId: string, weight: number) {
  const transitions = props.chain.transitions.map(t => ({
    from_song_id: t.from_song_id,
    to_song_id: t.to_song_id,
    weight: t.from_song_id === fromId && t.to_song_id === toId ? weight : t.weight,
  }))
  await moodChainStore.updateTransitions(transitions)
}

// Drag and drop reordering
const draggedIndex = ref<number | null>(null)
const dropTargetIndex = ref<number | null>(null)

function handleDragStart(index: number) {
  draggedIndex.value = index
}

function handleDragOver(index: number, event: DragEvent) {
  event.preventDefault()
  dropTargetIndex.value = index
}

function handleDragEnd() {
  if (draggedIndex.value !== null && dropTargetIndex.value !== null) {
    const newOrder = [...sortedSongs.value]
    const [moved] = newOrder.splice(draggedIndex.value, 1)
    newOrder.splice(dropTargetIndex.value, 0, moved)
    moodChainStore.reorderSongs(newOrder.map(s => s.song_id))
  }
  draggedIndex.value = null
  dropTargetIndex.value = null
}
</script>

<template>
  <div class="chain-editor">
    <!-- Song list -->
    <div class="song-list">
      <div
        v-for="(song, index) in sortedSongs"
        :key="song.song_id"
        class="song-item"
        :class="{
          current: song.song_id === currentSongId,
          dragging: draggedIndex === index,
          'drop-target': dropTargetIndex === index,
        }"
        :draggable="isEditing"
        @dragstart="handleDragStart(index)"
        @dragover="handleDragOver(index, $event)"
        @dragend="handleDragEnd"
      >
        <!-- Drag handle (editing mode) -->
        <div v-if="isEditing" class="drag-handle">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <circle cx="9" cy="6" r="1.5" />
            <circle cx="15" cy="6" r="1.5" />
            <circle cx="9" cy="12" r="1.5" />
            <circle cx="15" cy="12" r="1.5" />
            <circle cx="9" cy="18" r="1.5" />
            <circle cx="15" cy="18" r="1.5" />
          </svg>
        </div>

        <!-- Position number -->
        <span class="song-position">{{ song.position + 1 }}</span>

        <!-- Cover art -->
        <div class="song-cover">
          <img
            v-if="song.cover_art_path"
            :src="getCoverUrl(song.cover_art_path) || ''"
            :alt="song.title"
          />
          <div v-else class="cover-placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M9 18V5l12-2v13" />
              <circle cx="6" cy="18" r="3" />
              <circle cx="18" cy="16" r="3" />
            </svg>
          </div>
          <!-- Play overlay -->
          <button
            v-if="!isEditing"
            class="play-overlay"
            @click="handlePlaySong(song)"
          >
            <svg viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5,3 19,12 5,21" />
            </svg>
          </button>
        </div>

        <!-- Song info -->
        <div class="song-info">
          <span class="song-title">{{ song.title }}</span>
          <span class="song-artist">{{ song.artist || 'Unknown Artist' }}</span>
        </div>

        <!-- Audio features -->
        <div class="song-features" v-if="song.energy !== null || song.bpm !== null">
          <span v-if="song.energy !== null" class="feature">
            <span class="feature-label">Energy</span>
            <span class="feature-value">{{ Math.round(song.energy * 100) }}%</span>
          </span>
          <span v-if="song.bpm !== null" class="feature">
            <span class="feature-label">BPM</span>
            <span class="feature-value">{{ song.bpm }}</span>
          </span>
        </div>

        <!-- Duration -->
        <span class="song-duration">{{ formatDuration(song.duration_seconds) }}</span>

        <!-- Actions -->
        <div class="song-actions">
          <!-- Show transitions button -->
          <button
            v-if="getTransitionsFrom(song.song_id).length > 0"
            class="action-btn"
            :class="{ active: expandedTransitions === song.song_id }"
            @click="toggleTransitions(song.song_id)"
            title="View transitions"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </button>

          <!-- Remove button (editing mode) -->
          <button
            v-if="isEditing"
            class="action-btn remove"
            @click="handleRemoveSong(song.song_id)"
            title="Remove from chain"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <!-- Transitions panel -->
        <div
          v-if="expandedTransitions === song.song_id"
          class="transitions-panel"
        >
          <h4>Transitions from "{{ song.title }}"</h4>
          <div
            v-for="transition in getTransitionsFrom(song.song_id)"
            :key="`${transition.from_song_id}-${transition.to_song_id}`"
            class="transition-item"
          >
            <div class="transition-target">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
              <span>{{ getSong(transition.to_song_id)?.title || 'Unknown' }}</span>
            </div>
            <TransitionWeightSlider
              :weight="transition.weight"
              :play-count="transition.play_count"
              :disabled="!isEditing"
              @update="(w) => handleWeightUpdate(song.song_id, transition.to_song_id, w)"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Add song button (editing mode) -->
    <div v-if="isEditing" class="add-song-area">
      <Button
        variant="secondary"
        @click="showAddSongSearch = true"
      >
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        Add Song
      </Button>
    </div>
  </div>
</template>

<style scoped>
.chain-editor {
  height: 100%;
  overflow-y: auto;
  padding: 1rem 2rem;
}

.song-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.song-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: var(--color-bg-secondary, #f9fafb);
  border-radius: 8px;
  transition: all 0.15s ease;
}

.song-item:hover {
  background: var(--color-bg-tertiary, #e5e7eb);
}

.song-item.current {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid var(--color-accent-primary, #3b82f6);
}

.song-item.dragging {
  opacity: 0.5;
}

.song-item.drop-target {
  border-top: 2px solid var(--color-accent-primary, #3b82f6);
}

.drag-handle {
  cursor: grab;
  color: var(--color-text-muted, #9ca3af);
  padding: 0.25rem;
}

.drag-handle:active {
  cursor: grabbing;
}

.drag-handle svg {
  width: 16px;
  height: 16px;
}

.song-position {
  width: 24px;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary, #6b7280);
  text-align: center;
}

.song-cover {
  position: relative;
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
}

.song-cover img {
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
  width: 60%;
  height: 60%;
}

.play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  opacity: 0;
  transition: opacity 0.15s ease;
  border: none;
  cursor: pointer;
}

.song-cover:hover .play-overlay {
  opacity: 1;
}

.play-overlay svg {
  width: 20px;
  height: 20px;
}

.song-info {
  flex: 1;
  min-width: 0;
}

.song-title {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary, #1f2937);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.song-artist {
  display: block;
  font-size: 0.8rem;
  color: var(--color-text-secondary, #6b7280);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.song-features {
  display: flex;
  gap: 1rem;
}

.feature {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.feature-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  color: var(--color-text-muted, #9ca3af);
}

.feature-value {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-secondary, #6b7280);
}

.song-duration {
  font-size: 0.8rem;
  color: var(--color-text-secondary, #6b7280);
  min-width: 40px;
  text-align: right;
}

.song-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  color: var(--color-text-muted, #9ca3af);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: var(--color-bg-tertiary, #e5e7eb);
  color: var(--color-text-primary, #1f2937);
}

.action-btn.active {
  color: var(--color-accent-primary, #3b82f6);
}

.action-btn.remove:hover {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-accent-error, #ef4444);
}

.action-btn svg {
  width: 16px;
  height: 16px;
}

/* Transitions panel */
.transitions-panel {
  flex-basis: 100%;
  margin-top: 0.75rem;
  padding: 1rem;
  background: var(--color-bg-primary, #fff);
  border-radius: 6px;
  border: 1px solid var(--color-border, #e5e7eb);
}

.transitions-panel h4 {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-secondary, #6b7280);
  margin: 0 0 0.75rem;
}

.transition-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0;
}

.transition-item + .transition-item {
  border-top: 1px solid var(--color-border, #e5e7eb);
}

.transition-target {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 150px;
  font-size: 0.8rem;
  color: var(--color-text-primary, #1f2937);
}

.transition-target svg {
  width: 16px;
  height: 16px;
  color: var(--color-accent-primary, #3b82f6);
}

/* Add song area */
.add-song-area {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border, #e5e7eb);
  text-align: center;
}

.btn-icon {
  width: 1rem;
  height: 1rem;
  margin-right: 0.5rem;
}

/* Dark mode */
:root.dark .song-item {
  background: var(--color-bg-secondary, #374151);
}

:root.dark .song-item:hover {
  background: var(--color-bg-tertiary, #4b5563);
}

:root.dark .song-title {
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .transitions-panel {
  background: var(--color-bg-tertiary, #4b5563);
  border-color: var(--color-border, #4b5563);
}

:root.dark .transition-target {
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .add-song-area {
  border-color: var(--color-border, #4b5563);
}
</style>
