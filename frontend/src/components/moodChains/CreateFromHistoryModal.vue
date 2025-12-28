<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMoodChainStore } from '@/stores/moodChain'
import type { MoodChainFromHistoryRequest } from '@/types'
import Modal from '@/components/ui/Modal.vue'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'

const emit = defineEmits<{
  close: []
  created: [chainId: string]
}>()

const moodChainStore = useMoodChainStore()

// Form state
const name = ref('')
const description = ref('')
const fromDate = ref('')
const toDate = ref('')
const minPlays = ref(2)

// Time period presets
const selectedPreset = ref<string>('week')

const presets = [
  { value: 'week', label: 'Last Week' },
  { value: 'month', label: 'Last Month' },
  { value: '3months', label: 'Last 3 Months' },
  { value: 'year', label: 'Last Year' },
  { value: 'custom', label: 'Custom Range' },
]

// Validation
const isSubmitting = ref(false)
const errors = ref<Record<string, string>>({})

const isValid = computed(() => {
  return name.value.trim().length > 0 && name.value.trim().length <= 255
})

function getDateRange(): { from: string | undefined; to: string | undefined } {
  if (selectedPreset.value === 'custom') {
    return {
      from: fromDate.value || undefined,
      to: toDate.value || undefined,
    }
  }

  const now = new Date()
  const to = now.toISOString()
  let from: Date

  switch (selectedPreset.value) {
    case 'week':
      from = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      break
    case 'month':
      from = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      break
    case '3months':
      from = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000)
      break
    case 'year':
      from = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000)
      break
    default:
      from = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
  }

  return {
    from: from.toISOString(),
    to,
  }
}

async function handleSubmit() {
  if (!isValid.value || isSubmitting.value) return

  isSubmitting.value = true
  errors.value = {}

  try {
    const { from, to } = getDateRange()

    const data: MoodChainFromHistoryRequest = {
      name: name.value.trim(),
      description: description.value.trim() || undefined,
      from_date: from,
      to_date: to,
      min_plays: minPlays.value,
    }

    const chain = await moodChainStore.createFromHistory(data)
    if (chain) {
      emit('created', chain.id)
    }
  } catch (err) {
    errors.value.submit = err instanceof Error ? err.message : 'Failed to create chain'
  } finally {
    isSubmitting.value = false
  }
}

function handleClose() {
  emit('close')
}
</script>

<template>
  <Modal
    title="Create from Listening History"
    :show="true"
    @close="handleClose"
  >
    <form @submit.prevent="handleSubmit" class="create-history-form">
      <p class="intro-text">
        Analyze your listening history to automatically create a mood chain
        based on your actual listening patterns and transitions.
      </p>

      <!-- Name -->
      <div class="form-group">
        <label for="chain-name" class="form-label">Name *</label>
        <Input
          id="chain-name"
          v-model="name"
          placeholder="e.g., My February Mix"
          :max-length="255"
          autofocus
        />
      </div>

      <!-- Description -->
      <div class="form-group">
        <label for="chain-description" class="form-label">Description</label>
        <textarea
          id="chain-description"
          v-model="description"
          class="form-textarea"
          placeholder="Generated from my listening history..."
          rows="2"
          maxlength="5000"
        />
      </div>

      <!-- Time Period -->
      <div class="form-group">
        <label class="form-label">Time Period</label>
        <div class="preset-options">
          <button
            v-for="preset in presets"
            :key="preset.value"
            type="button"
            class="preset-button"
            :class="{ selected: selectedPreset === preset.value }"
            @click="selectedPreset = preset.value"
          >
            {{ preset.label }}
          </button>
        </div>

        <!-- Custom date range -->
        <div v-if="selectedPreset === 'custom'" class="custom-range">
          <div class="date-input">
            <label for="from-date">From</label>
            <input
              id="from-date"
              type="date"
              v-model="fromDate"
              class="date-field"
            />
          </div>
          <div class="date-input">
            <label for="to-date">To</label>
            <input
              id="to-date"
              type="date"
              v-model="toDate"
              class="date-field"
            />
          </div>
        </div>
      </div>

      <!-- Minimum plays filter -->
      <div class="form-group">
        <label for="min-plays" class="form-label">Minimum Plays</label>
        <div class="min-plays-input">
          <input
            id="min-plays"
            type="range"
            v-model.number="minPlays"
            min="1"
            max="10"
            class="range-input"
          />
          <span class="range-value">{{ minPlays }}+</span>
        </div>
        <p class="help-text">
          Only include songs you've played at least {{ minPlays }} time{{ minPlays > 1 ? 's' : '' }}
        </p>
      </div>

      <!-- Info box -->
      <div class="info-box">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 16v-4" />
          <path d="M12 8h.01" />
        </svg>
        <p>
          The chain will analyze consecutive plays to determine transition patterns
          and automatically calculate weights based on how often you listened to
          songs in sequence.
        </p>
      </div>

      <!-- Error message -->
      <p v-if="errors.submit" class="error-message">
        {{ errors.submit }}
      </p>

      <!-- Actions -->
      <div class="form-actions">
        <Button
          type="button"
          variant="secondary"
          @click="handleClose"
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="primary"
          :disabled="!isValid"
          :loading="isSubmitting"
        >
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 8v4l3 3" />
            <circle cx="12" cy="12" r="10" />
          </svg>
          Generate Chain
        </Button>
      </div>
    </form>
  </Modal>
