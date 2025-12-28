<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import type { MoodChainDetail, MoodChainSong } from '@/types'
import { getCoverUrl } from '@/services/moodChains'

const props = defineProps<{
  chain: MoodChainDetail
  currentSongId?: string
  isEditing?: boolean
}>()

const emit = defineEmits<{
  'node-click': [songId: string]
  'edge-click': [fromId: string, toId: string]
}>()

// Canvas refs
const containerRef = ref<HTMLElement | null>(null)
const canvasWidth = ref(800)
const canvasHeight = ref(600)

// Visualization state
const nodes = ref<VisNode[]>([])
const edges = ref<VisEdge[]>([])
const draggedNode = ref<VisNode | null>(null)
const offset = ref({ x: 0, y: 0 })

interface VisNode {
  id: string
  x: number
  y: number
  song: MoodChainSong
}

interface VisEdge {
  from: string
  to: string
  weight: number
  playCount: number
}

// Build nodes from chain songs
function buildVisualization() {
  if (!props.chain.songs.length) {
    nodes.value = []
    edges.value = []
    return
  }

  // Create nodes in a circular layout
  const centerX = canvasWidth.value / 2
  const centerY = canvasHeight.value / 2
  const radius = Math.min(canvasWidth.value, canvasHeight.value) * 0.35

  nodes.value = props.chain.songs.map((song, index) => {
    const angle = (index / props.chain.songs.length) * 2 * Math.PI - Math.PI / 2
    return {
      id: song.song_id,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
      song,
    }
  })

  // Create edges from transitions
  edges.value = props.chain.transitions.map(t => ({
    from: t.from_song_id,
    to: t.to_song_id,
    weight: t.weight,
    playCount: t.play_count,
  }))
}

// Get node by ID
function getNode(id: string): VisNode | undefined {
  return nodes.value.find(n => n.id === id)
}

// Calculate edge path
function getEdgePath(edge: VisEdge): string {
  const fromNode = getNode(edge.from)
  const toNode = getNode(edge.to)
  if (!fromNode || !toNode) return ''

  // Calculate curved path
  const dx = toNode.x - fromNode.x
  const dy = toNode.y - fromNode.y

  // Add curve for better visibility
  return `M ${fromNode.x} ${fromNode.y} Q ${(fromNode.x + toNode.x) / 2 + dy * 0.2} ${(fromNode.y + toNode.y) / 2 - dx * 0.2} ${toNode.x} ${toNode.y}`
}

// Edge stroke width based on weight
function getEdgeWidth(edge: VisEdge): number {
  return 1 + edge.weight * 4
}

// Edge opacity based on weight
function getEdgeOpacity(edge: VisEdge): number {
  return 0.3 + edge.weight * 0.5
}

// Handle node click
function handleNodeClick(node: VisNode, event: MouseEvent) {
  event.stopPropagation()
  if (!props.isEditing) {
    emit('node-click', node.id)
  }
}

// Drag handlers for editing
function handleMouseDown(node: VisNode, event: MouseEvent) {
  if (!props.isEditing) return
  draggedNode.value = node
  offset.value = {
    x: event.clientX - node.x,
    y: event.clientY - node.y,
  }
}

function handleMouseMove(event: MouseEvent) {
  if (!draggedNode.value || !props.isEditing) return

  const rect = containerRef.value?.getBoundingClientRect()
  if (!rect) return

  draggedNode.value.x = Math.max(40, Math.min(canvasWidth.value - 40, event.clientX - rect.left))
  draggedNode.value.y = Math.max(40, Math.min(canvasHeight.value - 40, event.clientY - rect.top))
}

function handleMouseUp() {
  draggedNode.value = null
}

// Resize observer
function updateSize() {
  if (containerRef.value) {
    canvasWidth.value = containerRef.value.clientWidth
    canvasHeight.value = containerRef.value.clientHeight
    buildVisualization()
  }
}

onMounted(() => {
  updateSize()
  window.addEventListener('resize', updateSize)
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateSize)
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
})

watch(() => props.chain, buildVisualization, { deep: true })
</script>

