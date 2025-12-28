<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()
const { isSidebarExpanded, isMobile } = storeToRefs(uiStore)
</script>

<template>
  <main
    :class="[
      'min-h-screen pt-16 pb-player-height transition-all duration-normal',
      isMobile ? 'pl-0' : isSidebarExpanded ? 'pl-sidebar-expanded' : 'pl-sidebar-collapsed',
    ]"
  >
    <div class="p-4 md:p-6">
      <slot />
    </div>
  </main>
</template>
