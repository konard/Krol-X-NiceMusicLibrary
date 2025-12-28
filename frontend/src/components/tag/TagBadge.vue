<script setup lang="ts">
import { computed } from 'vue'
import type { Tag } from '@/types'

export interface TagBadgeProps {
  tag: Tag
  removable?: boolean
  size?: 'sm' | 'md'
}

const props = withDefaults(defineProps<TagBadgeProps>(), {
  removable: false,
  size: 'md',
})

const emit = defineEmits<{
  remove: [tag: Tag]
  click: [tag: Tag]
}>()

const sizeClasses = computed(() => {
  if (props.size === 'sm') {
    return 'text-caption px-1.5 py-0.5'
  }
  return 'text-small px-2 py-1'
})

const backgroundColor = computed(() => {
  return `${props.tag.color}20` // 20 is hex for ~12% opacity
})

const borderColor = computed(() => {
  return `${props.tag.color}40` // 40 is hex for ~25% opacity
})

function handleClick() {
  emit('click', props.tag)
}

function handleRemove(event: MouseEvent) {
  event.stopPropagation()
  emit('remove', props.tag)
}
</script>

<template>
  <span
    :class="[
      'inline-flex items-center gap-1 rounded-full border font-medium transition-colors',
      sizeClasses,
      'cursor-pointer hover:opacity-80',
    ]"
    :style="{
      backgroundColor: backgroundColor,
      borderColor: borderColor,
      color: tag.color,
    }"
    @click="handleClick"
  >
    {{ tag.name }}

    <button
      v-if="removable"
      type="button"
      class="ml-0.5 rounded-full p-0.5 transition-colors hover:bg-black/10"
      aria-label="Remove tag"
      @click="handleRemove"
    >
      <svg
        class="h-3 w-3"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>
    </button>
  </span>
</template>
