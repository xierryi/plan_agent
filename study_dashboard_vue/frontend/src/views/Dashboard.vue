<script setup>
import { ref, onMounted, computed } from 'vue'
import { Line, Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { useStudyStore } from '../stores/study'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const studyStore = useStudyStore()

onMounted(() => {
  studyStore.loadWeeklyStats()
  studyStore.loadHistory(14)
})

// 模拟数据（实际从 API 获取）
const stats = ref({
  avgCompletion: 0.85,
  avgEfficiency: 0.78,
  totalHours: 42.5,
  avgAccuracy: 0.82
})

const trendData = computed(() => ({
  labels: studyStore.historyData.slice(-7).map(d => d.date?.slice(5) || ''),
  datasets: [
    {
      label: '完成率',
      data: studyStore.historyData.slice(-7).map(d => d.daily_summary?.completion_rate * 100 || 0),
      borderColor: '#0ea5e9',
      backgroundColor: 'rgba(14, 165, 233, 0.1)',
      fill: true,
      tension: 0.4
    },
    {
      label: '专注效率',
      data: studyStore.historyData.slice(-7).map(d => (d.daily_summary?.actual_focus_time / d.daily_summary?.planned_focus_time * 100) || 0),
      borderColor: '#d946ef',
      backgroundColor: 'rgba(217, 70, 239, 0.1)',
      fill: true,
      tension: 0.4
    }
  ]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: '#94a3b8',
        usePointStyle: true
      }
    }
  },
  scales: {
    x: {
      grid: { color: 'rgba(148, 163, 184, 0.1)' },
      ticks: { color: '#94a3b8' }
    },
    y: {
      grid: { color: 'rgba(148, 163, 184, 0.1)' },
      ticks: { color: '#94a3b8' },
      max: 100
    }
  }
}

const subjectData = computed(() => ({
  labels: ['数学', '物理', '经济', '计算机', '其他'],
  datasets: [{
    data: [35, 25, 20, 15, 5],
    backgroundColor: [
      '#0ea5e9',
      '#d946ef',
      '#22c55e',
      '#f59e0b',
      '#6b7280'
    ],
    borderWidth: 0
  }]
}))

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'right',
      labels: {
        color: '#94a3b8',
        usePointStyle: true,
        padding: 15
      }
    }
  },
  cutout: '70%'
}
</script>

<template>
  <div class="space-y-8">
    <!-- 页面标题 -->
    <div class="animate-fade-in">
      <h1 class="text-3xl font-bold text-white mb-2">数据看板</h1>
      <p class="text-slate-500">查看您的学习数据统计和趋势分析</p>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div class="stat-card animate-fade-in delay-100">
        <div class="stat-value">{{ (stats.avgCompletion * 100).toFixed(0) }}%</div>
        <div class="stat-label">平均完成率</div>
        <div class="mt-3 text-xs text-emerald-400">↑ 较上周 +5%</div>
      </div>
      
      <div class="stat-card animate-fade-in delay-200">
        <div class="stat-value">{{ (stats.avgEfficiency * 100).toFixed(0) }}%</div>
        <div class="stat-label">平均专注效率</div>
        <div class="mt-3 text-xs text-emerald-400">↑ 较上周 +3%</div>
      </div>
      
      <div class="stat-card animate-fade-in delay-300">
        <div class="stat-value">{{ stats.totalHours.toFixed(1) }}h</div>
        <div class="stat-label">本周学习时长</div>
        <div class="mt-3 text-xs text-slate-500">目标: 50h</div>
      </div>
      
      <div class="stat-card animate-fade-in delay-400">
        <div class="stat-value">{{ (stats.avgAccuracy * 100).toFixed(0) }}%</div>
        <div class="stat-label">计划准确性</div>
        <div class="mt-3 text-xs text-amber-400">→ 持平</div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 趋势图 -->
      <div class="lg:col-span-2 card animate-fade-in">
        <h3 class="text-lg font-semibold text-white mb-6">学习效率趋势</h3>
        <div class="h-80">
          <Line :data="trendData" :options="chartOptions" />
        </div>
      </div>

      <!-- 学科分布 -->
      <div class="card animate-fade-in">
        <h3 class="text-lg font-semibold text-white mb-6">学科时间分布</h3>
        <div class="h-80">
          <Doughnut :data="subjectData" :options="doughnutOptions" />
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="card animate-fade-in">
      <h3 class="text-lg font-semibold text-white mb-4">快捷操作</h3>
      <div class="flex flex-wrap gap-4">
        <router-link to="/today" class="btn-primary">
          📝 开始今日记录
        </router-link>
        <router-link to="/ai-assistant" class="btn-secondary">
          🤖 咨询 AI 助手
        </router-link>
        <router-link to="/history" class="btn-secondary">
          📚 查看历史数据
        </router-link>
      </div>
    </div>
  </div>
</template>

