<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { Song, SongDetail, SongUpdate } from '@/types'
import { Modal, Button, Input } from '@/components/ui'
import { getCoverUrl, formatDuration, formatFileSize } from '@/services/songs'

export interface SongEditModalProps {
  modelValue: boolean
  song: Song | SongDetail | null
  isLoading?: boolean
}

const props = withDefaults(defineProps<SongEditModalProps>(), {
  isLoading: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [id: string, data: SongUpdate]
  close: []
}>()

// Form state
const title = ref('')
const artist = ref('')
const album = ref('')
const genre = ref('')
const yearStr = ref('')
const lyrics = ref('')

// Computed year as number or null
const year = computed(() => {
  const num = parseInt(yearStr.value, 10)
  return isNaN(num) ? null : num
})

// Validation
const errors = ref<Record<string, string>>({})

const isValid = computed(() => {
  return title.value.trim().length > 0 && Object.keys(errors.value).length === 0
})

const hasChanges = computed(() => {
  if (!props.song) return false
  return (
    title.value !== (props.song.title || '') ||
    artist.value !== (props.song.artist || '') ||
    album.value !== (props.song.album || '') ||
    genre.value !== (props.song.genre || '') ||
    year.value !== props.song.year ||
    (isDetailedSong.value && lyrics.value !== ((props.song as SongDetail).lyrics || ''))
  )
})

const isDetailedSong = computed(() => {
  return props.song && 'file_size_bytes' in props.song
})

const coverUrl = computed(() =>
  props.song?.cover_art_path ? getCoverUrl(props.song.id) : null
)

const duration = computed(() =>
  props.song ? formatDuration(props.song.duration_seconds) : ''
)

const fileSize = computed(() =>
  isDetailedSong.value
    ? formatFileSize((props.song as SongDetail).file_size_bytes)
    : ''
)

// Watch for song changes to reset form
watch(
  () => props.song,
  (newSong) => {
    if (newSong) {
      title.value = newSong.title || ''
      artist.value = newSong.artist || ''
      album.value = newSong.album || ''
      genre.value = newSong.genre || ''
      yearStr.value = newSong.year ? String(newSong.year) : ''
      if ('lyrics' in newSong) {
        lyrics.value = newSong.lyrics || ''
      }
    }
    errors.value = {}
  },
  { immediate: true }
)

function validateField(field: string, value: string | number | null) {
  if (field === 'title' && (!value || String(value).trim() === '')) {
    errors.value.title = 'Title is required'
  } else if (field === 'year' && value !== null) {
    const yearNum = Number(value)
    if (isNaN(yearNum) || yearNum < 1000 || yearNum > 9999) {
      errors.value.year = 'Year must be between 1000 and 9999'
    } else {
      delete errors.value.year
    }
  } else {
    delete errors.value[field]
  }
}

function handleClose() {
  emit('update:modelValue', false)
  emit('close')
}

function handleSave() {
  if (!props.song || !isValid.value || !hasChanges.value) return

  const data: SongUpdate = {}

  if (title.value !== props.song.title) {
    data.title = title.value.trim()
  }
  if (artist.value !== (props.song.artist || '')) {
    data.artist = artist.value.trim() || undefined
  }
  if (album.value !== (props.song.album || '')) {
    data.album = album.value.trim() || undefined
  }
  if (genre.value !== (props.song.genre || '')) {
    data.genre = genre.value.trim() || undefined
  }
  if (year.value !== props.song.year) {
    data.year = year.value || undefined
  }
  if (isDetailedSong.value && lyrics.value !== ((props.song as SongDetail).lyrics || '')) {
    data.lyrics = lyrics.value.trim() || undefined
  }

  emit('save', props.song.id, data)
}
</script>

<template>
  <Modal
    :model-value="modelValue"
    title="Edit Song"
    size="lg"
    @update:model-value="$emit('update:modelValue', $event)"
    @close="handleClose"
  >
    <div
      v-if="song"
      class="space-y-6"
    >
      <!-- Song info header -->
      <div class="flex gap-4">
        <!-- Cover art -->
        <div
          class="h-24 w-24 flex-shrink-0 overflow-hidden rounded-lg bg-bg-tertiary"
        >
          <img
            v-if="coverUrl"
            :src="coverUrl"
            :alt="song.title"
            class="h-full w-full object-cover"
          >
          <div
            v-else
            class="flex h-full w-full items-center justify-center"
          >
            <svg
              class="h-8 w-8 text-text-muted"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 9l10.5-3m0 6.553v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 11-.99-3.467l2.31-.66a2.25 2.25 0 001.632-2.163zm0 0V2.25L9 5.25v10.303m0 0v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 01-.99-3.467l2.31-.66A2.25 2.25 0 009 15.553z"
              />
            </svg>
          </div>
        </div>

        <!-- File info -->
        <div class="flex-1 text-small text-text-secondary">
          <p>
            <span class="text-text-muted">Format:</span>
            {{ song.file_format.toUpperCase() }}
          </p>
          <p>
            <span class="text-text-muted">Duration:</span>
            {{ duration }}
          </p>
          <p v-if="fileSize">
            <span class="text-text-muted">Size:</span>
            {{ fileSize }}
          </p>
          <p v-if="isDetailedSong && (song as SongDetail).bitrate">
            <span class="text-text-muted">Bitrate:</span>
            {{ (song as SongDetail).bitrate }} kbps
          </p>
        </div>
      </div>

      <!-- Form fields -->
      <div class="grid gap-4 sm:grid-cols-2">
        <div class="sm:col-span-2">
          <Input
            v-model="title"
            label="Title"
            placeholder="Song title"
            :error="errors.title"
            required
            @blur="validateField('title', title)"
          />
        </div>

        <Input
          v-model="artist"
          label="Artist"
          placeholder="Artist name"
        />

        <Input
          v-model="album"
          label="Album"
          placeholder="Album name"
        />

        <Input
          v-model="genre"
          label="Genre"
          placeholder="Genre"
        />

        <Input
          v-model="yearStr"
          label="Year"
          type="number"
          placeholder="Release year"
          :error="errors.year"
          @blur="validateField('year', year)"
        />
      </div>

      <!-- Lyrics (only for detailed view) -->
      <div v-if="isDetailedSong">
        <label class="mb-1.5 block text-small font-medium text-text-primary">
          Lyrics
        </label>
        <textarea
          v-model="lyrics"
          class="w-full rounded-lg border border-bg-tertiary bg-bg-primary px-4 py-2 text-text-primary placeholder-text-muted transition-colors focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary"
          rows="4"
          placeholder="Song lyrics..."
        />
      </div>
    </div>

    <template #footer>
      <Button
        variant="ghost"
        :disabled="isLoading"
        @click="handleClose"
      >
        Cancel
      </Button>
      <Button
        variant="primary"
        :disabled="!isValid || !hasChanges || isLoading"
        @click="handleSave"
      >
        <svg
          v-if="isLoading"
          class="mr-2 h-4 w-4 animate-spin"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        {{ isLoading ? 'Saving...' : 'Save Changes' }}
      </Button>
    </template>
  </Modal>
</template>
