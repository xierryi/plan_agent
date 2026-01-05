<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStudyStore } from '../stores/study'

const route = useRoute()
const router = useRouter()
const studyStore = useStudyStore()

const navItems = [
  { path: '/', icon: '📊', label: '看板' },
  { path: '/today', icon: '📝', label: '记录' },
  { path: '/ai-assistant', icon: '🤖', label: 'AI' },
  { path: '/history', icon: '📚', label: '历史' },
  { path: '/settings', icon: '⚙️', label: '设置' }
]

const isActive = (path) => {
  return route.path === path
}

const currentDateFormatted = computed(() => {
  const date = new Date(studyStore.currentDate)
  return date.toLocaleDateString('zh-CN', { 
    month: 'long', 
    day: 'numeric',
    weekday: 'short'
  })
})
</script>

<template>
  <!-- 桌面端侧边栏 -->
  <aside class="hidden lg:flex fixed left-0 top-0 h-screen w-64 bg-slate-900/80 backdrop-blur-xl border-r border-slate-800 flex-col z-50">
    <!-- Logo -->
    <div class="p-6 border-b border-slate-800">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-xl">
          📚
        </div>
        <div>
          <h1 class="font-display font-bold text-lg text-white">StudyAgent</h1>
          <p class="text-xs text-slate-500">智能学习助手</p>
        </div>
      </div>
    </div>

    <!-- 日期显示 -->
    <div class="px-6 py-4 border-b border-slate-800">
      <div class="text-sm text-slate-500">当前日期</div>
      <div class="text-lg font-medium text-white">{{ currentDateFormatted }}</div>
    </div>

    <!-- 导航菜单 -->
    <nav class="flex-1 p-4 space-y-2">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        :class="[
          'nav-item',
          isActive(item.path) ? 'active' : ''
        ]"
      >
        <span class="text-xl">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- 底部状态 -->
    <div class="p-4 border-t border-slate-800">
      <div class="card-hover p-4 cursor-pointer" @click="router.push('/settings')">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
            <span class="text-emerald-400">✓</span>
          </div>
          <div>
            <div class="text-sm font-medium text-white">已连接</div>
            <div class="text-xs text-slate-500">GitHub 同步</div>
          </div>
        </div>
      </div>
    </div>
  </aside>

  <!-- 移动端底部导航 -->
  <nav class="lg:hidden fixed bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur-xl border-t border-slate-800 z-50 safe-area-bottom">
    <div class="flex justify-around items-center h-16">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        :class="[
          'flex flex-col items-center justify-center px-3 py-2 rounded-lg transition-all',
          isActive(item.path) 
            ? 'text-primary-400 bg-primary-500/10' 
            : 'text-slate-500 hover:text-slate-300'
        ]"
      >
        <span class="text-xl">{{ item.icon }}</span>
        <span class="text-xs mt-1">{{ item.label }}</span>
      </router-link>
    </div>
  </nav>
</template>

<style scoped>
.safe-area-bottom {
  padding-bottom: env(safe-area-inset-bottom, 0);
}
</style>

