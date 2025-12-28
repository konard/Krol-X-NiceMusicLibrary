<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
import MainContent from './MainContent.vue'
import { ToastContainer } from '@/components/ui'
import { AudioPlayer } from '@/components/player'

const authStore = useAuthStore()

onMounted(async () => {
  await authStore.initialize()
})
</script>

<template>
  <div class="min-h-screen bg-bg-primary pb-player-height">
    <Sidebar />
    <Header />
    <MainContent>
      <slot />
    </MainContent>
    <ToastContainer />
    <AudioPlayer />
  </div>
</template>
