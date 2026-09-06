<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore, type UserRole } from '@/stores/user'
import { getProfileApi, loginApi } from '@/api/modules/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const roleDefaultPages: Record<UserRole, string> = {
  patient: '/patient/triage',
  doctor: '/doctor/worklist',
  lab: '/lab/orders',
  cashier: '/billing/pending',
  pharmacist: '/pharmacy/pending',
  admin: '/admin/stats'
}

async function handleLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await loginApi({ username: form.username, password: form.password })
    userStore.setToken(res.access_token)
    const profile = await getProfileApi()
    userStore.setUserInfo({
      id: profile.id,
      username: profile.username,
      name: profile.full_name,
      role: profile.role as UserRole
    })
    userStore.persist()
    ElMessage.success('登录成功')
    const defaultPage = roleDefaultPages[profile.role as UserRole] || '/'
    router.push(defaultPage)
  } catch (err: unknown) {
    const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '登录失败，请检查用户名和密码'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div style="min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
    <el-card style="width: 400px; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.15)">
      <template #header>
        <div style="text-align: center">
          <h2 style="margin: 0; color: #303133; font-size: 24px">IMCS 智能医疗系统</h2>
          <p style="color: #909399; margin-top: 8px; font-size: 14px">智能预约诊疗服务平台</p>
        </div>
      </template>
      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" size="large" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div style="text-align: center; color: #909399; font-size: 12px; margin-top: 8px">
        <p>演示账号：patient01 / doctor01 / lab01 / cashier01 / pharmacist01 / admin</p>
        <p>密码：123456</p>
      </div>
    </el-card>
  </div>
</template>
