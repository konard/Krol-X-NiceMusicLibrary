<script setup lang="ts">
import { computed, ref } from 'vue'

export interface InputProps {
  modelValue?: string
  type?: 'text' | 'email' | 'password' | 'number' | 'search' | 'tel' | 'url'
  placeholder?: string
  disabled?: boolean
  readonly?: boolean
  error?: string
  label?: string
  id?: string
}

const props = withDefaults(defineProps<InputProps>(), {
  modelValue: '',
  type: 'text',
  placeholder: '',
  disabled: false,
  readonly: false,
  error: '',
  label: '',
  id: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
}>()

const inputId = computed(() => props.id || `input-${Math.random().toString(36).substr(2, 9)}`)
const isFocused = ref(false)

const inputClasses = computed(() => [
  'w-full rounded-lg border px-4 py-2',
  'text-text-primary placeholder:text-text-muted',
  'transition-colors duration-fast',
  'focus:outline-none',
  props.error
    ? 'border-accent-error focus:border-accent-error focus:ring-1 focus:ring-accent-error'
    : 'border-bg-tertiary focus:border-accent-primary focus:ring-1 focus:ring-accent-primary',
  props.disabled ? 'bg-bg-secondary cursor-not-allowed opacity-50' : 'bg-bg-primary',
])

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

function handleFocus(event: FocusEvent) {
  isFocused.value = true
  emit('focus', event)
}

function handleBlur(event: FocusEvent) {
  isFocused.value = false
  emit('blur', event)
}
</script>

<template>
  <div class="w-full">
    <label
      v-if="label"
      :for="inputId"
      class="mb-1.5 block text-small font-medium text-text-primary"
    >
      {{ label }}
    </label>
    <div class="relative">
      <slot name="prefix" />
      <input
        :id="inputId"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :class="inputClasses"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
      />
      <slot name="suffix" />
    </div>
    <p
      v-if="error"
      class="mt-1.5 text-caption text-accent-error"
    >
      {{ error }}
    </p>
  </div>
</template>
