<script setup lang="ts">
import type { LabReport } from '@/api/modules/lab'

defineProps<{
  report: LabReport
}>()
</script>

<template>
  <div style="display: flex; flex-direction: column; gap: 16px">
    <el-card shadow="never">
      <template #header><span style="font-weight: 600">AI 摘要</span></template>
      <p style="line-height: 1.8; color: #303133">{{ report.ai_summary }}</p>
    </el-card>

    <el-card shadow="never">
      <template #header><span style="font-weight: 600; color: #409eff">原始报告</span></template>
      <p style="line-height: 1.8; color: #303133; white-space: pre-wrap">{{ report.raw_text }}</p>
    </el-card>
    <el-alert v-if="report.ai_degraded" title="AI 服务暂不可用，已返回规则摘要" type="warning" :closable="false" />
  </div>
</template>
