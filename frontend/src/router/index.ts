import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'prompt-management',
      component: () => import('../views/PromptManagementView.vue'),
      meta: { menu: 'prompt', title: 'Prompt 管理' }
    },
    {
      path: '/prompts/:id',
      name: 'prompt-detail',
      component: () => import('../views/PromptDetailView.vue'),
      meta: { menu: 'prompt', title: 'Prompt 详情' }
    },
    {
      path: '/classes',
      name: 'class-management',
      component: () => import('../views/PromptClassManagementView.vue'),
      meta: { menu: 'class', title: '分类管理' }
    },
    {
      path: '/tags',
      name: 'tag-management',
      component: () => import('../views/PromptTagManagementView.vue'),
      meta: { menu: 'tag', title: '标签管理' }
    },
    {
      path: '/llms',
      name: 'llm-management',
      component: () => import('../views/LLMManagementView.vue'),
      meta: { menu: 'llm', title: 'LLMs 管理' }
    },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

export default router
