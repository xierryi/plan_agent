<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const syncStatus = ref({
  connected: false,
  repo_info: '',
  data_count: 0,
  last_sync: null
})

const loading = ref(false)

const fetchSyncStatus = async () => {
  try {
    const response = await api.getSyncStatus()
    syncStatus.value = response.data
  } catch (e) {
    console.error('获取同步状态失败:', e)
  }
}

const handleSync = async () => {
  loading.value = true
  try {
    await api.syncToGithub()
    await fetchSyncStatus()
    alert('✅ 同步成功！')
  } catch (e) {
    console.error('同步失败:', e)
    alert('❌ 同步失败，请检查配置')
  } finally {
    loading.value = false
  }
}

const formatDateTime = (isoString) => {
  if (!isoString) return '从未同步'
  return new Date(isoString).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchSyncStatus()
})
</script>

<template>
  <div class="space-y-8">
    <!-- 页面标题 -->
    <div class="animate-fade-in">
      <h1 class="text-3xl font-bold text-white mb-2">⚙️ 设置</h1>
      <p class="text-slate-500">管理应用配置和数据同步</p>
    </div>

    <!-- GitHub 同步 -->
    <div class="card animate-fade-in delay-100">
      <h3 class="text-lg font-semibold text-white mb-6">☁️ GitHub 数据同步</h3>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <!-- 状态 -->
        <div>
          <h4 class="text-sm font-medium text-slate-400 mb-4">连接状态</h4>
          
          <div class="space-y-4">
            <div class="flex items-center gap-3">
              <div 
                :class="[
                  'w-3 h-3 rounded-full',
                  syncStatus.connected ? 'bg-emerald-500' : 'bg-amber-500'
                ]"
              ></div>
              <span class="text-white">
                {{ syncStatus.connected ? 'GitHub 已连接' : '未连接 GitHub' }}
              </span>
            </div>

            <div v-if="syncStatus.connected" class="space-y-3 text-sm">
              <div class="flex justify-between">
                <span class="text-slate-500">仓库</span>
                <span class="text-slate-300">{{ syncStatus.repo_info }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-500">数据记录</span>
                <span class="text-slate-300">{{ syncStatus.data_count }} 条</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-500">最后同步</span>
                <span class="text-slate-300">{{ formatDateTime(syncStatus.last_sync) }}</span>
              </div>
            </div>

            <button
              @click="handleSync"
              class="btn-primary w-full mt-4"
              :disabled="loading || !syncStatus.connected"
            >
              {{ loading ? '同步中...' : '🔄 立即同步' }}
            </button>
          </div>
        </div>

        <!-- 配置说明 -->
        <div>
          <h4 class="text-sm font-medium text-slate-400 mb-4">配置说明</h4>
          
          <div class="space-y-4 text-sm text-slate-400">
            <p>使用 GitHub 作为数据存储，实现：</p>
            <ul class="list-disc list-inside space-y-1 ml-2">
              <li>🔄 多设备数据同步</li>
              <li>💾 自动版本控制</li>
              <li>🆓 完全免费</li>
              <li>🔒 数据安全</li>
            </ul>
            
            <div class="p-4 bg-slate-800/50 rounded-xl border border-slate-700 mt-4">
              <p class="text-slate-300 mb-2">需要配置环境变量：</p>
              <code class="text-xs text-primary-400 block">
                GITHUB_TOKEN=ghp_xxx<br/>
                GITHUB_OWNER=username<br/>
                GITHUB_REPO=repo-name
              </code>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- API 配置 -->
    <div class="card animate-fade-in delay-200">
      <h3 class="text-lg font-semibold text-white mb-6">🔌 API 配置</h3>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label class="label">后端 API 地址</label>
          <input 
            type="text" 
            class="input" 
            value="http://localhost:8000/api"
            disabled
          />
          <p class="text-xs text-slate-500 mt-1">在 .env 文件中配置 VITE_API_URL</p>
        </div>
        <div>
          <label class="label">AI 模型</label>
          <input 
            type="text" 
            class="input" 
            value="gemini-2.5-pro"
            disabled
          />
          <p class="text-xs text-slate-500 mt-1">在后端环境变量中配置 MODEL_NAME</p>
        </div>
      </div>
    </div>

    <!-- 关于 -->
    <div class="card animate-fade-in delay-300">
      <h3 class="text-lg font-semibold text-white mb-6">📖 关于</h3>
      
      <div class="flex items-start gap-6">
        <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-3xl shrink-0">
          📚
        </div>
        <div>
          <h4 class="text-xl font-bold text-white">StudyAgent</h4>
          <p class="text-slate-400 mt-1">智能学习效率分析 AI Agent</p>
          <p class="text-sm text-slate-500 mt-3">
            基于大语言模型的学习计划管理与效率分析智能助手。
            帮助你记录学习、分析模式、生成计划、提供建议。
          </p>
          <div class="flex gap-4 mt-4">
            <a 
              href="https://github.com/xierryi/plan_agent" 
              target="_blank"
              class="text-primary-400 hover:text-primary-300 text-sm"
            >
              GitHub →
            </a>
            <span class="text-slate-600">|</span>
            <span class="text-slate-500 text-sm">Vue 版本 v2.0.0</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
