<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMoodChainStore } from '@/stores/moodChain'
import Button from '@/components/ui/Button.vue'
import Loader from '@/components/ui/Loader.vue'
import MoodChainCard from '@/components/moodChains/MoodChainCard.vue'
import CreateChainModal from '@/components/moodChains/CreateChainModal.vue'
import CreateFromHistoryModal from '@/components/moodChains/CreateFromHistoryModal.vue'

const router = useRouter()
const moodChainStore = useMoodChainStore()

const showCreateModal = ref(false)
const showFromHistoryModal = ref(false)

const chains = computed(() => moodChainStore.chains)
const isLoading = computed(() => moodChainStore.isLoading)
const hasChains = computed(() => moodChainStore.hasChains)
const hasMore = computed(() => moodChainStore.hasMorePages)
const totalItems = computed(() => moodChainStore.totalItems)

onMounted(async () => {
  await moodChainStore.fetchChains()
})

async function loadMore() {
  await moodChainStore.loadMoreChains()
}

function openCreateModal() {
  showCreateModal.value = true
}

function openFromHistoryModal() {
  showFromHistoryModal.value = true
}

async function handleChainCreated(chainId: string) {
  showCreateModal.value = false
  showFromHistoryModal.value = false
  router.push({ name: 'mood-chain', params: { id: chainId } })
}

function handleCardClick(chainId: string) {
  router.push({ name: 'mood-chain', params: { id: chainId } })
}
</script>

<template>
  <div class="mood-chains-page">
    <!-- Header -->
    <header class="page-header">
      <div class="header-content">
        <div>
          <h1 class="page-title">Mood Chains</h1>
          <p class="page-subtitle">
            {{ totalItems }} {{ totalItems === 1 ? 'chain' : 'chains' }}
          </p>
        </div>
        <div class="header-actions">
          <Button
            variant="secondary"
            size="md"
            @click="openFromHistoryModal"
          >
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 8v4l3 3" />
              <circle cx="12" cy="12" r="10" />
            </svg>
            From History
          </Button>
          <Button
            variant="primary"
            size="md"
            @click="openCreateModal"
          >
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Create Chain
          </Button>
        </div>
      </div>
    </header>

    <!-- Content -->
    <div class="page-content">
      <!-- Loading state -->
      <div v-if="isLoading && !hasChains" class="loading-state">
        <Loader size="lg" />
        <p>Loading mood chains...</p>
      </div>

      <!-- Empty state -->
      <div v-else-if="!hasChains" class="empty-state">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
          </svg>
        </div>
        <h2>No mood chains yet</h2>
        <p>Create your first mood chain to build personalized listening experiences</p>
        <div class="empty-actions">
          <Button variant="primary" @click="openCreateModal">
            Create Your First Chain
          </Button>
          <Button variant="secondary" @click="openFromHistoryModal">
            Generate from History
          </Button>
        </div>
      </div>

      <!-- Chains grid -->
      <div v-else class="chains-grid">
        <MoodChainCard
          v-for="chain in chains"
          :key="chain.id"
          :chain="chain"
          @click="handleCardClick(chain.id)"
        />
      </div>

      <!-- Load more -->
      <div v-if="hasMore && hasChains" class="load-more">
        <Button
          variant="secondary"
          :loading="isLoading"
          @click="loadMore"
        >
          Load More
        </Button>
      </div>
    </div>

    <!-- Modals -->
    <CreateChainModal
      v-if="showCreateModal"
      @close="showCreateModal = false"
      @created="handleChainCreated"
    />

    <CreateFromHistoryModal
      v-if="showFromHistoryModal"
      @close="showFromHistoryModal = false"
      @created="handleChainCreated"
    />
  </div>
</template>

<style scoped>
.mood-chains-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
  background: var(--color-bg-primary, #fff);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-primary, #1f2937);
  margin: 0;
}

.page-subtitle {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #6b7280);
  margin: 0.25rem 0 0;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.icon {
  width: 1rem;
  height: 1rem;
  margin-right: 0.5rem;
}

.page-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}

.loading-state p,
.empty-state p {
  color: var(--color-text-secondary, #6b7280);
  margin-top: 1rem;
}

.empty-icon {
  width: 80px;
  height: 80px;
  margin-bottom: 1.5rem;
  color: var(--color-text-muted, #9ca3af);
}

.empty-icon svg {
  width: 100%;
  height: 100%;
}

.empty-state h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary, #1f2937);
  margin: 0 0 0.5rem;
}

.empty-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.chains-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
}

/* Dark mode */
:root.dark .page-header {
  background: var(--color-bg-primary, #1f2937);
  border-color: var(--color-border, #374151);
}

:root.dark .page-title {
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .empty-state h2 {
  color: var(--color-text-primary, #f9fafb);
}
</style>
