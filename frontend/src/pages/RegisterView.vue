<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { Button, Input } from '@/components/ui'

const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUiStore()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const errors = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

function validateForm(): boolean {
  errors.value = { username: '', email: '', password: '', confirmPassword: '' }
  let isValid = true

  if (!username.value) {
    errors.value.username = 'Username is required'
    isValid = false
  } else if (username.value.length < 3) {
    errors.value.username = 'Username must be at least 3 characters'
    isValid = false
  }

  if (!email.value) {
    errors.value.email = 'Email is required'
    isValid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    errors.value.email = 'Please enter a valid email'
    isValid = false
  }

  if (!password.value) {
    errors.value.password = 'Password is required'
    isValid = false
  } else if (password.value.length < 6) {
    errors.value.password = 'Password must be at least 6 characters'
    isValid = false
  }

  if (!confirmPassword.value) {
    errors.value.confirmPassword = 'Please confirm your password'
    isValid = false
  } else if (password.value !== confirmPassword.value) {
    errors.value.confirmPassword = 'Passwords do not match'
    isValid = false
  }

  return isValid
}

async function handleSubmit() {
  if (!validateForm()) return

  isLoading.value = true

  try {
    await authStore.register({
      username: username.value,
      email: email.value,
      password: password.value,
    })

    uiStore.showSuccess('Account created successfully!')
    router.push('/')
  } catch {
    uiStore.showError(authStore.error || 'Registration failed. Please try again.')
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-[calc(100vh-10rem)] items-center justify-center">
    <div class="w-full max-w-md animate-fade-in">
      <div class="card">
        <div class="mb-6 text-center">
          <div class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-accent-primary">
            <svg
              class="h-6 w-6 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 9l10.5-3m0 6.553v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 11-.99-3.467l2.31-.66a2.25 2.25 0 001.632-2.163zm0 0V2.25L9 5.25v10.303m0 0v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 01-.99-3.467l2.31-.66A2.25 2.25 0 009 15.553z"
              />
            </svg>
          </div>
          <h1 class="text-h2 text-text-primary">Create an account</h1>
          <p class="mt-1 text-small text-text-secondary">
            Join NiceMusicLibrary today
          </p>
        </div>

        <form
          class="space-y-4"
          @submit.prevent="handleSubmit"
        >
          <Input
            v-model="username"
            type="text"
            label="Username"
            placeholder="Choose a username"
            :error="errors.username"
            :disabled="isLoading"
          />

          <Input
            v-model="email"
            type="email"
            label="Email"
            placeholder="you@example.com"
            :error="errors.email"
            :disabled="isLoading"
          />

          <Input
            v-model="password"
            type="password"
            label="Password"
            placeholder="Create a password"
            :error="errors.password"
            :disabled="isLoading"
          />

          <Input
            v-model="confirmPassword"
            type="password"
            label="Confirm Password"
            placeholder="Confirm your password"
            :error="errors.confirmPassword"
            :disabled="isLoading"
          />

          <Button
            type="submit"
            variant="primary"
            :loading="isLoading"
            full-width
          >
            Create Account
          </Button>
        </form>

        <div class="mt-6 text-center">
          <p class="text-small text-text-secondary">
            Already have an account?
            <router-link
              to="/login"
              class="font-medium text-accent-primary hover:underline"
            >
              Sign in
            </router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
