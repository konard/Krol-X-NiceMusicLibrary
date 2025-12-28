<script setup lang="ts">
import { ref, computed } from 'vue'
import type { TopArtistItem } from '@/types'
import { usePlayerStore } from '@/stores/player'

export interface TopArtistsListProps {
  artists: TopArtistItem[]
  isLoading?: boolean
  limit?: number
}

const props = withDefaults(defineProps<TopArtistsListProps>(), {
  isLoading: false,
  limit: 5,
})

const playerStore = usePlayerStore()
const expandedArtist = ref<string | null>(null)

const displayedArtists = computed(() => props.artists.slice(0, props.limit))

function toggleExpand(artist: string) {
  expandedArtist.value = expandedArtist.value === artist ? null : artist
}

function playArtistSongs(artist: TopArtistItem) {
  if (artist.songs.length > 0) {
    // Play the first song and add the rest to queue
    playerStore.play(artist.songs[0])
    artist.songs.slice(1).forEach((song) => {
      playerStore.addToQueue(song)
    })
  }
}

function playSong(song: TopArtistItem['songs'][0]) {
  playerStore.play(song)
}
</script>

<template>
  <div class="card">
    <h2 class="text-h3 text-text-primary mb-4">Top Artists</h2>

    <div
      v-if="isLoading"
      class="space-y-3"
    >
      <div
        v-for="i in limit"
        :key="i"
        class="flex items-center gap-3 animate-pulse"
      >
        <div class="flex h-10 w-10 items-center justify-center rounded-full bg-bg-secondary text-text-muted">
          {{ i }}
        </div>
        <div class="flex-1">
          <div class="h-4 w-3/4 rounded bg-bg-secondary" />
          <div class="mt-1 h-3 w-1/2 rounded bg-bg-secondary" />
        </div>
      </div>
    </div>

    <div
      v-else-if="artists.length === 0"
      class="py-8 text-center"
    >
      <p class="text-text-muted">No listening data yet</p>
    </div>

    <div
      v-else
      class="space-y-2"
    >
      <div
        v-for="(item, index) in displayedArtists"
        :key="item.artist"
        class="rounded-lg transition-colors"
        :class="{ 'bg-bg-secondary/50': expandedArtist === item.artist }"
      >
        <!-- Artist Row -->
        <button
          class="flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors hover:bg-bg-secondary group"
          @click="toggleExpand(item.artist)"
        >
          <!-- Rank (circular) -->
          <div
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-small font-medium"
            :class="[
              index === 0 ? 'bg-accent-primary/20 text-accent-primary' :
              index === 1 ? 'bg-accent-secondary/20 text-accent-secondary' :
              index === 2 ? 'bg-accent-success/20 text-accent-success' :
              'bg-bg-secondary text-text-muted'
            ]"
          >
            {{ index + 1 }}
          </div>

          <!-- Artist Info -->
          <div class="min-w-0 flex-1">
            <p class="truncate font-medium text-text-primary">
              {{ item.artist }}
            </p>
            <p class="text-caption text-text-muted">
              {{ item.songs.length }} {{ item.songs.length === 1 ? 'track' : 'tracks' }}
            </p>
          </div>

          <!-- Play Count -->
          <div class="flex shrink-0 items-center gap-2">
            <span class="text-small font-medium text-accent-primary">
              {{ item.play_count }} plays
            </span>

            <!-- Expand Arrow -->
            <svg
              class="h-5 w-5 text-text-muted transition-transform"
              :class="{ 'rotate-180': expandedArtist === item.artist }"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </div>
        </button>

        <!-- Expanded Songs List -->
        <Transition
          enter-active-class="transition-all duration-200 ease-out"
          enter-from-class="opacity-0 max-h-0"
          enter-to-class="opacity-100 max-h-96"
          leave-active-class="transition-all duration-200 ease-in"
          leave-from-class="opacity-100 max-h-96"
          leave-to-class="opacity-0 max-h-0"
        >
          <div
            v-if="expandedArtist === item.artist"
            class="overflow-hidden"
          >
            <!-- Play All Button -->
            <button
              class="mx-2 mb-2 flex w-[calc(100%-1rem)] items-center gap-2 rounded-lg bg-accent-primary/10 px-3 py-2 text-small text-accent-primary transition-colors hover:bg-accent-primary/20"
              @click.stop="playArtistSongs(item)"
            >
              <svg
                class="h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M4.5 5.653c0-1.426 1.529-2.33 2.779-1.643l11.54 6.348c1.295.712 1.295 2.573 0 3.285L7.28 19.991c-1.25.687-2.779-.217-2.779-1.643V5.653z"
                  clip-rule="evenodd"
                />
              </svg>
              Play All
            </button>

            <!-- Songs -->
            <div class="space-y-1 px-2 pb-2">
              <button
                v-for="song in item.songs.slice(0, 3)"
                :key="song.id"
                class="flex w-full items-center gap-2 rounded p-2 text-left transition-colors hover:bg-bg-tertiary"
                @click.stop="playSong(song)"
              >
                <svg
                  class="h-4 w-4 shrink-0 text-text-muted"
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
                <span class="truncate text-small text-text-primary">{{ song.title }}</span>
              </button>

              <p
                v-if="item.songs.length > 3"
                class="px-2 py-1 text-caption text-text-muted"
              >
                +{{ item.songs.length - 3 }} more tracks
              </p>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>
