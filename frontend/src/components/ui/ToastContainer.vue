<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useUiStore } from '@/stores/ui'
import Toast from './Toast.vue'

const uiStore = useUiStore()
const { toasts } = storeToRefs(uiStore)

function handleClose(id: string) {
  uiStore.removeToast(id)
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed bottom-4 right-4 z-[100] flex flex-col gap-2"
      aria-live="polite"
    >
      <TransitionGroup
        enter-active-class="transition-all duration-normal"
        enter-from-class="opacity-0 translate-x-4"
        enter-to-class="opacity-100 translate-x-0"
        leave-active-class="transition-all duration-normal"
        leave-from-class="opacity-100 translate-x-0"
        leave-to-class="opacity-0 translate-x-4"
      >
        <Toast
          v-for="toast in toasts"
          :key="toast.id"
          :toast="toast"
          @close="handleClose"
        />
      </TransitionGroup>
    </div>
  </Teleport>
</template>
