<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getLlmLogsApi, type LlmLog } from '@/api/modules/admin'
import { ElMessage } from 'element-plus'

const logs = ref<LlmLog[]>([])
const loading = ref(false)
const filterType = ref('')

async function fetchLogs() {
  loading.value = true
  try {
    logs.value = await getLlmLogsApi({ limit: 100, scene: filterType.value || undefined })
  } catch {
    ElMessage.error('获取LLM日志失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchLogs)
</script>

<template>
  <div style="background: #fff; border-radius: 8px; padding: 20px">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px">
      <div style="display: flex; gap: 12px; align-items: center">
        <h3>LLM 调用日志</h3>
        <el-select v-model="filterType" placeholder="请求类型" clearable style="width: 150px" @change="fetchLogs">
          <el-option label="分诊" value="triage" />
          <el-option label="报告解读" value="report_interpretation" />
          <el-option label="知识库问答" value="kb_qa" />
        </el-select>
      </div>
      <el-button type="primary" @click="fetchLogs">刷新</el-button>
    </div>

    <el-table :data="logs" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="scene" label="类型" width="150" />
      <el-table-column label="Token数" width="120"><template #default="{ row }">{{ row.prompt_tokens + row.completion_tokens }}</template></el-table-column>
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column label="耗时" width="100">
        <template #default="{ row }">{{ row.latency_ms }}ms</template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="180" />
    </el-table>

  </div>
</template>
