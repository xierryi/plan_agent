<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import { useStudyStore } from '../stores/study'

const studyStore = useStudyStore()

// 本地缓存 key
const CACHE_KEY = 'study_today_cache'

// 缓存数据到 localStorage
const cacheData = () => {
  const cacheObj = {
    date: studyStore.currentDate,
    weather: studyStore.weather,
    energyLevel: studyStore.energyLevel,
    plannedTasks: studyStore.plannedTasks,
    actualExecution: studyStore.actualExecution,
    tasksConfirmed: studyStore.tasksConfirmed,
    reflection: studyStore.reflection,
    timestamp: Date.now()
  }
  localStorage.setItem(CACHE_KEY, JSON.stringify(cacheObj))
}

// 从缓存恢复数据
const restoreFromCache = () => {
  try {
    const cached = localStorage.getItem(CACHE_KEY)
    if (!cached) return false
    
    const cacheObj = JSON.parse(cached)
    
    // 检查是否是同一天的缓存且未过期（24小时）
    const isToday = cacheObj.date === studyStore.currentDate
    const isRecent = Date.now() - cacheObj.timestamp < 24 * 60 * 60 * 1000
    
    if (isToday && isRecent && !studyStore.tasksSaved) {
      // 恢复数据
      studyStore.weather = cacheObj.weather || '晴'
      studyStore.energyLevel = cacheObj.energyLevel || 7
      
      if (cacheObj.plannedTasks?.length > 0) {
        studyStore.plannedTasks = cacheObj.plannedTasks
      }
      if (cacheObj.actualExecution?.length > 0) {
        studyStore.actualExecution = cacheObj.actualExecution
      }
      if (cacheObj.tasksConfirmed) {
        studyStore.tasksConfirmed = cacheObj.tasksConfirmed
      }
      if (cacheObj.reflection) {
        studyStore.reflection = cacheObj.reflection
      }
      
      console.log('已从缓存恢复数据')
      return true
    }
  } catch (e) {
    console.error('恢复缓存失败:', e)
  }
  return false
}

// 清除缓存
const clearCache = () => {
  localStorage.removeItem(CACHE_KEY)
}

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
  // 尝试从缓存恢复
  setTimeout(() => {
    if (!studyStore.tasksSaved) {
      restoreFromCache()
    }
  }, 500)
})

// 页面离开前保存缓存
onBeforeUnmount(() => {
  if (!studyStore.tasksSaved) {
    cacheData()
  }
})

// 日期选择
const selectedDate = ref(studyStore.currentDate)

watch(selectedDate, (newDate) => {
  studyStore.setDate(newDate)
})

// 计划任务折叠状态
const isPlanCollapsed = ref(false)

// 按时间排序的计划任务（带原始索引）
const sortedPlannedTasks = computed(() => {
  return studyStore.plannedTasks
    .map((task, index) => ({ ...task, originalIndex: index }))
    .sort((a, b) => {
      const timeA = a.planned_start_time || '99:99'
      const timeB = b.planned_start_time || '99:99'
      return timeA.localeCompare(timeB)
    })
})

// 按时间排序的实际执行（带原始索引）
const sortedActualExecution = computed(() => {
  return studyStore.actualExecution
    .map((exec, index) => ({ 
      ...exec, 
      originalIndex: index,
      plannedTask: studyStore.plannedTasks[index]
    }))
    .sort((a, b) => {
      const timeA = a.actual_start_time || a.plannedTask?.planned_start_time || '99:99'
      const timeB = b.actual_start_time || b.plannedTask?.planned_start_time || '99:99'
      return timeA.localeCompare(timeB)
    })
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

// 确认计划弹窗
const showConfirmPlanDialog = ref(false)

// 点击确认计划按钮
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
  
  // 显示确认弹窗
  showConfirmPlanDialog.value = true
}

// 最终确认计划
const executeConfirmPlan = () => {
  studyStore.confirmTasks()
  // 确认后自动折叠显示表格
  isPlanCollapsed.value = true
  showConfirmPlanDialog.value = false
}

// 取消确认
const cancelConfirmPlan = () => {
  showConfirmPlanDialog.value = false
}

// 保存记录
const handleSaveRecord = async () => {
  const success = await studyStore.saveDailyRecord()
  if (success) {
    clearCache()  // 保存成功后清除缓存
    alert('🎉 记录保存成功！')
  }
}

// 是否是今天
const isToday = computed(() => {
  return studyStore.currentDate === new Date().toISOString().split('T')[0]
})

// 滚动到指定位置
const scrollTo = (id) => {
  const element = document.getElementById(id)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

const dateStatus = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  if (studyStore.currentDate === today) return 'today'
  if (studyStore.currentDate > today) return 'future'
  return 'past'
})
</script>

