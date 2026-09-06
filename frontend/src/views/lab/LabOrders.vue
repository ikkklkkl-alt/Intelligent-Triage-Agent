<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getLabOrdersApi, submitLabResultApi, getLabReportApi, type LabOrderItem, type LabReport } from '@/api/modules/lab'
import ReportViewer from '@/components/ReportViewer.vue'
import { ElMessage } from 'element-plus'

const orders = ref<LabOrderItem[]>([])
const loading = ref(false)
const selectedOrder = ref<LabOrderItem | null>(null)
const resultText = ref('')
const showResultDialog = ref(false)
const showReportDialog = ref(false)
const reportData = ref<LabReport | null>(null)

async function fetchOrders() {
  loading.value = true
  try {
    orders.value = await getLabOrdersApi()
  } catch {
    ElMessage.error('获取检验工单失败')
  } finally {
    loading.value = false
  }
}

function openResultDialog(order: LabOrderItem) {
  selectedOrder.value = order
  resultText.value = ''
  showResultDialog.value = true
}

async function handleSubmitResult() {
  if (!selectedOrder.value || !resultText.value.trim()) {
    ElMessage.warning('请输入检验结果')
    return
  }
  try {
    await submitLabResultApi(selectedOrder.value.id, { raw_text: resultText.value })
    ElMessage.success('结果已提交，AI解读中...')
    showResultDialog.value = false
    fetchOrders()
  } catch {
    ElMessage.error('提交失败')
  }
}

function statusLabel(status: string) {
  const map: Record<string, string> = { pending_payment: '待缴费', paid: '待检验', reported: '已出报告' }
  return map[status] || status
}

onMounted(fetchOrders)
</script>

<template>
  <div style="background: #fff; border-radius: 8px; padding: 20px">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
      <h3>检验工单</h3>
      <el-button type="primary" @click="fetchOrders">刷新</el-button>
    </div>
    <el-table :data="orders" v-loading="loading" stripe>
      <el-table-column prop="patient_name" label="患者" width="120" />
      <el-table-column prop="item_name" label="检验项目" width="180" />
      <el-table-column label="费用"><template #default="{ row }">¥{{ Number(row.fee).toFixed(2) }}</template></el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag>{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button v-if="row.status === 'paid'" type="primary" size="small" @click="openResultDialog(row)">录入结果</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showResultDialog" title="录入检验结果" width="500px">
      <p style="margin-bottom: 12px"><strong>项目：</strong>{{ selectedOrder?.item_name }}</p>
      <el-input v-model="resultText" type="textarea" :rows="6" placeholder="请输入检验结果文本..." />
      <template #footer>
        <el-button @click="showResultDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitResult">提交（触发AI解读）</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showReportDialog" title="AI 报告解读" width="600px">
      <ReportViewer v-if="reportData" :report="reportData" />
    </el-dialog>
  </div>
</template>
