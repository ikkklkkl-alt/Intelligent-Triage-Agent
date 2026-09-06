<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getDashboardStatsApi, type DashboardStats } from '@/api/modules/admin'
import StatsChart from '@/components/StatsChart.vue'
import { ElMessage } from 'element-plus'

const stats = ref<DashboardStats | null>(null)
const loading = ref(false)

async function fetchStats() {
  loading.value = true
  try {
    stats.value = await getDashboardStatsApi()
  } catch {
    ElMessage.error('获取统计数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchStats)
</script>

<template>
  <div v-loading="loading">
    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center">
            <div style="font-size: 32px; font-weight: 700; color: #409eff">{{ stats?.total_calls ?? '-' }}</div>
            <div style="color: #909399; margin-top: 8px">AI 调用总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center">
            <div style="font-size: 32px; font-weight: 700; color: #67c23a">{{ stats?.ok_calls ?? '-' }}</div>
            <div style="color: #909399; margin-top: 8px">成功调用</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center">
            <div style="font-size: 32px; font-weight: 700; color: #e6a23c">{{ stats?.fallback_calls ?? '-' }}</div>
            <div style="color: #909399; margin-top: 8px">降级调用</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center">
            <div style="font-size: 32px; font-weight: 700; color: #f56c6c">{{ stats?.error_calls ?? '-' }}</div>
            <div style="color: #909399; margin-top: 8px">失败调用</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card><p>今日调用：{{ stats?.today_calls ?? '-' }}</p><p>总 Token：{{ stats?.total_tokens ?? '-' }}</p><p>平均响应：{{ stats?.avg_latency_ms ?? '-' }} ms</p></el-card>
  </div>
</template>
