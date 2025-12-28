<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMoodChainStore } from '@/stores/moodChain'
import Button from '@/components/ui/Button.vue'
import Loader from '@/components/ui/Loader.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import ChainVisualization from '@/components/moodChains/ChainVisualization.vue'
import ChainEditor from '@/components/moodChains/ChainEditor.vue'
import ChainSettingsPanel from '@/components/moodChains/ChainSettingsPanel.vue'
import NextSuggestions from '@/components/moodChains/NextSuggestions.vue'
import { getCoverUrl } from '@/services/moodChains'

const route = useRoute()
const router = useRouter()
const moodChainStore = useMoodChainStore()

const chainId = computed(() => route.params.id as string)
const chain = computed(() => moodChainStore.currentChain)
const isLoading = computed(() => moodChainStore.isLoadingChain)
const isEditing = computed(() => moodChainStore.isEditing)
const isPlayingChain = computed(() => moodChainStore.isPlayingChain)
const currentSong = computed(() => moodChainStore.currentSongInChain)
const suggestions = computed(() => moodChainStore.suggestions)

const showSettings = ref(false)
const showDeleteConfirm = ref(false)
const viewMode = ref<'visualization' | 'list'>('visualization')

const transitionStyleLabels: Record<string, string> = {
  smooth: 'Smooth Transitions',
  random: 'Random',
  energy_flow: 'Energy Flow',
  genre_match: 'Genre Match',
}

const coverUrl = computed(() => getCoverUrl(chain.value?.cover_image_path || null))