</template>

<style scoped>
.create-history-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.intro-text {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #6b7280);
  margin: 0;
  line-height: 1.5;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary, #1f2937);
}

.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  font-size: 0.875rem;
  resize: vertical;
  font-family: inherit;
  background: var(--color-bg-primary, #fff);
  color: var(--color-text-primary, #1f2937);
}

.form-textarea:focus {
  outline: none;
  border-color: var(--color-accent-primary, #3b82f6);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.preset-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.preset-button {
  padding: 0.5rem 1rem;
  background: var(--color-bg-secondary, #f9fafb);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 20px;
  font-size: 0.8rem;
  color: var(--color-text-secondary, #6b7280);
  cursor: pointer;
  transition: all 0.15s ease;
}

.preset-button:hover {
  border-color: var(--color-accent-primary, #3b82f6);
  color: var(--color-accent-primary, #3b82f6);
}

.preset-button.selected {
  background: var(--color-accent-primary, #3b82f6);
  border-color: var(--color-accent-primary, #3b82f6);
  color: white;
}

.custom-range {
  display: flex;
  gap: 1rem;
  margin-top: 0.75rem;
}

.date-input {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.date-input label {
  font-size: 0.75rem;
  color: var(--color-text-secondary, #6b7280);
}

.date-field {
  padding: 0.5rem;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 6px;
  font-size: 0.875rem;
  background: var(--color-bg-primary, #fff);
  color: var(--color-text-primary, #1f2937);
}

.date-field:focus {
  outline: none;
  border-color: var(--color-accent-primary, #3b82f6);
}

.min-plays-input {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.range-input {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--color-bg-tertiary, #e5e7eb);
  border-radius: 3px;
  outline: none;
}

.range-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  background: var(--color-accent-primary, #3b82f6);
  border-radius: 50%;
  cursor: pointer;
}

.range-input::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: var(--color-accent-primary, #3b82f6);
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.range-value {
  min-width: 2.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-accent-primary, #3b82f6);
}

.help-text {
  font-size: 0.75rem;
  color: var(--color-text-muted, #9ca3af);
  margin: 0;
}

.info-box {
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(59, 130, 246, 0.05);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
}

.info-box svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: var(--color-accent-primary, #3b82f6);
}

.info-box p {
  font-size: 0.8rem;
  color: var(--color-text-secondary, #6b7280);
  margin: 0;
  line-height: 1.5;
}

.error-message {
  font-size: 0.8rem;
  color: var(--color-accent-error, #ef4444);
  text-align: center;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border, #e5e7eb);
}

.btn-icon {
  width: 1rem;
  height: 1rem;
  margin-right: 0.5rem;
}

/* Dark mode */
:root.dark .form-label {
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .form-textarea,
:root.dark .date-field {
  background: var(--color-bg-secondary, #374151);
  border-color: var(--color-border, #4b5563);
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .preset-button {
  background: var(--color-bg-tertiary, #4b5563);
  border-color: var(--color-border, #4b5563);
}

:root.dark .range-input {
  background: var(--color-bg-tertiary, #4b5563);
}

:root.dark .form-actions {
  border-color: var(--color-border, #4b5563);
}
</style>
