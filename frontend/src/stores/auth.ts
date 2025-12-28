import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginCredentials, RegisterCredentials, AuthTokens } from '@/types'
import { apiService, tokenManager } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!user.value && tokenManager.hasTokens())
  const currentUser = computed(() => user.value)

  // Actions
  async function login(credentials: LoginCredentials): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiService.post<AuthTokens>('/auth/login', credentials)
      tokenManager.setTokens(response.data)
      await fetchUser()
    } catch (e) {
      error.value = (e as { message: string }).message || 'Login failed'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function register(credentials: RegisterCredentials): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiService.post<AuthTokens>('/auth/register', credentials)
      tokenManager.setTokens(response.data)
      await fetchUser()
    } catch (e) {
      error.value = (e as { message: string }).message || 'Registration failed'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function logout(): Promise<void> {
    try {
      await apiService.post('/auth/logout')
    } catch {
      // Ignore logout errors
    } finally {
      tokenManager.clearTokens()
      user.value = null
    }
  }

  async function fetchUser(): Promise<void> {
    if (!tokenManager.hasTokens()) {
      user.value = null
      return
    }

    try {
      const response = await apiService.get<User>('/users/me')
      user.value = response.data
    } catch {
      tokenManager.clearTokens()
      user.value = null
    }
  }

  async function initialize(): Promise<void> {
    if (tokenManager.hasTokens()) {
      await fetchUser()
    }
  }

  function clearError(): void {
    error.value = null
  }

  return {
    // State
    user,
    isLoading,
    error,
    // Getters
    isAuthenticated,
    currentUser,
    // Actions
    login,
    register,
    logout,
    fetchUser,
    initialize,
    clearError,
  }
})
