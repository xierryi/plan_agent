import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useStudyStore = defineStore('study', () => {
  // 状态
  const currentDate = ref(new Date().toISOString().split('T')[0])
  const plannedTasks = ref([])
  const actualExecution = ref([])
  const tasksConfirmed = ref(false)
  const tasksSaved = ref(false)
  const weather = ref('晴')
  const energyLevel = ref(7)
  const reflection = ref('')
  const loading = ref(false)
  const error = ref(null)

  // 历史数据
  const historyData = ref([])
  const weeklyStats = ref(null)

  // 计算属性
  const totalPlannedMinutes = computed(() => {
    return plannedTasks.value.reduce((sum, task) => sum + (task.planned_duration || 0), 0)
  })

  const totalActualMinutes = computed(() => {
    return actualExecution.value.reduce((sum, exec) => sum + (exec.actual_duration || 0), 0)
  })

  const completionRate = computed(() => {
    if (plannedTasks.value.length === 0) return 0
    const completed = actualExecution.value.filter(e => e.completed).length
    return completed / plannedTasks.value.length
  })

  // 动作
  async function loadTodayState() {
    loading.value = true
    error.value = null
    try {
      const response = await api.getState(currentDate.value)
      if (response.data) {
        plannedTasks.value = response.data.planned_tasks || []
        actualExecution.value = response.data.actual_execution || []
        tasksConfirmed.value = response.data.tasks_confirmed || false
        tasksSaved.value = response.data.tasks_saved || false
        weather.value = response.data.weather || '晴'
        energyLevel.value = response.data.energy_level || 7
        reflection.value = response.data.reflection || ''
      }
    } catch (e) {
      error.value = e.message
      console.error('加载状态失败:', e)
    } finally {
      loading.value = false
    }
  }

  async function saveState() {
    loading.value = true
    try {
      await api.saveState({
        date: currentDate.value,
        planned_tasks: plannedTasks.value,
        actual_execution: actualExecution.value,
        tasks_confirmed: tasksConfirmed.value,
        tasks_saved: tasksSaved.value,
        weather: weather.value,
        energy_level: energyLevel.value,
        reflection: reflection.value
      })
    } catch (e) {
      error.value = e.message
      console.error('保存状态失败:', e)
    } finally {
      loading.value = false
    }
  }

  async function saveDailyRecord() {
    loading.value = true
    try {
      await api.saveDailyRecord({
        date: currentDate.value,
        weather: weather.value,
        energy_level: energyLevel.value,
        planned_tasks: plannedTasks.value,
        actual_execution: actualExecution.value,
        reflection: reflection.value
      })
      tasksSaved.value = true
      await saveState()
      return true
    } catch (e) {
      error.value = e.message
      console.error('保存记录失败:', e)
      return false
    } finally {
      loading.value = false
    }
  }

  async function loadWeeklyStats() {
    try {
      const response = await api.getWeeklyStats()
      weeklyStats.value = response.data
    } catch (e) {
      console.error('加载周统计失败:', e)
    }
  }

  async function loadHistory(days = 30) {
    try {
      const response = await api.getHistory(days)
      historyData.value = response.data || []
    } catch (e) {
      console.error('加载历史数据失败:', e)
    }
  }

  async function deleteRecord(date) {
    loading.value = true
    try {
      await api.deleteRecord(date)
      // 从本地数据中移除
      historyData.value = historyData.value.filter(d => d.date !== date)
      
      // 如果删除的是当前日期的记录，重置状态
      if (date === currentDate.value) {
        plannedTasks.value = []
        actualExecution.value = []
        tasksConfirmed.value = false
        tasksSaved.value = false
        reflection.value = ''
        // 清除本地缓存
        localStorage.removeItem('study_today_cache')
      }
      
      return true
    } catch (e) {
      error.value = e.message
      console.error('删除记录失败:', e)
      return false
    } finally {
      loading.value = false
    }
  }

  function addTask() {
    const lastTask = plannedTasks.value[plannedTasks.value.length - 1]
    const startHour = lastTask ? parseInt(lastTask.planned_end_time.split(':')[0]) : 9
    
    plannedTasks.value.push({
      task_id: plannedTasks.value.length + 1,
      task_name: '',
      subject: 'math',
      difficulty: 3,
      planned_start_time: `${String(startHour).padStart(2, '0')}:00`,
      planned_end_time: `${String(startHour + 1).padStart(2, '0')}:00`,
      planned_duration: 60
    })
  }

  function removeTask(index) {
    plannedTasks.value.splice(index, 1)
    // 重新编号
    plannedTasks.value.forEach((task, i) => {
      task.task_id = i + 1
    })
  }

  function updateTask(index, updates) {
    Object.assign(plannedTasks.value[index], updates)
    // 自动计算时长
    if (updates.planned_start_time || updates.planned_end_time) {
      const task = plannedTasks.value[index]
      const [startH, startM] = task.planned_start_time.split(':').map(Number)
      const [endH, endM] = task.planned_end_time.split(':').map(Number)
      task.planned_duration = (endH * 60 + endM) - (startH * 60 + startM)
    }
  }

  function confirmTasks() {
    tasksConfirmed.value = true
    // 初始化实际执行数据
    actualExecution.value = plannedTasks.value.map(task => ({
      task_id: task.task_id,
      actual_task_name: task.task_name,  // 默认使用计划任务名
      actual_start_time: task.planned_start_time,
      actual_end_time: task.planned_end_time,
      actual_duration: task.planned_duration,
      post_energy: 7,
      completed: false
    }))
    saveState()
  }

  function updateExecution(index, updates) {
    Object.assign(actualExecution.value[index], updates)
    // 自动计算时长
    if (updates.actual_start_time || updates.actual_end_time) {
      const exec = actualExecution.value[index]
      const [startH, startM] = exec.actual_start_time.split(':').map(Number)
      const [endH, endM] = exec.actual_end_time.split(':').map(Number)
      exec.actual_duration = (endH * 60 + endM) - (startH * 60 + startM)
    }
  }

  function setDate(date) {
    currentDate.value = date
    // 切换日期时重置状态
    plannedTasks.value = []
    actualExecution.value = []
    tasksConfirmed.value = false
    tasksSaved.value = false
    reflection.value = ''
    loadTodayState()
  }

  function clearTasks() {
    plannedTasks.value = []
    actualExecution.value = []
    tasksConfirmed.value = false
    tasksSaved.value = false
    reflection.value = ''
  }

  return {
    // 状态
    currentDate,
    plannedTasks,
    actualExecution,
    tasksConfirmed,
    tasksSaved,
    weather,
    energyLevel,
    reflection,
    loading,
    error,
    historyData,
    weeklyStats,
    // 计算属性
    totalPlannedMinutes,
    totalActualMinutes,
    completionRate,
    // 动作
    loadTodayState,
    saveState,
    saveDailyRecord,
    loadWeeklyStats,
    loadHistory,
    deleteRecord,
    addTask,
    removeTask,
    updateTask,
    confirmTasks,
    updateExecution,
    setDate,
    clearTasks
  }
})

