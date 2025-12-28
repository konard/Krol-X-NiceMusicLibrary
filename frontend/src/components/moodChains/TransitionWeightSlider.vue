<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  weight: number
  playCount?: number
  disabled?: boolean
}>()

const emit = defineEmits<{
  update: [weight: number]
}>()

const displayWeight = computed(() => Math.round(props.weight * 100))

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  const newWeight = parseInt(target.value, 10) / 100
  emit('update', Math.max(0, Math.min(1, newWeight)))
}
</script>

<template>
  <div class="transition-weight-slider">
    <div class="slider-container">
      <input
        type="range"
        min="0"
        max="100"
        :value="displayWeight"
        :disabled="disabled"
        class="weight-slider"
        @input="handleInput"
      />
      <span class="weight-value">{{ displayWeight }}%</span>
    </div>
    <span v-if="playCount !== undefined && playCount > 0" class="play-count">
      {{ playCount }} {{ playCount === 1 ? 'play' : 'plays' }}
    </span>
  </div>
</template>

<style scoped>
.transition-weight-slider {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.weight-slider {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--color-bg-tertiary, #e5e7eb);
  border-radius: 3px;
  outline: none;
}

.weight-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  background: var(--color-accent-primary, #3b82f6);
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.15s ease;
}

.weight-slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

.weight-slider:disabled {
  opacity: 0.6;
}

.weight-slider:disabled::-webkit-slider-thumb {
  cursor: not-allowed;
}

.weight-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  background: var(--color-accent-primary, #3b82f6);
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.weight-value {
  min-width: 36px;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-accent-primary, #3b82f6);
  text-align: right;
}

.play-count {
  font-size: 0.7rem;
  color: var(--color-text-muted, #9ca3af);
  white-space: nowrap;
}

/* Dark mode */
:root.dark .weight-slider {
  background: var(--color-bg-tertiary, #4b5563);
}
</style>
