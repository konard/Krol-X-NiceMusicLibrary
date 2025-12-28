<script setup lang="ts">
import { Modal, Button } from '@/components/ui'

export interface ConfirmDialogProps {
  modelValue: boolean
  title?: string
  message?: string
  confirmText?: string
  cancelText?: string
  variant?: 'default' | 'danger'
  isLoading?: boolean
}

const props = withDefaults(defineProps<ConfirmDialogProps>(), {
  title: 'Confirm',
  message: 'Are you sure you want to continue?',
  confirmText: 'Confirm',
  cancelText: 'Cancel',
  variant: 'default',
  isLoading: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: []
  cancel: []
}>()

function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  emit('update:modelValue', false)
  emit('cancel')
}

function handleClose() {
  if (!props.isLoading) {
    handleCancel()
  }
}
</script>

<template>
  <Modal
    :model-value="modelValue"
    :title="title"
    size="sm"
    :closable="!isLoading"
    @update:model-value="handleClose"
    @close="handleClose"
  >
    <div class="text-text-secondary">
      <slot>
        {{ message }}
      </slot>
    </div>

    <template #footer>
      <Button
        variant="ghost"
        :disabled="isLoading"
        @click="handleCancel"
      >
        {{ cancelText }}
      </Button>
      <Button
        :variant="variant === 'danger' ? 'danger' : 'primary'"
        :disabled="isLoading"
        @click="handleConfirm"
      >
        <svg
          v-if="isLoading"
          class="mr-2 h-4 w-4 animate-spin"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        {{ confirmText }}
      </Button>
    </template>
  </Modal>
</template>
