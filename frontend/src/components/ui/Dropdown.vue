<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

export interface DropdownOption {
  value: string | number
  label: string
  disabled?: boolean
}

export interface DropdownProps {
  modelValue?: string | number | null
  options: DropdownOption[]
  placeholder?: string
  disabled?: boolean
  label?: string
  error?: string
}

const props = withDefaults(defineProps<DropdownProps>(), {
  modelValue: null,
  placeholder: 'Select an option',
  disabled: false,
  label: '',
  error: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
}>()

const isOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const selectedOption = computed(() =>
  props.options.find((opt) => opt.value === props.modelValue)
)

const displayValue = computed(() =>
  selectedOption.value?.label || props.placeholder
)

function toggle() {
  if (!props.disabled) {
    isOpen.value = !isOpen.value
  }
}

function selectOption(option: DropdownOption) {
  if (!option.disabled) {
    emit('update:modelValue', option.value)
    isOpen.value = false
  }
}

function handleClickOutside(event: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isOpen.value = false
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div
    ref="dropdownRef"
    class="relative w-full"
  >
    <label
      v-if="label"
      class="mb-1.5 block text-small font-medium text-text-primary"
    >
      {{ label }}
    </label>

    <!-- Trigger -->
    <button
      type="button"
      :disabled="disabled"
      :class="[
        'flex w-full items-center justify-between rounded-lg border px-4 py-2',
        'text-left transition-colors duration-fast',
        error
          ? 'border-accent-error'
          : isOpen
            ? 'border-accent-primary ring-1 ring-accent-primary'
            : 'border-bg-tertiary hover:border-accent-primary',
        disabled ? 'cursor-not-allowed opacity-50 bg-bg-secondary' : 'bg-bg-primary',
      ]"
      @click="toggle"
    >
      <span
        :class="[
          selectedOption ? 'text-text-primary' : 'text-text-muted',
        ]"
      >
        {{ displayValue }}
      </span>
      <svg
        :class="[
          'h-5 w-5 text-text-secondary transition-transform duration-fast',
          isOpen ? 'rotate-180' : '',
        ]"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M19 9l-7 7-7-7"
        />
      </svg>
    </button>

    <!-- Options -->
    <Transition
      enter-active-class="transition-all duration-fast"
      enter-from-class="opacity-0 -translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition-all duration-fast"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-1"
    >
      <ul
        v-if="isOpen"
        class="absolute z-50 mt-1 w-full rounded-lg border border-bg-tertiary bg-bg-primary py-1 shadow-lg"
      >
        <li
          v-for="option in options"
          :key="option.value"
          :class="[
            'cursor-pointer px-4 py-2 transition-colors duration-fast',
            option.disabled
              ? 'cursor-not-allowed opacity-50'
              : 'hover:bg-bg-secondary',
            option.value === modelValue ? 'bg-accent-primary/10 text-accent-primary' : 'text-text-primary',
          ]"
          @click="selectOption(option)"
        >
          {{ option.label }}
        </li>
      </ul>
    </Transition>

    <p
      v-if="error"
      class="mt-1.5 text-caption text-accent-error"
    >
      {{ error }}
    </p>
  </div>
</template>
