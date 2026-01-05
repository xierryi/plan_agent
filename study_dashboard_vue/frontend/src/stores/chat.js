import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useChatStore = defineStore('chat', () => {
  const messages = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function sendMessage(content) {
    // 添加用户消息
    messages.value.push({
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    })

    loading.value = true
    error.value = null

    try {
      const response = await api.chat(content)
      
      // 添加 AI 回复
      messages.value.push({
        role: 'assistant',
        content: response.data.message,
        toolCalls: response.data.tool_calls || [],
        timestamp: new Date().toISOString()
      })
      
      return response.data
    } catch (e) {
      error.value = e.message
      messages.value.push({
        role: 'assistant',
        content: '抱歉，发生了错误，请稍后重试。',
        isError: true,
        timestamp: new Date().toISOString()
      })
      throw e
    } finally {
      loading.value = false
    }
  }

  async function generatePlan(hours, focusSubject = null, targetDate = null) {
    loading.value = true
    error.value = null

    try {
      const response = await api.generatePlan({
        total_hours: hours,
        focus_subject: focusSubject,
        date: targetDate
      })
      return response.data
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  function clearMessages() {
    messages.value = []
  }

  function addSystemMessage(content) {
    messages.value.push({
      role: 'system',
      content,
      timestamp: new Date().toISOString()
    })
  }

  return {
    messages,
    loading,
    error,
    sendMessage,
    generatePlan,
    clearMessages,
    addSystemMessage
  }
})

