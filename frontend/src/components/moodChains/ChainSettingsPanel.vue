<script setup lang="ts">
import { ref, watch } from 'vue'
import type { MoodChainDetail, TransitionStyle, MoodChainUpdate } from '@/types'
import { useMoodChainStore } from '@/stores/moodChain'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'

const props = defineProps<{
  chain: MoodChainDetail
}>()

const emit = defineEmits<{
  close: []
  delete: []
}>()

const moodChainStore = useMoodChainStore()

// Form state - initialized from props
const name = ref(props.chain.name)
const description = ref(props.chain.description || '')
const transitionStyle = ref<TransitionStyle>(props.chain.transition_style)
const autoAdvance = ref(props.chain.auto_advance)
const autoAdvanceDelay = ref(props.chain.auto_advance_delay_seconds)

const isSaving = ref(false)
const hasChanges = ref(false)

// Track changes
watch([name, description, transitionStyle, autoAdvance, autoAdvanceDelay], () => {
  hasChanges.value =
    name.value !== props.chain.name ||
    (description.value || '') !== (props.chain.description || '') ||
    transitionStyle.value !== props.chain.transition_style ||
    autoAdvance.value !== props.chain.auto_advance ||
    autoAdvanceDelay.value !== props.chain.auto_advance_delay_seconds
})

const transitionStyles: { value: TransitionStyle; label: string; icon: string }[] = [
  { value: 'smooth', label: 'Smooth', icon: '🌊' },
  { value: 'energy_flow', label: 'Energy Flow', icon: '⚡' },
  { value: 'genre_match', label: 'Genre Match', icon: '🎵' },
  { value: 'random', label: 'Random', icon: '🎲' },
]

async function handleSave() {
  if (!hasChanges.value || isSaving.value) return

  isSaving.value = true

  try {
    const data: MoodChainUpdate = {
      name: name.value.trim(),
      description: description.value.trim() || null,
      transition_style: transitionStyle.value,
      auto_advance: autoAdvance.value,
      auto_advance_delay_seconds: autoAdvanceDelay.value,
    }

    await moodChainStore.updateChain(props.chain.id, data)
    emit('close')
  } catch (err) {
    console.error('Failed to save settings:', err)
  } finally {
    isSaving.value = false
  }
}

function handleDelete() {
  emit('delete')
}

function handleClose() {
  emit('close')
}
</script>

