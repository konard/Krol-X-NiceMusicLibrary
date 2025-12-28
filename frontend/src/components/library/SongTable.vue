<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Song } from '@/types'
import type { SortField, SortOrder } from '@/stores/library'
import SongRow from './SongRow.vue'
import { Loader } from '@/components/ui'

export interface SongTableProps {
  songs: Song[]
  isLoading?: boolean
  hasMore?: boolean
  sortBy?: SortField
  sortOrder?: SortOrder
  selectedSongId?: string | null
  playingSongId?: string | null
}

const props = withDefaults(defineProps<SongTableProps>(), {
  isLoading: false,
  hasMore: false,
  sortBy: 'created_at',
  sortOrder: 'desc',
  selectedSongId: null,
  playingSongId: null,
})

const emit = defineEmits<{
  sort: [field: SortField]
  loadMore: []
  select: [song: Song]
  play: [song: Song]
  favorite: [song: Song]
  edit: [song: Song]
  delete: [song: Song]
  contextmenu: [event: MouseEvent, song: Song]
}>()

const tableRef = ref<HTMLElement | null>(null)

// Column definitions
interface Column {
  key: SortField | 'index' | 'actions'
  label: string
  sortable: boolean
  class: string
  headerClass?: string
}

const columns: Column[] = [
  { key: 'index', label: '#', sortable: false, class: 'w-12 pl-4 pr-2' },
  { key: 'title', label: 'Title', sortable: true, class: 'pr-4' },
  { key: 'album', label: 'Album', sortable: true, class: 'hidden md:table-cell pr-4' },
  { key: 'created_at', label: 'Genre', sortable: false, class: 'hidden lg:table-cell pr-4', headerClass: 'hidden lg:table-cell' },
  { key: 'play_count', label: 'Plays', sortable: true, class: 'hidden xl:table-cell pr-4 text-right', headerClass: 'hidden xl:table-cell text-right' },
  { key: 'actions', label: 'Duration', sortable: false, class: 'pr-2 text-right' },
]

const sortableColumns = computed(() =>
  columns.filter((col) => col.sortable).map((col) => col.key)
)

function handleSort(field: string) {
  if (sortableColumns.value.includes(field as SortField)) {
    emit('sort', field as SortField)
  }
}

function getSortIcon(field: string) {
  if (props.sortBy !== field) return null
  return props.sortOrder === 'asc' ? '↑' : '↓'
}

function handleRowClick(song: Song) {
  emit('select', song)
}

function handleRowDblClick(song: Song) {
  emit('play', song)
}

function handleContextMenu(event: MouseEvent, song: Song) {
  emit('contextmenu', event, song)
}

function handlePlay(song: Song) {
  emit('play', song)
}

function handleFavorite(song: Song) {
  emit('favorite', song)
}

// Infinite scroll
function handleScroll() {
  if (!tableRef.value || props.isLoading || !props.hasMore) return

  const { scrollTop, scrollHeight, clientHeight } = tableRef.value
  if (scrollTop + clientHeight >= scrollHeight - 200) {
    emit('loadMore')
  }
}

onMounted(() => {
  tableRef.value?.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  tableRef.value?.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <div
    ref="tableRef"
    class="overflow-auto rounded-lg border border-bg-tertiary"
  >
    <table class="w-full min-w-[600px]">
      <!-- Header -->
      <thead class="sticky top-0 z-10 border-b border-bg-tertiary bg-bg-secondary">
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            :class="[
              'py-3 text-left text-small font-medium text-text-secondary',
              col.class,
              col.headerClass,
              col.sortable && 'cursor-pointer select-none hover:text-text-primary',
            ]"
            @click="col.sortable ? handleSort(col.key) : undefined"
          >
            <span class="inline-flex items-center gap-1">
              {{ col.label }}
              <span
                v-if="getSortIcon(col.key)"
                class="text-accent-primary"
              >
                {{ getSortIcon(col.key) }}
              </span>
            </span>
          </th>
          <!-- Extra column for favorite button -->
          <th class="w-10 py-3 pr-4" />
        </tr>
      </thead>

      <!-- Body -->
      <tbody>
        <SongRow
          v-for="(song, index) in songs"
          :key="song.id"
          :song="song"
          :index="index"
          :is-selected="selectedSongId === song.id"
          :is-playing="playingSongId === song.id"
          @click="handleRowClick"
          @dblclick="handleRowDblClick"
          @contextmenu="handleContextMenu"
          @play="handlePlay"
          @favorite="handleFavorite"
          @edit="$emit('edit', song)"
          @delete="$emit('delete', song)"
        />

        <!-- Loading row -->
        <tr v-if="isLoading && songs.length > 0">
          <td
            :colspan="columns.length + 1"
            class="py-4 text-center"
          >
            <Loader size="sm" />
          </td>
        </tr>

        <!-- Empty state -->
        <tr v-if="!isLoading && songs.length === 0">
          <td
            :colspan="columns.length + 1"
            class="py-12 text-center"
          >
            <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-bg-secondary">
              <svg
                class="h-8 w-8 text-text-muted"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M9 9l10.5-3m0 6.553v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 11-.99-3.467l2.31-.66a2.25 2.25 0 001.632-2.163zm0 0V2.25L9 5.25v10.303m0 0v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 01-.99-3.467l2.31-.66A2.25 2.25 0 009 15.553z"
                />
              </svg>
            </div>
            <p class="text-text-secondary">
              No songs found
            </p>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
