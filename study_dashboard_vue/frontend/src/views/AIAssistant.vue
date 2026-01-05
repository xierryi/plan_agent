<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useChatStore } from '../stores/chat'
import { useStudyStore } from '../stores/study'

const chatStore = useChatStore()
const studyStore = useStudyStore()

const messageInput = ref('')
const chatContainer = ref(null)

// 快捷提示
const quickPrompts = [
  { icon: '📊', label: '周统计', prompt: '帮我看看这周的学习统计数据' },
  { icon: '📈', label: '效率分析', prompt: '分析一下我最近的学习效率和模式' },
  { icon: '📅', label: '生成计划', prompt: '基于我的历史数据，帮我规划明天的学习' },
  { icon: '💡', label: '给点建议', prompt: '根据我的学习数据，给我一些改进建议' }
]

// 一键生成计划
const planHours = ref(4)
const focusSubject = ref(null)
const planDate = ref('today')
const showPlanPanel = ref(false)

const subjects = [
  { value: null, label: '无重点' },
  { value: 'math', label: '数学' },
  { value: 'physics', label: '物理' },
  { value: 'econ', label: '经济' },
  { value: 'cs', label: '计算机' }
]

// 发送消息
const sendMessage = async () => {
  if (!messageInput.value.trim() || chatStore.loading) return
  
  const message = messageInput.value
  messageInput.value = ''
  
  await chatStore.sendMessage(message)
  scrollToBottom()
}

// 使用快捷提示
const useQuickPrompt = async (prompt) => {
  await chatStore.sendMessage(prompt)
  scrollToBottom()
}