<template>
  <div class="settings-overlay" @click.self="handleClose">
    <div class="settings-panel">
      <header class="panel-header">
        <h2>Chain Settings</h2>
        <button class="close-btn" @click="handleClose">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </header>

      <div class="panel-content">
        <!-- Name -->
        <div class="form-group">
          <label for="chain-name" class="form-label">Name</label>
          <Input
            id="chain-name"
            v-model="name"
            placeholder="Chain name"
            :max-length="255"
          />
        </div>

        <!-- Description -->
        <div class="form-group">
          <label for="chain-desc" class="form-label">Description</label>
          <textarea
            id="chain-desc"
            v-model="description"
            class="form-textarea"
            placeholder="Optional description..."
            rows="3"
            maxlength="5000"
          />
        </div>

        <!-- Transition Style -->
        <div class="form-group">
          <label class="form-label">Transition Style</label>
          <div class="style-grid">
            <button
              v-for="style in transitionStyles"
              :key="style.value"
              type="button"
              class="style-btn"
              :class="{ selected: transitionStyle === style.value }"
              @click="transitionStyle = style.value"
            >
              <span class="style-icon">{{ style.icon }}</span>
              <span class="style-label">{{ style.label }}</span>
            </button>
          </div>
        </div>

        <!-- Auto-advance -->
        <div class="form-group">
          <label class="toggle-label">
            <input
              type="checkbox"
              v-model="autoAdvance"
              class="toggle-input"
            />
            <span class="toggle-switch" />
            <span class="toggle-text">Auto-advance to next song</span>
          </label>

          <div v-if="autoAdvance" class="delay-control">
            <label>Wait time:</label>
            <input
              type="number"
              v-model.number="autoAdvanceDelay"
              min="1"
              max="60"
              class="delay-input"
            />
            <span>seconds</span>
          </div>
        </div>

        <!-- Chain info -->
        <div class="chain-info">
          <h3>Chain Information</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">Songs</span>
              <span class="info-value">{{ chain.song_count }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Play count</span>
              <span class="info-value">{{ chain.play_count }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Created</span>
              <span class="info-value">
                {{ new Date(chain.created_at).toLocaleDateString() }}
              </span>
            </div>
            <div v-if="chain.is_auto_generated" class="info-item">
              <span class="info-label">Type</span>
              <span class="info-value auto-badge">Auto-generated</span>
            </div>
          </div>
        </div>

        <!-- Danger zone -->
        <div class="danger-zone">
          <h3>Danger Zone</h3>
          <p>Once deleted, this mood chain cannot be recovered.</p>
          <Button
            variant="danger"
            size="sm"
            @click="handleDelete"
          >
            Delete Mood Chain
          </Button>
        </div>
      </div>

      <footer class="panel-footer">
        <Button variant="secondary" @click="handleClose">
          Cancel
        </Button>
        <Button
          variant="primary"
          :disabled="!hasChanges"
          :loading="isSaving"
          @click="handleSave"
        >
          Save Changes
        </Button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.settings-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  z-index: 100;
}

.settings-panel {
  width: 400px;
  max-width: 100%;
  height: 100%;
  background: var(--color-bg-primary, #fff);
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.15);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}

.panel-header h2 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-primary, #1f2937);
  margin: 0;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  color: var(--color-text-secondary, #6b7280);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-btn:hover {
  background: var(--color-bg-secondary, #f9fafb);
  color: var(--color-text-primary, #1f2937);
}

.close-btn svg {
  width: 18px;
  height: 18px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary, #1f2937);
  margin-bottom: 0.5rem;
}

.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  font-size: 0.875rem;
  font-family: inherit;
  resize: vertical;
  background: var(--color-bg-primary, #fff);
  color: var(--color-text-primary, #1f2937);
}

.form-textarea:focus {
  outline: none;
  border-color: var(--color-accent-primary, #3b82f6);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.style-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.style-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 2px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  background: none;
  cursor: pointer;
  transition: all 0.15s ease;
}

.style-btn:hover {
  border-color: var(--color-accent-primary, #3b82f6);
}

.style-btn.selected {
  border-color: var(--color-accent-primary, #3b82f6);
  background: rgba(59, 130, 246, 0.05);
}

.style-icon {
  font-size: 1.25rem;
}

.style-label {
  font-size: 0.875rem;
  color: var(--color-text-primary, #1f2937);
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
}

.toggle-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-switch {
  position: relative;
  width: 44px;
  height: 24px;
  background: var(--color-bg-tertiary, #e5e7eb);
  border-radius: 12px;
  transition: background 0.2s ease;
  flex-shrink: 0;
}

.toggle-switch::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.toggle-input:checked + .toggle-switch {
  background: var(--color-accent-primary, #3b82f6);
}

.toggle-input:checked + .toggle-switch::after {
  transform: translateX(20px);
}

.toggle-text {
  font-size: 0.875rem;
  color: var(--color-text-primary, #1f2937);
}

.delay-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding-left: 56px;
  font-size: 0.8rem;
  color: var(--color-text-secondary, #6b7280);
}

.delay-input {
  width: 60px;
  padding: 0.375rem 0.5rem;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 6px;
  font-size: 0.875rem;
  text-align: center;
  background: var(--color-bg-primary, #fff);
  color: var(--color-text-primary, #1f2937);
}

.delay-input:focus {
  outline: none;
  border-color: var(--color-accent-primary, #3b82f6);
}

.chain-info {
  margin-top: 1.5rem;
  padding: 1rem;
  background: var(--color-bg-secondary, #f9fafb);
  border-radius: 8px;
}

.chain-info h3 {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted, #9ca3af);
  margin: 0 0 0.75rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.info-label {
  font-size: 0.75rem;
  color: var(--color-text-muted, #9ca3af);
}

.info-value {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary, #1f2937);
}

.auto-badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  background: var(--color-accent-primary, #3b82f6);
  color: white;
  font-size: 0.7rem;
  border-radius: 4px;
}

.danger-zone {
  margin-top: 1.5rem;
  padding: 1rem;
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
}

.danger-zone h3 {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-accent-error, #ef4444);
  margin: 0 0 0.5rem;
}

.danger-zone p {
  font-size: 0.8rem;
  color: var(--color-text-secondary, #6b7280);
  margin: 0 0 1rem;
}

.panel-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border, #e5e7eb);
}

/* Dark mode */
:root.dark .settings-panel {
  background: var(--color-bg-primary, #1f2937);
}

:root.dark .panel-header {
  border-color: var(--color-border, #4b5563);
}

:root.dark .panel-header h2 {
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .form-label,
:root.dark .toggle-text,
:root.dark .style-label {
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .form-textarea,
:root.dark .delay-input {
  background: var(--color-bg-secondary, #374151);
  border-color: var(--color-border, #4b5563);
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .style-btn {
  border-color: var(--color-border, #4b5563);
}

:root.dark .toggle-switch {
  background: var(--color-bg-tertiary, #4b5563);
}

:root.dark .chain-info {
  background: var(--color-bg-secondary, #374151);
}

:root.dark .info-value {
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .panel-footer {
  border-color: var(--color-border, #4b5563);
}
</style>
