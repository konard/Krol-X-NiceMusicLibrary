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
import type { DailyListeningCount } from '@/types'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

export interface ListeningChartProps {
  data: DailyListeningCount[]
  isLoading?: boolean
}

const props = withDefaults(defineProps<ListeningChartProps>(), {
  isLoading: false,
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
let chartInstance: ChartJS<'bar'> | null = null

const chartData = computed<ChartData<'bar'>>(() => {
  const labels = props.data.map((item) => {
    const date = new Date(item.day)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  })

  const values = props.data.map((item) => item.count)

  return {
    labels,
    datasets: [
      {
        label: 'Plays',
        data: values,
        backgroundColor: 'rgba(99, 102, 241, 0.7)',
        borderColor: 'rgb(99, 102, 241)',
        borderWidth: 1,
        borderRadius: 4,
        barThickness: 'flex',
        maxBarThickness: 40,
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
          if (index >= 0 && index < props.data.length) {
            const date = new Date(props.data[index].day)
            return date.toLocaleDateString('en-US', {
              weekday: 'long',
              month: 'long',
              day: 'numeric',
            })
          }
          return ''
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
          size: 11,
        },
        maxRotation: 45,
        minRotation: 0,
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
  if (props.data.length > 0) {
    createChart()
  }
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
    <h2 class="text-h3 text-text-primary mb-4">Daily Activity</h2>

    <div
      v-if="isLoading"
      class="flex h-64 items-center justify-center"
    >
      <div class="animate-pulse text-text-muted">Loading chart...</div>
    </div>

    <div
      v-else-if="data.length === 0"
      class="flex h-64 items-center justify-center"
    >
      <p class="text-text-muted">No listening data yet</p>
    </div>

    <div
      v-else
      class="h-64"
    >
      <canvas ref="canvasRef" />
    </div>
  </div>
</template>
