<template>
  <el-config-provider :locale="locale">
    <div class="app-shell">
      <el-container class="app-container">
        <el-header class="app-header" height="64px">
          <div class="header-left">
            <span class="app-title">PromptWorks 控制台</span>
          </div>
          <div class="header-right">
            <el-button type="primary" :icon="Setting" text>设置</el-button>
            <el-select v-model="language" size="small" class="language-select">
              <el-option label="中文" value="zh-CN" />
              <el-option label="English" value="en-US" />
            </el-select>
            <el-switch
              v-model="isDark"
              inline-prompt
              :active-icon="Moon"
              :inactive-icon="Sunny"
              active-color="#303133"
              inactive-color="#409EFF"
            />
          </div>
        </el-header>
        <el-container>
          <el-aside width="220px" class="side-nav">
            <el-menu class="side-menu" :default-active="activeMenu" @select="handleMenuSelect">
              <el-menu-item
                v-for="item in menuItems"
                :key="item.index"
                :index="item.index"
              >
                <el-icon>
                  <component :is="item.icon" />
                </el-icon>
                <span>{{ item.label }}</span>
              </el-menu-item>
            </el-menu>
          </el-aside>
          <el-main class="main-view">
            <router-view />
          </el-main>
        </el-container>
      </el-container>
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Setting, Collection, Cpu, Sunny, Moon } from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import enUs from 'element-plus/es/locale/lang/en'

interface MenuItem {
  index: string
  label: string
  routeName: string
  icon: Component
}

const router = useRouter()
const route = useRoute()

const language = ref<'zh-CN' | 'en-US'>('zh-CN')
const locale = computed(() => (language.value === 'zh-CN' ? zhCn : enUs))
const isDark = ref(false)

const menuItems: MenuItem[] = [
  { index: 'prompt', label: 'Prompt 管理', routeName: 'prompt-management', icon: Collection },
  { index: 'llm', label: 'LLMs 管理', routeName: 'llm-management', icon: Cpu }
]

const activeMenu = computed(() => (route.meta.menu as string | undefined) ?? 'prompt')

watch(isDark, (value) => toggleTheme(value), { immediate: true })

function toggleTheme(value: boolean) {
  const root = document.documentElement
  if (value) {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

function handleMenuSelect(index: string) {
  const target = menuItems.find((item) => item.index === index)
  if (target) {
    router.push({ name: target.routeName })
  }
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--app-bg-color);
}

.app-container {
  min-height: 100vh;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: var(--header-bg-color);
  color: var(--header-text-color);
  box-shadow: 0 1px 4px rgb(0 0 0 / 10%);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-title {
  font-size: 20px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.language-select {
  width: 120px;
}

.side-nav {
  background: var(--side-bg-color);
  border-right: 1px solid var(--side-border-color);
}

.side-menu {
  border-right: none;
}

.main-view {
  padding: 24px;
  background: var(--content-bg-color);
}
</style>
