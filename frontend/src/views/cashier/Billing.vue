<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getPendingBillingApi, confirmPaymentApi, type BillingItem } from '@/api/modules/billing'
import { ElMessage, ElMessageBox } from 'element-plus'

const items = ref<BillingItem[]>([])
const loading = ref(false)

async function fetchPending() {
  loading.value = true
  try {
    items.value = await getPendingBillingApi()
  } catch {
    ElMessage.error('获取待收费列表失败')
  } finally {
    loading.value = false
  }
}

async function handleConfirm(item: BillingItem) {
  try {
    await ElMessageBox.confirm(`确认收费 ¥${Number(item.amount).toFixed(2)}？`, '确认收费', { type: 'warning' })
    await confirmPaymentApi(item.id)
    ElMessage.success('收费成功')
    fetchPending()
  } catch {
    // user cancelled or error
  }
}

function typeLabel(type: string) {
  const map: Record<string, string> = { prescription: '处方', lab: '检验' }
  return map[type] || type
}

onMounted(fetchPending)
</script>

<template>
  <div style="background: #fff; border-radius: 8px; padding: 20px">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
      <h3>待收费列表</h3>
      <el-button type="primary" @click="fetchPending">刷新</el-button>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="patient_name" label="患者" width="120" />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">{{ typeLabel(row.kind) }}</template>
      </el-table-column>
      <el-table-column label="项目"><template #default="{ row }">{{ row.kind === 'prescription' ? '处方缴费' : '检验缴费' }}</template></el-table-column>
      <el-table-column label="金额" width="120">
        <template #default="{ row }">
          <span style="color: #f56c6c; font-weight: 600">&yen;{{ Number(row.amount).toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="日期" width="180" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button type="success" size="small" @click="handleConfirm(row)">确认收费</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