const totalDuration = computed(() => {
  if (!chain.value?.songs) return '0:00'
  const totalSeconds = chain.value.songs.reduce((sum, s) => sum + s.duration_seconds, 0)
  const hours = Math.floor(totalSeconds / 3600)
  const mins = Math.floor((totalSeconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${mins}m`
  }
  return `${mins} min`
})

onMounted(async () => {
  await moodChainStore.fetchChain(chainId.value)
})

onUnmounted(() => {
  moodChainStore.stopChainPlayback()
  moodChainStore.clearCurrentChain()
})

// Watch for route changes
watch(chainId, async (newId) => {
  if (newId) {
    moodChainStore.stopChainPlayback()
    await moodChainStore.fetchChain(newId)
  }
})

async function handlePlay() {
  if (!chain.value) return
  await moodChainStore.startChainPlayback()
}

function toggleEdit() {
  moodChainStore.setEditing(!isEditing.value)
}

function handleSettingsClick() {
  showSettings.value = true
}

async function handleDelete() {
  if (!chain.value) return
  const success = await moodChainStore.deleteChain(chain.value.id)
  if (success) {
    router.push({ name: 'mood-chains' })
  }
  showDeleteConfirm.value = false
}

function handleBack() {
  router.push({ name: 'mood-chains' })
}
</script>

<template>
  <div class="mood-chain-page">
    <!-- Loading state -->
    <div v-if="isLoading" class="loading-state">
      <Loader size="lg" />
      <p>Loading mood chain...</p>
    </div>

    <!-- Not found state -->
    <div v-else-if="!chain" class="not-found-state">
      <h2>Mood chain not found</h2>
      <p>The mood chain you're looking for doesn't exist or has been deleted.</p>
      <Button variant="primary" @click="handleBack">
        Back to Mood Chains
      </Button>
    </div>

    <!-- Chain content -->
    <template v-else>
      <!-- Header -->
      <header class="chain-header">
        <button class="back-button" @click="handleBack">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5" />
            <path d="M12 19l-7-7 7-7" />
          </svg>
        </button>

        <div class="header-content">
          <!-- Cover art -->
          <div class="chain-cover">
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
          </div>

          <!-- Chain info -->
          <div class="chain-info">
            <span class="chain-type">Mood Chain</span>
            <h1 class="chain-name">{{ chain.name }}</h1>
            <p v-if="chain.description" class="chain-description">
              {{ chain.description }}
            </p>
            <div class="chain-meta">
              <span class="meta-item">{{ chain.song_count }} songs</span>
              <span class="meta-separator">•</span>
              <span class="meta-item">{{ totalDuration }}</span>
              <span class="meta-separator">•</span>
              <span class="meta-item">{{ transitionStyleLabels[chain.transition_style] }}</span>
              <template v-if="chain.play_count > 0">
                <span class="meta-separator">•</span>
                <span class="meta-item">{{ chain.play_count }} plays</span>
              </template>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="header-actions">
          <Button
            v-if="chain.songs.length > 0"
            variant="primary"
            size="lg"
            :disabled="isPlayingChain"
            @click="handlePlay"
          >
            <svg class="btn-icon" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5,3 19,12 5,21" />
            </svg>
            {{ isPlayingChain ? 'Playing' : 'Play Chain' }}
          </Button>
          <Button
            variant="secondary"
            :class="{ 'is-active': isEditing }"
            @click="toggleEdit"
          >
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            {{ isEditing ? 'Done' : 'Edit' }}
          </Button>
          <Button
            variant="ghost"
            @click="handleSettingsClick"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
          </Button>
        </div>
      </header>

      <!-- View mode toggle -->
      <div class="view-controls">
        <div class="view-toggle">
          <button
            :class="{ active: viewMode === 'visualization' }"
            @click="viewMode = 'visualization'"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3" />
              <line x1="12" y1="3" x2="12" y2="9" />
              <line x1="12" y1="15" x2="12" y2="21" />
              <line x1="3" y1="12" x2="9" y2="12" />
              <line x1="15" y1="12" x2="21" y2="12" />
            </svg>
            Graph
          </button>
          <button
            :class="{ active: viewMode === 'list' }"
            @click="viewMode = 'list'"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="8" y1="6" x2="21" y2="6" />
              <line x1="8" y1="12" x2="21" y2="12" />
              <line x1="8" y1="18" x2="21" y2="18" />
              <line x1="3" y1="6" x2="3.01" y2="6" />
              <line x1="3" y1="12" x2="3.01" y2="12" />
              <line x1="3" y1="18" x2="3.01" y2="18" />
            </svg>
            List
          </button>
        </div>
      </div>

      <!-- Main content area -->
      <div class="chain-content">
        <!-- Empty state -->
        <div v-if="chain.songs.length === 0" class="empty-chain">
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M9 18V5l12-2v13" />
              <circle cx="6" cy="18" r="3" />
              <circle cx="18" cy="16" r="3" />
            </svg>
          </div>
          <h3>No songs yet</h3>
          <p>Add songs to start building your mood chain</p>
          <Button variant="primary" @click="toggleEdit">
            Add Songs
          </Button>
        </div>

        <!-- Visualization view -->
        <ChainVisualization
          v-else-if="viewMode === 'visualization'"
          :chain="chain"
          :current-song-id="currentSong?.song_id"
          :is-editing="isEditing"
          @node-click="(id) => moodChainStore.startChainPlayback(id)"
        />

        <!-- List/Editor view -->
        <ChainEditor
          v-else
          :chain="chain"
          :is-editing="isEditing"
          :current-song-id="currentSong?.song_id"
        />
      </div>

      <!-- Next song suggestions (during playback) -->
      <NextSuggestions
        v-if="isPlayingChain && suggestions.length > 0"
        :suggestions="suggestions"
        :countdown="moodChainStore.autoAdvanceCountdown"
        :auto-advance="chain.auto_advance"
        @select="moodChainStore.selectNextSong"
      />

      <!-- Settings panel -->
      <ChainSettingsPanel
        v-if="showSettings"
        :chain="chain"
        @close="showSettings = false"
        @delete="showDeleteConfirm = true"
      />

      <!-- Delete confirmation -->
      <ConfirmDialog
        v-model="showDeleteConfirm"
        title="Delete Mood Chain"
        message="Are you sure you want to delete this mood chain? This action cannot be undone."
        confirm-text="Delete"
        cancel-text="Cancel"
        variant="danger"
        @confirm="handleDelete"
        @cancel="showDeleteConfirm = false"
      />
    </template>
  </div>
</template>

<style scoped>
.mood-chain-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.loading-state,
.not-found-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem;
}

.loading-state p,
.not-found-state p {
  color: var(--color-text-secondary, #6b7280);
  margin: 1rem 0;
}

.not-found-state h2 {
  color: var(--color-text-primary, #1f2937);
  margin: 0;
}

/* Header */
.chain-header {
  padding: 1.5rem 2rem;
  background: var(--color-bg-secondary, #f9fafb);
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}

.back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: none;
  color: var(--color-text-secondary, #6b7280);
  cursor: pointer;
  border-radius: 8px;
  margin-bottom: 1rem;
  transition: all 0.15s ease;
}

.back-button:hover {
  background: var(--color-bg-tertiary, #e5e7eb);
  color: var(--color-text-primary, #1f2937);
}

.back-button svg {
  width: 20px;
  height: 20px;
}

.header-content {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.25rem;
}

.chain-cover {
  width: 180px;
  height: 180px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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

.chain-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.chain-type {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted, #9ca3af);
}

.chain-name {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-primary, #1f2937);
  margin: 0.25rem 0 0.5rem;
}

.chain-description {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #6b7280);
  margin: 0 0 0.75rem;
  max-width: 600px;
}

.chain-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary, #6b7280);
}

.meta-separator {
  color: var(--color-text-muted, #9ca3af);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.btn-icon {
  width: 1rem;
  height: 1rem;
  margin-right: 0.5rem;
}

.is-active {
  background: var(--color-accent-primary, #3b82f6) !important;
  color: white !important;
  border-color: var(--color-accent-primary, #3b82f6) !important;
}

/* View controls */
.view-controls {
  padding: 0.75rem 2rem;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
  background: var(--color-bg-primary, #fff);
}

.view-toggle {
  display: inline-flex;
  background: var(--color-bg-secondary, #f9fafb);
  border-radius: 8px;
  padding: 4px;
}

.view-toggle button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: none;
  background: none;
  font-size: 0.875rem;
  color: var(--color-text-secondary, #6b7280);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.view-toggle button:hover {
  color: var(--color-text-primary, #1f2937);
}

.view-toggle button.active {
  background: white;
  color: var(--color-text-primary, #1f2937);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.view-toggle button svg {
  width: 16px;
  height: 16px;
}

/* Content */
.chain-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.empty-chain {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem;
}

.empty-icon {
  width: 80px;
  height: 80px;
  color: var(--color-text-muted, #9ca3af);
  margin-bottom: 1rem;
}

.empty-icon svg {
  width: 100%;
  height: 100%;
}

.empty-chain h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-primary, #1f2937);
  margin: 0 0 0.5rem;
}

.empty-chain p {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #6b7280);
  margin: 0 0 1.5rem;
}

/* Dark mode */
:root.dark .chain-header {
  background: var(--color-bg-secondary, #374151);
  border-color: var(--color-border, #4b5563);
}

:root.dark .back-button:hover {
  background: var(--color-bg-tertiary, #4b5563);
}

:root.dark .chain-name {
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .view-controls {
  background: var(--color-bg-primary, #1f2937);
  border-color: var(--color-border, #4b5563);
}

:root.dark .view-toggle {
  background: var(--color-bg-secondary, #374151);
}

:root.dark .view-toggle button.active {
  background: var(--color-bg-tertiary, #4b5563);
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .empty-chain h3 {
  color: var(--color-text-primary, #f9fafb);
}
</style>
