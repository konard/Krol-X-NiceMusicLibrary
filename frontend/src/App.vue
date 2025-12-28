<script setup lang="ts">
import { RouterView } from 'vue-router'
import { AppLayout } from '@/components/layout'
import { useKeyboard } from '@/composables'

// Initialize global keyboard shortcuts
useKeyboard()
</script>

<template>
  <AppLayout>
    <RouterView />
  </AppLayout>
</template>
