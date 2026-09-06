<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getPendingPrescriptionsApi, dispensePrescriptionApi, type PharmacyItem } from '@/api/modules/pharmacy'
import { ElMessage, ElMessageBox } from 'element-plus'

const items = ref<PharmacyItem[]>([])
const loading = ref(false)

async function fetchPending() {
  loading.value = true
  try {
    items.value = await getPendingPrescriptionsApi()
  } catch {
    ElMessage.error('获取待发药列表失败')
  } finally {
    loading.value = false
  }
}

async function handleDispense(item: PharmacyItem) {
  try {
    await ElMessageBox.confirm(`确认发药：${item.items.map(i => i.drug_name).join('、')}？`, '确认发药', { type: 'warning' })
    await dispensePrescriptionApi(item.id)
    ElMessage.success('发药成功')
    fetchPending()
  } catch {
    // user cancelled or error
  }
}

onMounted(fetchPending)
</script>

<template>
  <div style="background: #fff; border-radius: 8px; padding: 20px">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
      <h3>待发药列表</h3>
      <el-button type="primary" @click="fetchPending">刷新</el-button>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="patient_name" label="患者" width="120" />
      <el-table-column label="药品"><template #default="{ row }">{{ row.items.map((i: any) => `${i.drug_name} × ${i.quantity}`).join('；') }}</template></el-table-column>
      <el-table-column label="金额" width="100"><template #default="{ row }">¥{{ Number(row.total_fee).toFixed(2) }}</template></el-table-column>
      <el-table-column prop="created_at" label="日期" width="180" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button type="success" size="small" @click="handleDispense(row)">确认发药</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