<template>
  <div class="space-y-3 lg:space-y-8">
    <!-- 页面标题 -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 animate-fade-in">
      <div>
        <h1 class="text-2xl lg:text-3xl font-bold text-white mb-1">
          {{ dateStatus === 'today' ? '今日记录' : dateStatus === 'future' ? '未来计划' : '历史记录' }}
        </h1>
        <p class="text-sm text-slate-500">记录和追踪您的学习任务</p>
      </div>
      
      <div class="flex items-center gap-2 sm:gap-4">
        <input 
          type="date" 
          v-model="selectedDate"
          class="input w-auto text-sm"
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
      <h3 class="text-base lg:text-lg font-semibold text-white mb-4">📋 基本信息</h3>
      <div class="grid grid-cols-2 gap-4 lg:gap-6">
        <div>
          <label class="label text-xs lg:text-sm">天气</label>
          <select v-model="studyStore.weather" class="input text-sm" @change="cacheData">
            <option v-for="w in weatherOptions" :key="w" :value="w.split(' ')[1]">
              {{ w }}
            </option>
          </select>
        </div>
        <div>
          <label class="label text-xs lg:text-sm">精力水平</label>
          <div class="flex items-center gap-2 lg:gap-4">
            <input 
              type="range" 
              v-model.number="studyStore.energyLevel"
              min="1" 
              max="10" 
              class="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
              @input="cacheData"
            />
            <span class="text-xl lg:text-2xl font-bold text-primary-400 w-8 lg:w-12 text-center">
              {{ studyStore.energyLevel }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 计划任务 -->
    <div id="plan-tasks" class="card animate-fade-in delay-200">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <!-- 折叠按钮（确认后显示） -->
          <button 
            v-if="studyStore.tasksConfirmed"
            @click="isPlanCollapsed = !isPlanCollapsed"
            class="text-slate-400 hover:text-white transition-colors"
          >
            <span :class="['inline-block transition-transform', isPlanCollapsed ? '' : 'rotate-90']">▶</span>
          </button>
          <h3 class="text-lg font-semibold text-white">📝 计划任务</h3>
          <span v-if="studyStore.tasksConfirmed" class="px-2 py-1 bg-emerald-500/20 text-emerald-400 text-xs rounded-full">
            已确认
          </span>
        </div>
        <div class="flex gap-2">
          <button 
            @click="studyStore.addTask(); cacheData()"
            class="btn-secondary text-sm"
            :disabled="studyStore.tasksConfirmed"
            v-if="!studyStore.tasksConfirmed"
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

      <!-- 确认后的计划表格（简洁视图） -->
      <div v-if="studyStore.tasksConfirmed && isPlanCollapsed" class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-slate-700">
              <th class="text-left py-3 px-4 text-slate-400 font-medium">#</th>
              <th class="text-left py-3 px-4 text-slate-400 font-medium">任务</th>
              <th class="text-left py-3 px-4 text-slate-400 font-medium">学科</th>
              <th class="text-left py-3 px-4 text-slate-400 font-medium">时间</th>
              <th class="text-left py-3 px-4 text-slate-400 font-medium">时长</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="(task, idx) in sortedPlannedTasks" 
              :key="task.task_id"
              class="border-b border-slate-800 hover:bg-slate-800/30"
            >
              <td class="py-3 px-4 text-slate-500">{{ idx + 1 }}</td>
              <td class="py-3 px-4 text-white font-medium">{{ task.task_name }}</td>
              <td class="py-3 px-4">
                <span class="px-2 py-1 bg-slate-800 rounded text-slate-300 text-xs">
                  {{ subjects.find(s => s.value === task.subject)?.icon }} {{ subjects.find(s => s.value === task.subject)?.label }}
                </span>
              </td>
              <td class="py-3 px-4 text-slate-300">{{ task.planned_start_time }} - {{ task.planned_end_time }}</td>
              <td class="py-3 px-4 text-primary-400 font-medium">{{ formatDuration(task.planned_duration) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="bg-slate-800/30">
              <td colspan="4" class="py-3 px-4 text-right text-slate-400">总计划时间：</td>
              <td class="py-3 px-4 text-primary-400 font-bold">{{ formatDuration(studyStore.totalPlannedMinutes) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <!-- 任务列表（未折叠时显示） -->
      <div v-if="studyStore.plannedTasks.length > 0 && !isPlanCollapsed" class="space-y-2 lg:space-y-4">
        <div 
          v-for="(task, index) in studyStore.plannedTasks" 
          :key="task.task_id"
          class="p-2.5 lg:p-4 bg-slate-800/50 rounded-lg lg:rounded-xl border border-slate-700 space-y-2 lg:space-y-4"
        >
          <div class="flex items-center justify-between">
            <span class="text-sm text-slate-500">任务 {{ index + 1 }}</span>
            <button 
              v-if="!studyStore.tasksConfirmed"
              @click="studyStore.removeTask(index); cacheData()"
              class="text-red-400 hover:text-red-300 text-sm"
            >
              🗑️ 删除
            </button>
          </div>

          <div class="space-y-3">
            <div>
              <label class="label text-xs lg:text-sm">任务名称</label>
              <input 
                type="text"
                v-model="task.task_name"
                class="input text-sm"
                placeholder="输入任务名称..."
                :disabled="studyStore.tasksConfirmed"
                @input="cacheData"
              />
            </div>
            
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="label text-xs lg:text-sm">学科</label>
                <select 
                  v-model="task.subject" 
                  class="input text-sm"
                  :disabled="studyStore.tasksConfirmed"
                  @change="cacheData"
                >
                  <option v-for="s in subjects" :key="s.value" :value="s.value">
                    {{ s.icon }} {{ s.label }}
                  </option>
                </select>
              </div>

              <div>
                <label class="label text-xs lg:text-sm">难度</label>
                <select 
                  v-model.number="task.difficulty" 
                  class="input text-sm"
                  :disabled="studyStore.tasksConfirmed"
                  @change="cacheData"
                >
                  <option :value="1">⭐ 简单</option>
                  <option :value="2">⭐⭐ 较易</option>
                  <option :value="3">⭐⭐⭐ 中等</option>
                  <option :value="4">⭐⭐⭐⭐ 较难</option>
                  <option :value="5">⭐⭐⭐⭐⭐ 困难</option>
                </select>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-3 gap-2 lg:gap-4">
            <div>
              <label class="label text-xs lg:text-sm">开始</label>
              <input 
                type="time"
                v-model="task.planned_start_time"
                class="input text-sm"
                :disabled="studyStore.tasksConfirmed"
                @change="studyStore.updateTask(index, { planned_start_time: task.planned_start_time }); cacheData()"
              />
            </div>
            <div>
              <label class="label text-xs lg:text-sm">结束</label>
              <input 
                type="time"
                v-model="task.planned_end_time"
                class="input text-sm"
                :disabled="studyStore.tasksConfirmed"
                @change="studyStore.updateTask(index, { planned_end_time: task.planned_end_time }); cacheData()"
              />
            </div>
            <div class="flex items-end">
              <div class="px-2 lg:px-4 py-3 bg-primary-500/20 rounded-xl text-primary-400 font-medium w-full text-center text-xs lg:text-sm">
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
      <div v-if="studyStore.plannedTasks.length === 0 && !studyStore.tasksConfirmed" class="text-center py-12 text-slate-500">
        <div class="text-4xl mb-4">📋</div>
        <p>还没有添加任务</p>
        <button @click="studyStore.addTask(); cacheData()" class="btn-primary mt-4">
          ➕ 添加第一个任务
        </button>
      </div>
    </div>

    <!-- 实际执行（确认后显示） -->
    <div id="actual-execution" v-if="studyStore.tasksConfirmed" class="card animate-fade-in">
      <h3 class="text-base lg:text-lg font-semibold text-white mb-3 lg:mb-6">✅ 实际执行</h3>
      
      <div class="space-y-2 lg:space-y-4">
        <div 
          v-for="(item, idx) in sortedActualExecution" 
          :key="item.task_id"
          class="p-2.5 lg:p-4 bg-slate-800/50 rounded-lg lg:rounded-xl border border-slate-700"
        >
          <div class="flex items-center gap-2 lg:gap-4 mb-2 lg:mb-4">
            <div class="flex-1">
              <label class="label">实际任务名称</label>
              <input 
                type="text"
                v-model="studyStore.actualExecution[item.originalIndex].actual_task_name"
                class="input"
                :placeholder="item.plannedTask?.task_name"
                :disabled="studyStore.tasksSaved"
                @input="cacheData"
              />
              <div v-if="studyStore.actualExecution[item.originalIndex].actual_task_name !== item.plannedTask?.task_name" class="text-xs text-amber-400 mt-1">
                原计划：{{ item.plannedTask?.task_name }}
              </div>
            </div>
            <div class="pt-6">
              <label class="flex items-center gap-2 cursor-pointer">
                <input 
                  type="checkbox" 
                  v-model="studyStore.actualExecution[item.originalIndex].completed"
                  class="w-5 h-5 rounded border-slate-600 text-primary-500 focus:ring-primary-500"
                  :disabled="studyStore.tasksSaved"
                  @change="cacheData"
                />
                <span :class="studyStore.actualExecution[item.originalIndex].completed ? 'text-emerald-400' : 'text-slate-500'">
                  {{ studyStore.actualExecution[item.originalIndex].completed ? '已完成' : '未完成' }}
                </span>
              </label>
            </div>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label class="label">实际开始</label>
              <input 
                type="time"
                v-model="studyStore.actualExecution[item.originalIndex].actual_start_time"
                class="input"
                :disabled="studyStore.tasksSaved"
                @change="studyStore.updateExecution(item.originalIndex, { actual_start_time: studyStore.actualExecution[item.originalIndex].actual_start_time }); cacheData()"
              />
            </div>
            <div>
              <label class="label">实际结束</label>
              <input 
                type="time"
                v-model="studyStore.actualExecution[item.originalIndex].actual_end_time"
                class="input"
                :disabled="studyStore.tasksSaved"
                @change="studyStore.updateExecution(item.originalIndex, { actual_end_time: studyStore.actualExecution[item.originalIndex].actual_end_time }); cacheData()"
              />
            </div>
            <div>
              <label class="label">结束后精力</label>
              <select 
                v-model.number="studyStore.actualExecution[item.originalIndex].post_energy" 
                class="input"
                :disabled="studyStore.tasksSaved"
                @change="cacheData"
              >
                <option v-for="n in 10" :key="n" :value="n">{{ n }}</option>
              </select>
            </div>
            <div class="flex items-end">
              <div class="px-4 py-3 bg-accent-500/20 rounded-xl text-accent-400 font-medium w-full text-center">
                {{ formatDuration(studyStore.actualExecution[item.originalIndex].actual_duration) }}
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
          @input="cacheData"
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

    <!-- 确认计划弹窗 -->
    <Teleport to="body">
      <div 
        v-if="showConfirmPlanDialog" 
        class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
        @click="cancelConfirmPlan"
      >
        <div 
          class="bg-slate-900 border border-slate-700 rounded-2xl p-6 w-full max-w-lg mx-4 shadow-2xl"
          @click.stop
        >
          <div class="text-center mb-6">
            <div class="text-5xl mb-4">📋</div>
            <h3 class="text-xl font-semibold text-white mb-2">确认今日计划</h3>
            <p class="text-slate-400">
              确认后将锁定计划，开始记录实际执行情况
            </p>
          </div>

          <!-- 计划预览表格 -->
          <div class="bg-slate-800/50 rounded-xl p-4 mb-6 max-h-60 overflow-y-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-slate-700">
                  <th class="text-left py-2 px-2 text-slate-400 font-medium">任务</th>
                  <th class="text-left py-2 px-2 text-slate-400 font-medium">时间</th>
                  <th class="text-right py-2 px-2 text-slate-400 font-medium">时长</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="task in sortedPlannedTasks" 
                  :key="task.task_id"
                  class="border-b border-slate-700/50"
                >
                  <td class="py-2 px-2 text-white">{{ task.task_name }}</td>
                  <td class="py-2 px-2 text-slate-300">{{ task.planned_start_time }} - {{ task.planned_end_time }}</td>
                  <td class="py-2 px-2 text-primary-400 text-right">{{ formatDuration(task.planned_duration) }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="bg-slate-800/30">
                  <td colspan="2" class="py-2 px-2 text-right text-slate-400 font-medium">总计：</td>
                  <td class="py-2 px-2 text-primary-400 font-bold text-right">{{ formatDuration(studyStore.totalPlannedMinutes) }}</td>
                </tr>
              </tfoot>
            </table>
          </div>

          <div class="flex gap-3">
            <button 
              @click="cancelConfirmPlan"
              class="flex-1 btn-secondary"
            >
              返回修改
            </button>
            <button 
              @click="executeConfirmPlan"
              class="flex-1 btn-primary"
            >
              ✅ 确认计划
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 移动端悬浮快速导航（确认后显示） -->
    <div 
      v-if="studyStore.tasksConfirmed && !studyStore.tasksSaved" 
      class="lg:hidden fixed right-4 bottom-24 z-40 flex flex-col gap-2"
    >
      <button 
        @click="scrollTo('plan-tasks')"
        class="w-12 h-12 rounded-full bg-slate-800/90 backdrop-blur border border-slate-700 
               flex items-center justify-center text-xl shadow-lg
               active:scale-95 transition-transform"
        title="跳转到计划"
      >
        📝
      </button>
      <button 
        @click="scrollTo('actual-execution')"
        class="w-12 h-12 rounded-full bg-primary-500/90 backdrop-blur border border-primary-400 
               flex items-center justify-center text-xl shadow-lg shadow-primary-500/25
               active:scale-95 transition-transform"
        title="跳转到执行"
      >
        ✅
      </button>
    </div>
  </div>
</template>

