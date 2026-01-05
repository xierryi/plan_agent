<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useStudyStore } from '../stores/study'

const studyStore = useStudyStore()

const subjects = [
  { value: 'math', label: '数学', icon: '📐' },
  { value: 'physics', label: '物理', icon: '⚛️' },
  { value: 'econ', label: '经济', icon: '📈' },
  { value: 'cs', label: '计算机', icon: '💻' },
  { value: 'other', label: '其他', icon: '📖' }
]

const weatherOptions = ['☀️ 晴', '⛅ 多云', '🌧️ 雨', '☁️ 阴', '❄️ 雪']

onMounted(() => {
  studyStore.loadTodayState()
})

// 日期选择
const selectedDate = ref(studyStore.currentDate)

watch(selectedDate, (newDate) => {
  studyStore.setDate(newDate)
})

// 时间格式化
const formatDuration = (minutes) => {
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
}

// 时间转分钟数（用于比较）
const timeToMinutes = (timeStr) => {
  if (!timeStr) return 0
  const [h, m] = timeStr.split(':').map(Number)
  return h * 60 + m
}

// 检查时间冲突
const timeConflicts = computed(() => {
  const conflicts = []
  const tasks = studyStore.plannedTasks
  
  for (let i = 0; i < tasks.length; i++) {
    const task1 = tasks[i]
    if (!task1.planned_start_time || !task1.planned_end_time || !task1.task_name) continue
    
    const start1 = timeToMinutes(task1.planned_start_time)
    const end1 = timeToMinutes(task1.planned_end_time)
    
    // 检查结束时间是否在开始时间之前
    if (end1 <= start1) {
      conflicts.push({
        type: 'invalid',
        message: `「${task1.task_name || '任务' + (i+1)}」结束时间必须晚于开始时间`
      })
      continue
    }
    
    // 检查与其他任务的冲突
    for (let j = i + 1; j < tasks.length; j++) {
      const task2 = tasks[j]
      if (!task2.planned_start_time || !task2.planned_end_time || !task2.task_name) continue
      
      const start2 = timeToMinutes(task2.planned_start_time)
      const end2 = timeToMinutes(task2.planned_end_time)
      
      // 检查时间重叠
      if (start1 < end2 && end1 > start2) {
        conflicts.push({
          type: 'overlap',
          message: `「${task1.task_name}」和「${task2.task_name}」时间重叠`
        })
      }
    }
  }
  
  return conflicts
})

// 是否有时间冲突
const hasConflicts = computed(() => timeConflicts.value.length > 0)

// 确认任务
const handleConfirmTasks = () => {
  if (studyStore.plannedTasks.length === 0) {
    alert('请至少添加一个任务')
    return
  }
  
  const hasEmptyTask = studyStore.plannedTasks.some(t => !t.task_name.trim())
  if (hasEmptyTask) {
    alert('请填写所有任务名称')
    return
  }
  
  // 检查时间冲突
  if (hasConflicts.value) {
    alert('❌ 存在时间冲突，请先解决：\n\n' + timeConflicts.value.map(c => '• ' + c.message).join('\n'))
    return
  }
  
  studyStore.confirmTasks()
}

// 保存记录
const handleSaveRecord = async () => {
  const success = await studyStore.saveDailyRecord()
  if (success) {
    alert('🎉 记录保存成功！')
  }
}

// 是否是今天
const isToday = computed(() => {
  return studyStore.currentDate === new Date().toISOString().split('T')[0]
})

const dateStatus = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  if (studyStore.currentDate === today) return 'today'
  if (studyStore.currentDate > today) return 'future'
  return 'past'
})
</script>

