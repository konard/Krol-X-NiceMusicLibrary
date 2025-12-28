<script setup lang="ts">
import { computed } from 'vue'
import type { Toast } from '@/types'

export interface ToastProps {
  toast: Toast
}

const props = defineProps<ToastProps>()

const emit = defineEmits<{
  close: [id: string]
}>()

const iconMap = {
  success: `<path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />`,
  error: `<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />`,
  warning: `<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />`,
  info: `<path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />`,
}

const colorClasses = computed(() => {
  const colors = {
    success: 'bg-accent-success/10 border-accent-success text-accent-success',
    error: 'bg-accent-error/10 border-accent-error text-accent-error',
    warning: 'bg-accent-warning/10 border-accent-warning text-accent-warning',
    info: 'bg-accent-primary/10 border-accent-primary text-accent-primary',
  }
  return colors[props.toast.type]
})

function close() {
  emit('close', props.toast.id)
}
</script>

<template>
  <div
    :class="[
      'flex items-start gap-3 rounded-lg border p-4 shadow-lg',
      'animate-slide-up',
      colorClasses,
    ]"
    role="alert"
  >
    <svg
      class="h-5 w-5 flex-shrink-0"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      stroke-width="1.5"
      v-html="iconMap[toast.type]"
    />
    <p class="flex-1 text-small text-text-primary">
      {{ toast.message }}
    </p>
    <button
      type="button"
      class="flex-shrink-0 rounded p-0.5 hover:bg-bg-secondary transition-colors"
      aria-label="Dismiss"
      @click="close"
    >
      <svg
        class="h-4 w-4"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>
    </button>
  </div>
</template>
