<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMoodChainStore } from '@/stores/moodChain'
import type { TransitionStyle, MoodChainCreate } from '@/types'
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
const transitionStyle = ref<TransitionStyle>('smooth')
const autoAdvance = ref(true)
const autoAdvanceDelay = ref(10)

// Validation
const isSubmitting = ref(false)
const errors = ref<Record<string, string>>({})

const isValid = computed(() => {
  return name.value.trim().length > 0 && name.value.trim().length <= 255
})

const transitionStyles: { value: TransitionStyle; label: string; description: string; icon: string }[] = [
  {
    value: 'smooth',
    label: 'Smooth',
    description: 'Similar energy and mood transitions',
    icon: '🌊',
  },
  {
    value: 'energy_flow',
    label: 'Energy Flow',
    description: 'Gradually increase or decrease energy',
    icon: '⚡',
  },
  {
    value: 'genre_match',
    label: 'Genre Match',
    description: 'Prefer songs from the same genre',
    icon: '🎵',
  },
  {
    value: 'random',
    label: 'Random',
    description: 'Random transitions with weight consideration',
    icon: '🎲',
  },
]

async function handleSubmit() {
  if (!isValid.value || isSubmitting.value) return

  isSubmitting.value = true
  errors.value = {}

  try {
    const data: MoodChainCreate = {
      name: name.value.trim(),
      description: description.value.trim() || undefined,
      transition_style: transitionStyle.value,
      auto_advance: autoAdvance.value,
      auto_advance_delay_seconds: autoAdvanceDelay.value,
    }

    const chain = await moodChainStore.createChain(data)
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
    title="Create Mood Chain"
    :show="true"
    @close="handleClose"
  >
    <form @submit.prevent="handleSubmit" class="create-chain-form">
      <!-- Name -->
      <div class="form-group">
        <label for="chain-name" class="form-label">Name *</label>
        <Input
          id="chain-name"
          v-model="name"
          placeholder="e.g., Evening Vibes"
          :max-length="255"
          autofocus
        />
        <p v-if="errors.name" class="error-message">{{ errors.name }}</p>
      </div>

      <!-- Description -->
      <div class="form-group">
        <label for="chain-description" class="form-label">Description</label>
        <textarea
          id="chain-description"
          v-model="description"
          class="form-textarea"
          placeholder="A relaxing chain for winding down..."
          rows="3"
          maxlength="5000"
        />
      </div>

      <!-- Transition Style -->
      <div class="form-group">
        <label class="form-label">Transition Style</label>
        <div class="style-options">
          <label
            v-for="style in transitionStyles"
            :key="style.value"
            class="style-option"
            :class="{ selected: transitionStyle === style.value }"
          >
            <input
              type="radio"
              :value="style.value"
              v-model="transitionStyle"
              class="sr-only"
            />
            <span class="style-icon">{{ style.icon }}</span>
            <div class="style-content">
              <span class="style-label">{{ style.label }}</span>
              <span class="style-description">{{ style.description }}</span>
            </div>
          </label>
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
          <span class="toggle-text">
            Auto-advance to next song
          </span>
        </label>

        <div v-if="autoAdvance" class="delay-input">
          <label for="delay" class="delay-label">Wait time:</label>
          <input
            id="delay"
            type="number"
            v-model.number="autoAdvanceDelay"
            min="1"
            max="60"
            class="delay-number"
          />
          <span class="delay-suffix">seconds</span>
        </div>
      </div>

      <!-- Error message -->
      <p v-if="errors.submit" class="error-message submit-error">
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
          Create Chain
        </Button>
      </div>
    </form>
  </Modal>
</template>

<style scoped>
.create-chain-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
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

.style-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.style-option {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.875rem;
  border: 2px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.style-option:hover {
  border-color: var(--color-accent-primary, #3b82f6);
  background: var(--color-bg-secondary, #f9fafb);
}

.style-option.selected {
  border-color: var(--color-accent-primary, #3b82f6);
  background: rgba(59, 130, 246, 0.05);
}

.style-icon {
  font-size: 1.5rem;
  line-height: 1;
}

.style-content {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.style-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary, #1f2937);
}

.style-description {
  font-size: 0.75rem;
  color: var(--color-text-secondary, #6b7280);
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

.delay-input {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding-left: 56px;
}

.delay-label {
  font-size: 0.8rem;
  color: var(--color-text-secondary, #6b7280);
}

.delay-number {
  width: 60px;
  padding: 0.375rem 0.5rem;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 6px;
  font-size: 0.875rem;
  text-align: center;
  background: var(--color-bg-primary, #fff);
  color: var(--color-text-primary, #1f2937);
}

.delay-number:focus {
  outline: none;
  border-color: var(--color-accent-primary, #3b82f6);
}

.delay-suffix {
  font-size: 0.8rem;
  color: var(--color-text-secondary, #6b7280);
}

.error-message {
  font-size: 0.8rem;
  color: var(--color-accent-error, #ef4444);
}

.submit-error {
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

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

/* Dark mode */
:root.dark .form-label,
:root.dark .toggle-text,
:root.dark .style-label {
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .form-textarea,
:root.dark .delay-number {
  background: var(--color-bg-secondary, #374151);
  border-color: var(--color-border, #4b5563);
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .style-option {
  border-color: var(--color-border, #4b5563);
}

:root.dark .style-option:hover {
  background: var(--color-bg-tertiary, #4b5563);
}

:root.dark .style-option.selected {
  background: rgba(59, 130, 246, 0.15);
}

:root.dark .toggle-switch {
  background: var(--color-bg-tertiary, #4b5563);
}

:root.dark .form-actions {
  border-color: var(--color-border, #4b5563);
}
</style>
