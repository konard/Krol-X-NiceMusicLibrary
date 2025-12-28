<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui'

const router = useRouter()

function goHome() {
  router.push('/')
}

function goBack() {
  router.back()
}
</script>

<template>
  <div class="flex min-h-[calc(100vh-10rem)] items-center justify-center animate-fade-in">
    <div class="text-center">
      <div class="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-bg-secondary">
        <svg
          class="h-12 w-12 text-text-muted"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
          />
        </svg>
      </div>
      <h1 class="text-h1 text-text-primary mb-2">404</h1>
      <p class="text-h3 text-text-secondary mb-2">Page Not Found</p>
      <p class="text-body text-text-muted mb-6 max-w-md">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <div class="flex items-center justify-center gap-3">
        <Button
          variant="secondary"
          @click="goBack"
        >
          Go Back
        </Button>
        <Button
          variant="primary"
          @click="goHome"
        >
          Go Home
        </Button>
      </div>
    </div>
  </div>
</template>