<template>
  <div class="space-y-8">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between animate-fade-in">
      <div>
        <h1 class="text-3xl font-bold text-white mb-2">
          {{ dateStatus === 'today' ? '今日记录' : dateStatus === 'future' ? '未来计划' : '历史记录' }}
        </h1>
        <p class="text-slate-500">记录和追踪您的学习任务</p>
      </div>
      
      <div class="flex items-center gap-4">
        <input 
          type="date" 
          v-model="selectedDate"
          class="input w-auto"
        />
        <span 
          :class="[
            'px-3 py-1 rounded-full text-sm',
            dateStatus === 'today' ? 'bg-emerald-500/20 text-emerald-400' :
            dateStatus === 'future' ? 'bg-amber-500/20 text-amber-400' :
            'bg-slate-500/20 text-slate-400'
          ]"
        >
          {{ dateStatus === 'today' ? '📅 今天' : dateStatus === 'future' ? '🔮 未来' : '📚 过往' }}
        </span>
      </div>
    </div>

    <!-- 基本信息 -->
    <div class="card animate-fade-in delay-100">
      <h3 class="text-lg font-semibold text-white mb-4">📋 基本信息</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label class="label">天气</label>
          <select v-model="studyStore.weather" class="input">
            <option v-for="w in weatherOptions" :key="w" :value="w.split(' ')[1]">
              {{ w }}
            </option>
          </select>
        </div>
        <div>
          <label class="label">精力水平</label>
          <div class="flex items-center gap-4">
            <input 
              type="range" 
              v-model.number="studyStore.energyLevel"
              min="1" 
              max="10" 
              class="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
            />
            <span class="text-2xl font-bold text-primary-400 w-12 text-center">
              {{ studyStore.energyLevel }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 计划任务 -->
    <div class="card animate-fade-in delay-200">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-lg font-semibold text-white">📝 计划任务</h3>
        <div class="flex gap-2">
          <button 
            @click="studyStore.addTask"
            class="btn-secondary text-sm"
            :disabled="studyStore.tasksConfirmed"
          >
            ➕ 添加任务
          </button>
          <button
            v-if="!studyStore.tasksConfirmed"
            @click="handleConfirmTasks"
            class="btn-primary text-sm"
            :disabled="studyStore.plannedTasks.length === 0"
          >
            ✅ 确认计划
          </button>
        </div>
      </div>

      <!-- 任务列表 -->
      <div v-if="studyStore.plannedTasks.length > 0" class="space-y-4">
        <div 
          v-for="(task, index) in studyStore.plannedTasks" 
          :key="task.task_id"
          class="p-4 bg-slate-800/50 rounded-xl border border-slate-700 space-y-4"
        >
          <div class="flex items-center justify-between">
            <span class="text-sm text-slate-500">任务 {{ index + 1 }}</span>
            <button 
              v-if="!studyStore.tasksConfirmed"
              @click="studyStore.removeTask(index)"
              class="text-red-400 hover:text-red-300 text-sm"
            >
              🗑️ 删除
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="lg:col-span-2">
              <label class="label">任务名称</label>
              <input 
                type="text"
                v-model="task.task_name"
                class="input"
                placeholder="输入任务名称..."
                :disabled="studyStore.tasksConfirmed"
              />
            </div>
            
            <div>
              <label class="label">学科</label>
              <select 
                v-model="task.subject" 
                class="input"
                :disabled="studyStore.tasksConfirmed"
              >
                <option v-for="s in subjects" :key="s.value" :value="s.value">
                  {{ s.icon }} {{ s.label }}
                </option>
              </select>
            </div>

            <div>
              <label class="label">难度</label>
              <select 
                v-model.number="task.difficulty" 
                class="input"
                :disabled="studyStore.tasksConfirmed"
              >
                <option :value="1">⭐ 简单</option>
                <option :value="2">⭐⭐ 较易</option>
                <option :value="3">⭐⭐⭐ 中等</option>
                <option :value="4">⭐⭐⭐⭐ 较难</option>
                <option :value="5">⭐⭐⭐⭐⭐ 困难</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label class="label">开始时间</label>
              <input 
                type="time"
                v-model="task.planned_start_time"
                class="input"
                :disabled="studyStore.tasksConfirmed"
                @change="studyStore.updateTask(index, { planned_start_time: task.planned_start_time })"
              />
            </div>
            <div>
              <label class="label">结束时间</label>
              <input 
                type="time"
                v-model="task.planned_end_time"
                class="input"
                :disabled="studyStore.tasksConfirmed"
                @change="studyStore.updateTask(index, { planned_end_time: task.planned_end_time })"
              />
            </div>
            <div class="flex items-end">
              <div class="px-4 py-3 bg-primary-500/20 rounded-xl text-primary-400 font-medium w-full text-center">
                {{ formatDuration(task.planned_duration) }}
              </div>
            </div>
          </div>
        </div>

        <!-- 时间冲突警告 -->
        <div v-if="hasConflicts && !studyStore.tasksConfirmed" class="p-4 bg-red-500/10 border border-red-500/30 rounded-xl">
          <div class="flex items-center gap-2 text-red-400 font-medium mb-2">
            <span>⚠️</span>
            <span>检测到时间冲突</span>
          </div>
          <ul class="space-y-1 text-sm text-red-300">
            <li v-for="(conflict, idx) in timeConflicts" :key="idx" class="flex items-start gap-2">
              <span>•</span>
              <span>{{ conflict.message }}</span>
            </li>
          </ul>
        </div>

        <!-- 总计 -->
        <div class="flex justify-end">
          <div class="px-6 py-3 bg-gradient-to-r from-primary-500/20 to-accent-500/20 rounded-xl">
            <span class="text-slate-400">总计划时间：</span>
            <span class="text-xl font-bold text-white ml-2">
              {{ formatDuration(studyStore.totalPlannedMinutes) }}
            </span>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="text-center py-12 text-slate-500">
        <div class="text-4xl mb-4">📋</div>
        <p>还没有添加任务</p>
        <button @click="studyStore.addTask" class="btn-primary mt-4">
          ➕ 添加第一个任务
        </button>
      </div>
    </div>

    <!-- 实际执行（确认后显示） -->
    <div v-if="studyStore.tasksConfirmed" class="card animate-fade-in">
      <h3 class="text-lg font-semibold text-white mb-6">✅ 实际执行</h3>
      
      <div class="space-y-4">
        <div 
          v-for="(exec, index) in studyStore.actualExecution" 
          :key="exec.task_id"
          class="p-4 bg-slate-800/50 rounded-xl border border-slate-700"
        >
          <div class="flex items-center justify-between mb-4">
            <span class="font-medium text-white">
              {{ studyStore.plannedTasks[index]?.task_name }}
            </span>
            <label class="flex items-center gap-2 cursor-pointer">
              <input 
                type="checkbox" 
                v-model="exec.completed"
                class="w-5 h-5 rounded border-slate-600 text-primary-500 focus:ring-primary-500"
                :disabled="studyStore.tasksSaved"
              />
              <span :class="exec.completed ? 'text-emerald-400' : 'text-slate-500'">
                {{ exec.completed ? '已完成' : '未完成' }}
              </span>
            </label>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label class="label">实际开始</label>
              <input 
                type="time"
                v-model="exec.actual_start_time"
                class="input"
                :disabled="studyStore.tasksSaved"
                @change="studyStore.updateExecution(index, { actual_start_time: exec.actual_start_time })"
              />
            </div>
            <div>
              <label class="label">实际结束</label>
              <input 
                type="time"
                v-model="exec.actual_end_time"
                class="input"
                :disabled="studyStore.tasksSaved"
                @change="studyStore.updateExecution(index, { actual_end_time: exec.actual_end_time })"
              />
            </div>
            <div>
              <label class="label">结束后精力</label>
              <select 
                v-model.number="exec.post_energy" 
                class="input"
                :disabled="studyStore.tasksSaved"
              >
                <option v-for="n in 10" :key="n" :value="n">{{ n }}</option>
              </select>
            </div>
            <div class="flex items-end">
              <div class="px-4 py-3 bg-accent-500/20 rounded-xl text-accent-400 font-medium w-full text-center">
                {{ formatDuration(exec.actual_duration) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 反思 -->
      <div class="mt-6">
        <label class="label">📝 今日反思</label>
        <textarea 
          v-model="studyStore.reflection"
          class="input min-h-24"
          placeholder="今天的收获和改进点..."
          :disabled="studyStore.tasksSaved"
        ></textarea>
      </div>

      <!-- 保存按钮 -->
      <div class="mt-6 flex justify-end">
        <button
          v-if="!studyStore.tasksSaved"
          @click="handleSaveRecord"
          class="btn-primary"
          :disabled="studyStore.loading"
        >
          {{ studyStore.loading ? '保存中...' : '💾 保存今日记录' }}
        </button>
        <div v-else class="px-6 py-3 bg-emerald-500/20 rounded-xl text-emerald-400">
          ✅ 记录已保存
        </div>
      </div>
    </div>
  </div>
</template>