// 生成并应用计划
const generateAndApplyPlan = async () => {
  try {
    const targetDate = planDate.value === 'today' 
      ? new Date().toISOString().split('T')[0]
      : new Date(Date.now() + 86400000).toISOString().split('T')[0]
    
    const result = await chatStore.generatePlan(planHours.value, focusSubject.value, targetDate)
    
    if (result.success && result.data?.tasks) {
      // 应用到 studyStore
      studyStore.currentDate = targetDate
      studyStore.plannedTasks = result.data.tasks.map((task, index) => ({
        task_id: index + 1,
        task_name: `${task.subject_name}学习`,
        subject: task.subject,
        difficulty: task.difficulty || 3,
        planned_start_time: task.start_time,
        planned_end_time: task.end_time,
        planned_duration: task.duration_minutes
      }))
      studyStore.tasksConfirmed = false
      studyStore.tasksSaved = false
      
      chatStore.addSystemMessage(`✅ 已生成 ${result.data.tasks.length} 个任务，总计 ${planHours.value} 小时！请前往「今日记录」页面查看和确认。`)
    }
  } catch (e) {
    console.error('生成计划失败:', e)
  }
  
  showPlanPanel.value = false
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

// 格式化消息内容（支持简单的 Markdown）
const formatMessage = (content) => {
  if (!content) return ''
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code class="px-1 py-0.5 bg-slate-700 rounded text-sm">$1</code>')
    .replace(/\n/g, '<br>')
}

onMounted(() => {
  if (chatStore.messages.length === 0) {
    chatStore.addSystemMessage('👋 你好！我是你的 AI 学习助手，可以帮你分析学习数据、生成计划、提供建议。试试下面的快捷操作吧！')
  }
})
</script>

<template>
  <div class="h-[calc(100vh-8rem)] flex flex-col">
    <!-- 页面标题 -->
    <div class="mb-6 animate-fade-in">
      <h1 class="text-3xl font-bold text-white mb-2">🤖 AI 助手</h1>
      <p class="text-slate-500">与 AI 对话，获取学习分析和智能建议</p>
    </div>

    <!-- 一键生成计划 -->
    <div class="card mb-6 animate-fade-in delay-100">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-white">🎯 一键生成计划</h3>
        <button 
          @click="showPlanPanel = !showPlanPanel"
          class="text-primary-400 hover:text-primary-300 text-sm"
        >
          {{ showPlanPanel ? '收起' : '展开' }}
        </button>
      </div>
      
      <div v-if="showPlanPanel" class="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="label">学习时长</label>
          <select v-model.number="planHours" class="input">
            <option v-for="h in 8" :key="h" :value="h">{{ h }} 小时</option>
          </select>
        </div>
        <div>
          <label class="label">重点学科</label>
          <select v-model="focusSubject" class="input">
            <option v-for="s in subjects" :key="s.value" :value="s.value">
              {{ s.label }}
            </option>
          </select>
        </div>
        <div>
          <label class="label">计划日期</label>
          <select v-model="planDate" class="input">
            <option value="today">今天</option>
            <option value="tomorrow">明天</option>
          </select>
        </div>
        <div class="flex items-end">
          <button 
            @click="generateAndApplyPlan"
            class="btn-primary w-full"
            :disabled="chatStore.loading"
          >
            🚀 生成并应用
          </button>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="flex flex-wrap gap-2 mb-4 animate-fade-in delay-200">
      <button
        v-for="item in quickPrompts"
        :key="item.label"
        @click="useQuickPrompt(item.prompt)"
        class="btn-secondary text-sm"
        :disabled="chatStore.loading"
      >
        {{ item.icon }} {{ item.label }}
      </button>
    </div>

    <!-- 聊天区域 -->
    <div 
      ref="chatContainer"
      class="flex-1 overflow-y-auto space-y-4 pr-2 animate-fade-in delay-300"
    >
      <div
        v-for="(msg, index) in chatStore.messages"
        :key="index"
        :class="[
          'flex',
          msg.role === 'user' ? 'justify-end' : 'justify-start'
        ]"
      >
        <div
          :class="[
            'max-w-[80%] rounded-2xl px-4 py-3',
            msg.role === 'user' 
              ? 'bg-gradient-to-r from-primary-500 to-accent-500 text-white' 
              : msg.role === 'system'
              ? 'bg-slate-800 text-slate-300 border border-slate-700'
              : 'bg-slate-800 text-slate-100',
            msg.isError ? 'border border-red-500/50' : ''
          ]"
        >
          <!-- 头像和角色 -->
          <div class="flex items-center gap-2 mb-1" v-if="msg.role !== 'user'">
            <span class="text-lg">{{ msg.role === 'system' ? '📢' : '🤖' }}</span>
            <span class="text-xs text-slate-500">
              {{ msg.role === 'system' ? '系统' : 'AI 助手' }}
            </span>
          </div>
          
          <!-- 消息内容 -->
          <div 
            class="prose prose-invert prose-sm max-w-none"
            v-html="formatMessage(msg.content)"
          ></div>

          <!-- 工具调用信息 -->
          <div 
            v-if="msg.toolCalls?.length"
            class="mt-2 pt-2 border-t border-slate-700 text-xs text-slate-500"
          >
            🔧 调用了: {{ msg.toolCalls.map(t => t.name).join(', ') }}
          </div>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="chatStore.loading" class="flex justify-start">
        <div class="bg-slate-800 rounded-2xl px-4 py-3">
          <div class="flex items-center gap-2">
            <div class="flex space-x-1">
              <div class="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
              <div class="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
              <div class="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
            </div>
            <span class="text-slate-500 text-sm">AI 正在思考...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="mt-4 animate-fade-in delay-400">
      <div class="flex gap-3">
        <input
          v-model="messageInput"
          @keyup.enter="sendMessage"
          type="text"
          class="input flex-1"
          placeholder="输入你的问题..."
          :disabled="chatStore.loading"
        />
        <button
          @click="sendMessage"
          class="btn-primary px-6"
          :disabled="!messageInput.trim() || chatStore.loading"
        >
          发送
        </button>
      </div>
      
      <div class="flex items-center justify-between mt-2">
        <span class="text-xs text-slate-500">
          按 Enter 发送消息
        </span>
        <button
          @click="chatStore.clearMessages"
          class="text-xs text-slate-500 hover:text-slate-400"
        >
          🗑️ 清空对话
        </button>
      </div>
    </div>
  </div>
</template>
