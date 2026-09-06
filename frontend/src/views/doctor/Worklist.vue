<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getWorklistApi, startEncounterApi, type WorklistAppointment } from '@/api/modules/encounters'
import { ElMessage } from 'element-plus'

const router = useRouter()
const encounters = ref<WorklistAppointment[]>([])
const loading = ref(false)

async function fetchWorklist() {
  loading.value = true
  try {
    encounters.value = await getWorklistApi()
  } catch {
    ElMessage.error('获取待接诊列表失败')
  } finally {
    loading.value = false
  }
}

async function handleStart(encounter: WorklistAppointment) {
  try {
    const created = await startEncounterApi(encounter.id)
    ElMessage.success('已开始接诊')
    router.push(`/doctor/encounter/${created.id}`)
  } catch {
    ElMessage.error('操作失败')
  }
}

function statusLabel(status: string) {
  const map: Record<string, string> = { booked: '待接诊', completed: '已完成' }
  return map[status] || status
}

function statusType(status: string) {
  const map: Record<string, string> = { booked: 'warning', completed: 'info' }
  return map[status] || 'info'
}

onMounted(fetchWorklist)
</script>

<template>
  <div style="background: #fff; border-radius: 8px; padding: 20px">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
      <h3>今日待接诊</h3>
      <el-button type="primary" @click="fetchWorklist">刷新</el-button>
    </div>
    <el-table :data="encounters" v-loading="loading" stripe>
      <el-table-column prop="patient_name" label="患者" width="120" />
      <el-table-column prop="department_name" label="科室" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status) as any">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="到达时间" width="180" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button v-if="row.status === 'booked'" type="primary" size="small" @click="handleStart(row)">接诊</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
