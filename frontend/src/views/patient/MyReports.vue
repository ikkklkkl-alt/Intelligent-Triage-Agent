<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getMyReportsApi, type LabReport } from '@/api/modules/lab'
import ReportViewer from '@/components/ReportViewer.vue'
import { ElMessage } from 'element-plus'

const reports = ref<LabReport[]>([])
const loading = ref(false)
const selectedReport = ref<LabReport | null>(null)
const showReportDialog = ref(false)

async function fetchReports() {
  loading.value = true
  try {
    reports.value = await getMyReportsApi()
  } catch {
    ElMessage.error('获取报告列表失败')
  } finally {
    loading.value = false
  }
}

function viewReport(item: LabReport) {
  selectedReport.value = item
  showReportDialog.value = true
}

function statusTag(status: string) {
  if (status === 'pending') return { text: 'AI 解读中...', type: 'warning' as const }
  if (status === 'done') return { text: '已解读', type: 'success' as const }
  if (status === 'failed') return { text: '解读失败', type: 'danger' as const }
  return { text: status, type: 'info' as const }
}

onMounted(fetchReports)
</script>

<template>
  <div style="background: #fff; border-radius: 8px; padding: 20px">
    <h3 style="margin-bottom: 8px">我的报告</h3>
    <p style="color: #909399; font-size: 13px; margin-bottom: 16px">检验报告由检验师提交后，系统自动进行 AI 解读。解读完成后可查看详情。</p>

    <el-table :data="reports" v-loading="loading" stripe>
      <el-table-column prop="item_name" label="检验项目" min-width="150" />
      <el-table-column label="AI 解读状态" width="140">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.ai_status).type" size="small">{{ statusTag(row.ai_status).text }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="日期" width="180" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button v-if="row.ai_status !== 'pending'" type="primary" size="small" link @click="viewReport(row)">查看详情</el-button>
          <span v-else style="color: #909399; font-size: 12px">请稍候...</span>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showReportDialog" title="检验报告详情" width="600px">
      <ReportViewer v-if="selectedReport" :report="selectedReport" />
    </el-dialog>
  </div>
</template>
