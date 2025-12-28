<script setup lang="ts">
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useUiStore } from '@/stores/ui'
import { Dropdown } from '@/components/ui'
import type { DropdownOption } from '@/components/ui/Dropdown.vue'
import type { Theme } from '@/types'

const uiStore = useUiStore()
const { theme, isDarkMode } = storeToRefs(uiStore)

const themeOptions: DropdownOption[] = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
  { value: 'system', label: 'System' },
]

const selectedTheme = computed({
  get: () => theme.value,
  set: (value: string | number) => uiStore.setTheme(value as Theme),
})

const languageOptions: DropdownOption[] = [
  { value: 'ru', label: 'Русский' },
  { value: 'en', label: 'English' },
]

const selectedLanguage = ref<string>('en')

const crossfadeValue = ref<number>(3)
const qualityOptions: DropdownOption[] = [
  { value: 'low', label: 'Low (128 kbps)' },
  { value: 'medium', label: 'Medium (256 kbps)' },
  { value: 'high', label: 'High (320 kbps)' },
  { value: 'original', label: 'Original' },
]
const selectedQuality = ref<string>('high')
const showLyrics = ref<boolean>(true)
</script>

<template>
  <div class="animate-fade-in max-w-2xl">
    <div class="mb-8">
      <h1 class="text-h1 text-text-primary">Settings</h1>
      <p class="text-text-secondary">Customize your experience</p>
    </div>

    <!-- Appearance -->
    <div class="card mb-6">
      <h2 class="text-h3 text-text-primary mb-4">Appearance</h2>
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-body font-medium text-text-primary">Theme</p>
            <p class="text-small text-text-secondary">Choose your preferred color scheme</p>
          </div>
          <div class="w-36">
            <Dropdown
              v-model="selectedTheme"
              :options="themeOptions"
            />
          </div>
        </div>

        <div class="flex items-center justify-between">
          <div>
            <p class="text-body font-medium text-text-primary">Language</p>
            <p class="text-small text-text-secondary">Select your preferred language</p>
          </div>
          <div class="w-36">
            <Dropdown
              v-model="selectedLanguage"
              :options="languageOptions"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Playback -->
    <div class="card mb-6">
      <h2 class="text-h3 text-text-primary mb-4">Playback</h2>
      <div class="space-y-6">
        <div>
          <div class="flex items-center justify-between mb-2">
            <div>
              <p class="text-body font-medium text-text-primary">Crossfade</p>
              <p class="text-small text-text-secondary">Blend tracks together when switching</p>
            </div>
            <span class="text-small text-text-primary font-medium">{{ crossfadeValue }}s</span>
          </div>
          <input
            v-model="crossfadeValue"
            type="range"
            min="0"
            max="12"
            class="w-full h-2 bg-bg-tertiary rounded-lg appearance-none cursor-pointer accent-accent-primary"
          />
        </div>

        <div class="flex items-center justify-between">
          <div>
            <p class="text-body font-medium text-text-primary">Audio Quality</p>
            <p class="text-small text-text-secondary">Higher quality uses more bandwidth</p>
          </div>
          <div class="w-44">
            <Dropdown
              v-model="selectedQuality"
              :options="qualityOptions"
            />
          </div>
        </div>

        <div class="flex items-center justify-between">
          <div>
            <p class="text-body font-medium text-text-primary">Show Lyrics</p>
            <p class="text-small text-text-secondary">Display lyrics when available</p>
          </div>
          <button
            type="button"
            :class="[
              'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out',
              showLyrics ? 'bg-accent-primary' : 'bg-bg-tertiary',
            ]"
            role="switch"
            :aria-checked="showLyrics"
            @click="showLyrics = !showLyrics"
          >
            <span
              :class="[
                'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                showLyrics ? 'translate-x-5' : 'translate-x-0',
              ]"
            />
          </button>
        </div>
      </div>
    </div>

    <!-- Storage -->
    <div class="card">
      <h2 class="text-h3 text-text-primary mb-4">Storage</h2>
      <div class="space-y-4">
        <div>
          <div class="flex items-center justify-between mb-2">
            <p class="text-body font-medium text-text-primary">Cache Usage</p>
            <p class="text-small text-text-secondary">0 MB / 500 MB</p>
          </div>
          <div class="h-2 w-full rounded-full bg-bg-tertiary overflow-hidden">
            <div
              class="h-full bg-accent-primary rounded-full transition-all"
              style="width: 0%"
            />
          </div>
        </div>
        <button
          type="button"
          class="text-small text-accent-error hover:underline"
        >
          Clear Cache
        </button>
      </div>
    </div>

    <!-- Current Theme Info -->
    <div class="mt-6 text-center text-caption text-text-muted">
      <p>
        Current theme: <span class="font-medium">{{ isDarkMode ? 'Dark' : 'Light' }}</span>
      </p>
    </div>
  </div>
</template>
