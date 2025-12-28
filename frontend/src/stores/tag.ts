/**
 * Tag Store (Pinia)
 *
 * Manages the tag state including:
 * - Tags list
 * - Create, update, delete operations
 * - Assign/remove tags from songs
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Tag, TagCreate, TagUpdate } from '@/types'
import { apiService } from '@/services/api'

// Default tag colors
export const TAG_COLORS = [
  '#ef4444', // red
  '#f97316', // orange
  '#eab308', // yellow
  '#22c55e', // green
  '#14b8a6', // teal
  '#3b82f6', // blue
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#6b7280', // gray
]

export const useTagStore = defineStore('tag', () => {
  // State
  const tags = ref<Tag[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Modal state
  const isManageModalOpen = ref(false)

  // Getters
  const tagCount = computed(() => tags.value.length)
  const isEmpty = computed(() => tags.value.length === 0 && !isLoading.value)
  const sortedTags = computed(() =>
    [...tags.value].sort((a, b) => a.name.localeCompare(b.name))
  )

  // Actions

  /**
   * Fetch all tags
   */
  async function fetchTags(): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiService.get<Tag[]>('/tags')
      tags.value = response.data
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to load tags'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create a new tag
   */
  async function createTag(data: TagCreate): Promise<Tag> {
    isLoading.value = true
    error.value = null

    try {
      // Set default color if not provided
      const tagData = {
        ...data,
        color: data.color || TAG_COLORS[tags.value.length % TAG_COLORS.length],
      }
      const response = await apiService.post<Tag>('/tags', tagData)
      const newTag = response.data
      tags.value = [...tags.value, newTag]
      return newTag
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to create tag'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update an existing tag
   */
  async function updateTag(id: string, data: TagUpdate): Promise<Tag> {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiService.patch<Tag>(`/tags/${id}`, data)
      const updatedTag = response.data

      // Update in the list
      const index = tags.value.findIndex((t) => t.id === id)
      if (index !== -1) {
        tags.value[index] = updatedTag
      }

      return updatedTag
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to update tag'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete a tag
   */
  async function deleteTag(id: string): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      await apiService.delete(`/tags/${id}`)
      tags.value = tags.value.filter((t) => t.id !== id)
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to delete tag'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Add a tag to a song
   */
  async function addTagToSong(songId: string, tagId: string): Promise<void> {
    error.value = null

    try {
      await apiService.post(`/songs/${songId}/tags`, { tag_id: tagId })
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to add tag to song'
      throw e
    }
  }

  /**
   * Remove a tag from a song
   */
  async function removeTagFromSong(songId: string, tagId: string): Promise<void> {
    error.value = null

    try {
      await apiService.delete(`/songs/${songId}/tags/${tagId}`)
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to remove tag from song'
      throw e
    }
  }

  /**
   * Get tags for a song
   */
  async function getSongTags(songId: string): Promise<Tag[]> {
    try {
      const response = await apiService.get<Tag[]>(`/songs/${songId}/tags`)
      return response.data
    } catch (e) {
      error.value = (e as { message: string }).message || 'Failed to get song tags'
      throw e
    }
  }

  /**
   * Find tag by name
   */
  function findTagByName(name: string): Tag | undefined {
    return tags.value.find((t) => t.name.toLowerCase() === name.toLowerCase())
  }

  /**
   * Open manage tags modal
   */
  function openManageModal(): void {
    isManageModalOpen.value = true
  }

  /**
   * Close manage tags modal
   */
  function closeManageModal(): void {
    isManageModalOpen.value = false
  }

  /**
   * Clear error
   */
  function clearError(): void {
    error.value = null
  }

  return {
    // State
    tags,
    isLoading,
    error,
    isManageModalOpen,

    // Getters
    tagCount,
    isEmpty,
    sortedTags,

    // Actions
    fetchTags,
    createTag,
    updateTag,
    deleteTag,
    addTagToSong,
    removeTagFromSong,
    getSongTags,
    findTagByName,
    openManageModal,
    closeManageModal,
    clearError,
  }
})
