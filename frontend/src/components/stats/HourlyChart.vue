<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  type ChartData,
  type ChartOptions,
} from 'chart.js'
import type { HourlyListeningCount } from '@/types'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

export interface HourlyChartProps {
  data: HourlyListeningCount[]
  isLoading?: boolean
}

const props = withDefaults(defineProps<HourlyChartProps>(), {
  isLoading: false,
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
let chartInstance: ChartJS<'bar'> | null = null

// Generate all 24 hours data (fill missing hours with 0)
const fullDayData = computed(() => {
  const hourMap = new Map<number, number>()
  props.data.forEach((item) => {
    hourMap.set(item.hour, item.count)
  })

  return Array.from({ length: 24 }, (_, hour) => ({
    hour,
    count: hourMap.get(hour) || 0,
  }))
})

const chartData = computed<ChartData<'bar'>>(() => {
  const labels = fullDayData.value.map((item) => {
    const hour = item.hour
    const period = hour >= 12 ? 'PM' : 'AM'
    const displayHour = hour % 12 || 12
    return `${displayHour}${period}`
  })

  const values = fullDayData.value.map((item) => item.count)

  // Create gradient colors based on value intensity
  const maxValue = Math.max(...values, 1)
  const backgroundColors = values.map((value) => {
    const intensity = value / maxValue
    const alpha = 0.3 + intensity * 0.5
    return `rgba(99, 102, 241, ${alpha})`
  })

  return {
    labels,
    datasets: [
      {
        label: 'Plays',
        data: values,
        backgroundColor: backgroundColors,
        borderColor: 'rgb(99, 102, 241)',
        borderWidth: 1,
        borderRadius: 2,
        barThickness: 'flex',
      },
    ],
  }
})

const chartOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#fff',
      bodyColor: '#fff',
      padding: 12,
      cornerRadius: 8,
      displayColors: false,
      callbacks: {
        title: (items) => {
          if (items.length === 0) return ''
          const index = items[0].dataIndex
          const hour = index
          const period = hour >= 12 ? 'PM' : 'AM'
          const displayHour = hour % 12 || 12
          const nextHour = (hour + 1) % 12 || 12
          const nextPeriod = (hour + 1) >= 12 && (hour + 1) < 24 ? 'PM' : 'AM'
          return `${displayHour}:00 ${period} - ${nextHour}:00 ${nextPeriod}`
        },
        label: (item) => `${item.raw} plays`,
      },
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
      ticks: {
        color: 'rgba(156, 163, 175, 0.8)',
        font: {
          size: 10,
        },
        maxRotation: 0,
        callback: function(_, index) {
          // Show every 3rd hour
          if (index % 3 === 0) {
            return this.getLabelForValue(index)
          }
          return ''
        },
      },
    },
    y: {
      beginAtZero: true,
      grid: {
        color: 'rgba(156, 163, 175, 0.1)',
      },
      ticks: {
        color: 'rgba(156, 163, 175, 0.8)',
        font: {
          size: 11,
        },
        precision: 0,
      },
    },
  },
}

function createChart() {
  if (!canvasRef.value) return

  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  chartInstance = new ChartJS(canvasRef.value, {
    type: 'bar',
    data: chartData.value,
    options: chartOptions,
  })
}

function updateChart() {
  if (chartInstance) {
    chartInstance.data = chartData.value
    chartInstance.update('none')
  }
}

watch(() => props.data, () => {
  if (chartInstance) {
    updateChart()
  } else {
    createChart()
  }
}, { deep: true })

onMounted(() => {
  createChart()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})
</script>

<template>
  <div class="card">
    <h2 class="text-h3 text-text-primary mb-4">Listening by Hour</h2>

    <div
      v-if="isLoading"
      class="flex h-48 items-center justify-center"
    >
      <div class="animate-pulse text-text-muted">Loading chart...</div>
    </div>

    <div
      v-else-if="data.length === 0"
      class="flex h-48 items-center justify-center"
    >
      <p class="text-text-muted">No listening data yet</p>
    </div>

    <div
      v-else
      class="h-48"
    >
      <canvas ref="canvasRef" />
    </div>
  </div>
</template>
