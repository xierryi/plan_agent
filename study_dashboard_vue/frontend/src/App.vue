<script setup>
import { RouterView, useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
</script>

<template>
  <div class="min-h-screen bg-slate-950">
    <!-- 侧边栏 -->
    <Sidebar />
    
    <!-- 主内容区 -->
    <main class="lg:ml-64 p-4 lg:p-8 pb-24 lg:pb-8">
      <div class="max-w-7xl mx-auto">
        <RouterView v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </RouterView>
      </div>
    </main>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
