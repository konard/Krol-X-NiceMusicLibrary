<script setup lang="ts">
import { ref, onMounted } from 'vue'

const healthStatus = ref<string>('checking...')

onMounted(async () => {
  try {
    const response = await fetch('/api/v1/health')
    const data = await response.json()
    healthStatus.value = data.status
  } catch (error) {
    healthStatus.value = 'error'
  }
})
</script>

<template>
  <div class="flex min-h-screen items-center justify-center">
    <div class="text-center">
      <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
        NiceMusicLibrary
      </h1>
      <p class="text-gray-600 dark:text-gray-400 mb-4">
        Personal music library with mood chains
      </p>
      <div class="inline-flex items-center gap-2 rounded-full bg-gray-200 dark:bg-gray-800 px-4 py-2">
        <span class="text-sm text-gray-600 dark:text-gray-400">API Status:</span>
        <span
          :class="[
            'text-sm font-medium',
            healthStatus === 'healthy' ? 'text-green-600' : 'text-red-600'
          ]"
        >
          {{ healthStatus }}
        </span>
      </div>
    </div>
  </div>
</template>
