import { ref, type Ref } from 'vue'
import type { ApiError } from '@/types'

interface UseApiOptions<T> {
  immediate?: boolean
  defaultValue?: T
  onSuccess?: (data: T) => void
  onError?: (error: ApiError) => void
}

interface UseApiReturn<T, Args extends unknown[]> {
  data: Ref<T | null>
  isLoading: Ref<boolean>
  error: Ref<ApiError | null>
  execute: (...args: Args) => Promise<T | null>
  reset: () => void
}

export function useApi<T, Args extends unknown[] = []>(
  fn: (...args: Args) => Promise<T>,
  options: UseApiOptions<T> = {}
): UseApiReturn<T, Args> {
  const { immediate = false, defaultValue = null, onSuccess, onError } = options

  const data = ref<T | null>(defaultValue) as Ref<T | null>
  const isLoading = ref(false)
  const error = ref<ApiError | null>(null)

  async function execute(...args: Args): Promise<T | null> {
    isLoading.value = true
    error.value = null

    try {
      const result = await fn(...args)
      data.value = result
      onSuccess?.(result)
      return result
    } catch (e) {
      const apiError = e as ApiError
      error.value = apiError
      onError?.(apiError)
      return null
    } finally {
      isLoading.value = false
    }
  }

  function reset() {
    data.value = defaultValue
    error.value = null
    isLoading.value = false
  }

  // Execute immediately if requested
  if (immediate) {
    execute(...([] as unknown as Args))
  }

  return {
    data,
    isLoading,
    error,
    execute,
    reset,
  }
}
