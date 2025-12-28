<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'

export interface ContextMenuItem {
  id: string
  label: string
  icon?: string
  disabled?: boolean
  danger?: boolean
  divider?: boolean
}

export interface ContextMenuProps {
  modelValue: boolean
  items: ContextMenuItem[]
  x?: number
  y?: number
}

const props = withDefaults(defineProps<ContextMenuProps>(), {
  x: 0,
  y: 0,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  select: [item: ContextMenuItem]
}>()

const menuRef = ref<HTMLElement | null>(null)
const position = ref({ x: 0, y: 0 })

// Adjust position to keep menu within viewport
function adjustPosition() {
  if (!menuRef.value) return

  const menu = menuRef.value
  const rect = menu.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  let x = props.x
  let y = props.y

  // Adjust horizontal position
  if (x + rect.width > viewportWidth) {
    x = viewportWidth - rect.width - 10
  }

  // Adjust vertical position
  if (y + rect.height > viewportHeight) {
    y = viewportHeight - rect.height - 10
  }

  // Ensure minimum values
  x = Math.max(10, x)
  y = Math.max(10, y)

  position.value = { x, y }
}

watch(
  () => props.modelValue,
  async (isOpen) => {
    if (isOpen) {
      position.value = { x: props.x, y: props.y }
      await nextTick()
      adjustPosition()
    }
  }
)

function handleSelect(item: ContextMenuItem) {
  if (!item.disabled && !item.divider) {
    emit('select', item)
    emit('update:modelValue', false)
  }
}

function handleClickOutside(event: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(event.target as Node)) {
    emit('update:modelValue', false)
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    emit('update:modelValue', false)
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('scroll', () => emit('update:modelValue', false), true)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-fast"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition-all duration-fast"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="modelValue"
        ref="menuRef"
        class="fixed z-50 min-w-[160px] rounded-lg border border-bg-tertiary bg-bg-primary py-1 shadow-lg"
        :style="{
          left: `${position.x}px`,
          top: `${position.y}px`,
        }"
        role="menu"
      >
        <template
          v-for="item in items"
          :key="item.id"
        >
          <!-- Divider -->
          <div
            v-if="item.divider"
            class="my-1 h-px bg-bg-tertiary"
            role="separator"
          />

          <!-- Menu item -->
          <button
            v-else
            type="button"
            :class="[
              'flex w-full items-center gap-2 px-3 py-2 text-left text-small transition-colors',
              item.disabled
                ? 'cursor-not-allowed opacity-50'
                : item.danger
                  ? 'text-accent-error hover:bg-accent-error/10'
                  : 'text-text-primary hover:bg-bg-secondary',
            ]"
            :disabled="item.disabled"
            role="menuitem"
            @click="handleSelect(item)"
          >
            <!-- Play icon -->
            <svg
              v-if="item.icon === 'play'"
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

            <!-- Add to queue icon -->
            <svg
              v-else-if="item.icon === 'queue'"
              class="h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z"
              />
            </svg>

            <!-- Add to playlist icon -->
            <svg
              v-else-if="item.icon === 'playlist'"
              class="h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>

            <!-- Heart icon -->
            <svg
              v-else-if="item.icon === 'heart' || item.icon === 'heart-filled'"
              :class="['h-4 w-4', item.icon === 'heart-filled' && 'fill-current']"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              :fill="item.icon === 'heart-filled' ? 'currentColor' : 'none'"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
              />
            </svg>

            <!-- Edit icon -->
            <svg
              v-else-if="item.icon === 'edit'"
              class="h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"
              />
            </svg>

            <!-- Delete icon -->
            <svg
              v-else-if="item.icon === 'delete'"
              class="h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
              />
            </svg>

            {{ item.label }}
          </button>
        </template>
      </div>
    </Transition>
  </Teleport>
</template>