<template>
  <div ref="containerRef" class="chain-visualization">
    <svg :width="canvasWidth" :height="canvasHeight" class="vis-svg">
      <!-- Edges -->
      <g class="edges">
        <g
          v-for="edge in edges"
          :key="`${edge.from}-${edge.to}`"
          class="edge"
          @click="emit('edge-click', edge.from, edge.to)"
        >
          <path
            :d="getEdgePath(edge)"
            :stroke-width="getEdgeWidth(edge)"
            :stroke-opacity="getEdgeOpacity(edge)"
            fill="none"
            class="edge-path"
          />
          <!-- Arrow head -->
          <circle
            v-if="getNode(edge.to)"
            :cx="getNode(edge.to)!.x - (getNode(edge.to)!.x - getNode(edge.from)!.x) * 0.12"
            :cy="getNode(edge.to)!.y - (getNode(edge.to)!.y - getNode(edge.from)!.y) * 0.12"
            r="4"
            class="edge-arrow"
            :fill-opacity="getEdgeOpacity(edge)"
          />
        </g>
      </g>

      <!-- Nodes -->
      <g class="nodes">
        <g
          v-for="node in nodes"
          :key="node.id"
          class="node"
          :class="{
            current: node.id === currentSongId,
            dragging: draggedNode?.id === node.id,
          }"
          :transform="`translate(${node.x}, ${node.y})`"
          @click="handleNodeClick(node, $event)"
          @mousedown="handleMouseDown(node, $event)"
        >
          <!-- Background circle -->
          <circle r="40" class="node-bg" />

          <!-- Cover image clip -->
          <clipPath :id="`clip-${node.id}`">
            <circle r="35" />
          </clipPath>

          <!-- Cover image or placeholder -->
          <image
            v-if="node.song.cover_art_path"
            :href="getCoverUrl(node.song.cover_art_path) || ''"
            :clip-path="`url(#clip-${node.id})`"
            x="-35"
            y="-35"
            width="70"
            height="70"
            preserveAspectRatio="xMidYMid slice"
          />
          <circle
            v-else
            r="35"
            class="node-placeholder"
          />

          <!-- Play icon on hover -->
          <g class="node-play-icon" v-if="!isEditing">
            <circle r="16" class="play-bg" />
            <polygon points="-5,-8 -5,8 7,0" class="play-triangle" />
          </g>

          <!-- Current indicator ring -->
          <circle
            v-if="node.id === currentSongId"
            r="42"
            class="current-ring"
          />

          <!-- Position badge -->
          <g :transform="`translate(25, -25)`">
            <circle r="12" class="position-badge" />
            <text class="position-text">{{ node.song.position + 1 }}</text>
          </g>
        </g>
      </g>
    </svg>

    <!-- Node tooltip/label -->
    <div
      v-for="node in nodes"
      :key="`label-${node.id}`"
      class="node-label"
      :style="{
        left: `${node.x}px`,
        top: `${node.y + 50}px`,
      }"
    >
      <span class="label-title">{{ node.song.title }}</span>
      <span class="label-artist">{{ node.song.artist || 'Unknown' }}</span>
    </div>

    <!-- Legend -->
    <div class="legend">
      <div class="legend-item">
        <div class="legend-line strong" />
        <span>Strong transition</span>
      </div>
      <div class="legend-item">
        <div class="legend-line weak" />
        <span>Weak transition</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chain-visualization {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  background: var(--color-bg-primary, #fff);
}

.vis-svg {
  display: block;
}

/* Edges */
.edge {
  cursor: pointer;
}

.edge-path {
  stroke: var(--color-accent-primary, #3b82f6);
  transition: stroke-opacity 0.2s ease;
}

.edge:hover .edge-path {
  stroke-opacity: 1 !important;
}

.edge-arrow {
  fill: var(--color-accent-primary, #3b82f6);
}

/* Nodes */
.node {
  cursor: pointer;
  transition: transform 0.15s ease;
}

.node:not(.dragging):hover {
  transform: scale(1.05);
}

.node.dragging {
  cursor: grabbing;
}

.node-bg {
  fill: var(--color-bg-secondary, #f9fafb);
  stroke: var(--color-border, #e5e7eb);
  stroke-width: 2;
  transition: all 0.15s ease;
}

.node:hover .node-bg {
  stroke: var(--color-accent-primary, #3b82f6);
  stroke-width: 3;
}

.node.current .node-bg {
  stroke: var(--color-accent-success, #22c55e);
  stroke-width: 3;
}

.node-placeholder {
  fill: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.node-play-icon {
  opacity: 0;
  transition: opacity 0.15s ease;
}

.node:hover .node-play-icon {
  opacity: 1;
}

.play-bg {
  fill: rgba(0, 0, 0, 0.6);
}

.play-triangle {
  fill: white;
}

.current-ring {
  fill: none;
  stroke: var(--color-accent-success, #22c55e);
  stroke-width: 3;
  stroke-dasharray: 8 4;
  animation: rotate 10s linear infinite;
}

@keyframes rotate {
  from {
    stroke-dashoffset: 0;
  }
  to {
    stroke-dashoffset: -75;
  }
}

.position-badge {
  fill: var(--color-bg-tertiary, #e5e7eb);
  stroke: var(--color-border, #d1d5db);
  stroke-width: 1;
}

.position-text {
  font-size: 11px;
  font-weight: 600;
  fill: var(--color-text-secondary, #6b7280);
  text-anchor: middle;
  dominant-baseline: central;
}

/* Node labels */
.node-label {
  position: absolute;
  transform: translateX(-50%);
  text-align: center;
  pointer-events: none;
  max-width: 120px;
}

.label-title {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-primary, #1f2937);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.label-artist {
  display: block;
  font-size: 0.7rem;
  color: var(--color-text-secondary, #6b7280);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Legend */
.legend {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--color-bg-secondary, #f9fafb);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  font-size: 0.75rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-line {
  width: 24px;
  height: 0;
  border-radius: 2px;
}

.legend-line.strong {
  border-top: 4px solid var(--color-accent-primary, #3b82f6);
}

.legend-line.weak {
  border-top: 2px solid var(--color-accent-primary, #3b82f6);
  opacity: 0.5;
}

/* Dark mode */
:root.dark .chain-visualization {
  background: var(--color-bg-primary, #1f2937);
}

:root.dark .node-bg {
  fill: var(--color-bg-secondary, #374151);
  stroke: var(--color-border, #4b5563);
}

:root.dark .position-badge {
  fill: var(--color-bg-tertiary, #4b5563);
  stroke: var(--color-border, #6b7280);
}

:root.dark .position-text {
  fill: var(--color-text-secondary, #9ca3af);
}

:root.dark .label-title {
  color: var(--color-text-primary, #f9fafb);
}

:root.dark .legend {
  background: var(--color-bg-secondary, #374151);
  border-color: var(--color-border, #4b5563);
}
</style>
