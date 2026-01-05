<script setup>
import { ref, onMounted, computed } from 'vue'
import { useStudyStore } from '../stores/study'

const studyStore = useStudyStore()

const selectedDate = ref(null)
const selectedRecord = ref(null)

onMounted(() => {
  studyStore.loadHistory(30)
})

const sortedHistory = computed(() => {
  return [...studyStore.historyData].sort((a, b) => 
    new Date(b.date) - new Date(a.date)
  )
})

const selectRecord = (record) => {
  selectedDate.value = record.date
  selectedRecord.value = record
}

const getSubjectLabel = (subject) => {
  const labels = {
    math: '📐 数学',
    physics: '⚛️ 物理',
    econ: '📈 经济',
    cs: '💻 计算机',
    other: '📖 其他'
  }
  return labels[subject] || subject
}

const formatDuration = (minutes) => {
  if (!minutes) return '0分钟'
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'short'
  })
}
</script>

<template>
  <div class="space-y-8">
    <!-- 页面标题 -->
    <div class="animate-fade-in">
      <h1 class="text-3xl font-bold text-white mb-2">📚 历史数据</h1>
      <p class="text-slate-500">浏览和回顾您的学习记录</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 日期列表 -->
      <div class="card animate-fade-in delay-100">
        <h3 class="text-lg font-semibold text-white mb-4">📅 选择日期</h3>
        
        <div v-if="sortedHistory.length > 0" class="space-y-2 max-h-[600px] overflow-y-auto pr-2">
          <button
            v-for="record in sortedHistory"
            :key="record.date"
            @click="selectRecord(record)"
            :class="[
              'w-full p-4 rounded-xl text-left transition-all duration-200',
              selectedDate === record.date 
                ? 'bg-gradient-to-r from-primary-500/20 to-accent-500/20 border border-primary-500/30' 
                : 'bg-slate-800/50 border border-slate-700 hover:border-slate-600'
            ]"
          >
            <div class="font-medium text-white">{{ formatDate(record.date) }}</div>
            <div class="text-sm text-slate-500 mt-1">
              {{ record.planned_tasks?.length || 0 }} 个任务 · 
              {{ formatDuration(record.daily_summary?.actual_total_time) }}
            </div>
            <div class="flex items-center gap-2 mt-2">
              <div 
                class="h-1.5 flex-1 bg-slate-700 rounded-full overflow-hidden"
              >
                <div 
                  class="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full"
                  :style="{ width: `${(record.daily_summary?.completion_rate || 0) * 100}%` }"
                ></div>
              </div>
              <span class="text-xs text-slate-400">
                {{ ((record.daily_summary?.completion_rate || 0) * 100).toFixed(0) }}%
              </span>
            </div>
          </button>
        </div>
        
        <div v-else class="text-center py-12 text-slate-500">
          <div class="text-4xl mb-4">📭</div>
          <p>暂无历史记录</p>
        </div>
      </div>

      <!-- 详情面板 -->
      <div class="lg:col-span-2 space-y-6">
        <template v-if="selectedRecord">
          <!-- 基本信息 -->
          <div class="card animate-fade-in">
            <h3 class="text-lg font-semibold text-white mb-4">📋 基本信息</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div class="text-sm text-slate-500">日期</div>
                <div class="font-medium text-white">{{ formatDate(selectedRecord.date) }}</div>
              </div>
              <div>
                <div class="text-sm text-slate-500">天气</div>
                <div class="font-medium text-white">{{ selectedRecord.weather }}</div>
              </div>
              <div>
                <div class="text-sm text-slate-500">精力水平</div>
                <div class="font-medium text-white">{{ selectedRecord.energy_level }}/10</div>
              </div>
              <div>
                <div class="text-sm text-slate-500">完成率</div>
                <div class="font-medium text-emerald-400">
                  {{ ((selectedRecord.daily_summary?.completion_rate || 0) * 100).toFixed(0) }}%
                </div>
              </div>
            </div>
          </div>

          <!-- 统计卡片 -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 animate-fade-in delay-100">
            <div class="stat-card">
              <div class="stat-value">
                {{ formatDuration(selectedRecord.daily_summary?.planned_total_time) }}
              </div>
              <div class="stat-label">计划时间</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">
                {{ formatDuration(selectedRecord.daily_summary?.actual_total_time) }}
              </div>
              <div class="stat-label">实际时间</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">
                {{ formatDuration(selectedRecord.daily_summary?.actual_focus_time) }}
              </div>
              <div class="stat-label">专注时间</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ selectedRecord.planned_tasks?.length || 0 }}</div>
              <div class="stat-label">任务数量</div>
            </div>
          </div>

          <!-- 任务列表 -->
          <div class="card animate-fade-in delay-200">
            <h3 class="text-lg font-semibold text-white mb-4">📝 任务详情</h3>
            <div class="space-y-3">
              <div 
                v-for="(task, index) in selectedRecord.planned_tasks"
                :key="index"
                class="p-4 bg-slate-800/50 rounded-xl border border-slate-700"
              >
                <div class="flex items-center justify-between mb-2">
                  <span class="font-medium text-white">{{ task.task_name }}</span>
                  <span class="px-2 py-1 bg-slate-700 rounded text-xs text-slate-300">
                    {{ getSubjectLabel(task.subject) }}
                  </span>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                  <div>
                    <span class="text-slate-500">计划：</span>
                    <span class="text-slate-300">
                      {{ task.planned_start_time }} - {{ task.planned_end_time }}
                    </span>
                  </div>
                  <div>
                    <span class="text-slate-500">时长：</span>
                    <span class="text-slate-300">{{ formatDuration(task.planned_duration) }}</span>
                  </div>
                  <div>
                    <span class="text-slate-500">难度：</span>
                    <span class="text-slate-300">{{ '⭐'.repeat(task.difficulty) }}</span>
                  </div>
                  <div>
                    <span 
                      :class="selectedRecord.actual_execution?.[index]?.completed ? 'text-emerald-400' : 'text-amber-400'"
                    >
                      {{ selectedRecord.actual_execution?.[index]?.completed ? '✅ 已完成' : '⏳ 未完成' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 反思 -->
          <div 
            v-if="selectedRecord.daily_summary?.reflection"
            class="card animate-fade-in delay-300"
          >
            <h3 class="text-lg font-semibold text-white mb-4">💭 当日反思</h3>
            <p class="text-slate-300 leading-relaxed">
              {{ selectedRecord.daily_summary.reflection }}
            </p>
          </div>
        </template>

        <!-- 空状态 -->
        <div v-else class="card text-center py-16 animate-fade-in">
          <div class="text-5xl mb-4">📋</div>
          <h3 class="text-xl font-semibold text-white mb-2">选择日期查看详情</h3>
          <p class="text-slate-500">点击左侧列表中的日期查看当天的学习记录</p>
        </div>
      </div>
    </div>
  </div>
</template>
