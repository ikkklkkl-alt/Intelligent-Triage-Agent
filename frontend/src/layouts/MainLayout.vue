<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const isCollapse = ref(false)

const menuItems = computed(() => {
  const role = userStore.userRole
  switch (role) {
    case 'patient':
      return [
        { index: '/patient/guide', icon: 'HomeFilled', label: '就诊指南' },
        { index: '/patient/triage', icon: 'ChatDotRound', label: '智能分诊' },
        { index: '/patient/book', icon: 'Calendar', label: '预约挂号' },
        { index: '/patient/payments', icon: 'Wallet', label: '缴费记录' },
        { index: '/patient/reports', icon: 'Document', label: '我的报告' }
      ]
    case 'doctor':
      return [
        { index: '/doctor/worklist', icon: 'List', label: '今日待接诊' }
      ]
    case 'lab':
      return [
        { index: '/lab/orders', icon: 'Microscope', label: '检验工单' }
      ]
    case 'cashier':
      return [
        { index: '/billing/pending', icon: 'Money', label: '待收费列表' }
      ]
    case 'pharmacist':
      return [
        { index: '/pharmacy/pending', icon: 'Box', label: '待发药列表' }
      ]
    case 'admin':
      return [
        { index: '/admin/stats', icon: 'DataAnalysis', label: 'AI监控看板' },
        { index: '/admin/kb', icon: 'Collection', label: '知识库管理' },
        { index: '/admin/llm-logs', icon: 'Tickets', label: 'LLM日志' }
      ]
    default:
      return []
  }
})

const roleNameMap: Record<string, string> = {
  patient: '患者',
  doctor: '医生',
  lab: '检验员',
  cashier: '收费员',
  pharmacist: '药剂师',
  admin: '管理员'
}

function handleMenuSelect(index: string) {
  router.push(index)
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <el-container style="height: 100vh">
    <el-aside :width="isCollapse ? '64px' : '220px'" style="transition: width 0.3s; background-color: #001529">
      <div style="height: 60px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 18px; font-weight: bold; white-space: nowrap; overflow: hidden">
        <span v-if="!isCollapse">IMCS 智能医疗</span>
        <span v-else>IM</span>
      </div>
      <el-menu
        :default-active="$route.path"
        :collapse="isCollapse"
        background-color="#001529"
        text-color="#ffffffb3"
        active-text-color="#409eff"
        @select="handleMenuSelect"
      >
        <el-menu-item v-for="item in menuItems" :key="item.index" :index="item.index">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.label }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e8e8e8; background: #fff; padding: 0 20px">
        <el-icon style="cursor: pointer; font-size: 20px" @click="isCollapse = !isCollapse">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
        <div style="display: flex; align-items: center; gap: 12px">
          <span style="color: #666">{{ roleNameMap[userStore.userInfo?.role || ''] || '' }}</span>
          <span style="font-weight: 600">{{ userStore.userInfo?.name }}</span>
          <el-button type="danger" link @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main style="background: #f0f2f5; padding: 20px">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
