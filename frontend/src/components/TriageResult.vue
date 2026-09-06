<script setup lang="ts">
import { computed } from 'vue'
import type { TriageResult } from '@/api/modules/triage'

const props = defineProps<{
  result: TriageResult
}>()

const emit = defineEmits<{
  goBooking: []
}>()

const urgencyConfig = computed(() => {
  const map: Record<string, { color: string; bgColor: string; label: string }> = {
    emergency: { color: '#fff', bgColor: '#f56c6c', label: '紧急' },
    high: { color: '#fff', bgColor: '#e6a23c', label: '高' },
    medium: { color: '#fff', bgColor: '#409eff', label: '中' },
    low: { color: '#fff', bgColor: '#67c23a', label: '低' }
  }
  return map[props.result.urgency] || map.medium
})
</script>

<template>
  <div style="display: flex; justify-content: flex-start; margin-top: 8px">
    <el-card shadow="hover" style="max-width: 70%; border-left: 4px solid #409eff; border-radius: 12px">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span style="font-weight: 600; font-size: 16px">分诊结论</span>
          <el-tag
            :style="{ backgroundColor: urgencyConfig.bgColor, color: urgencyConfig.color, border: 'none' }"
            size="large"
          >
            紧急程度：{{ urgencyConfig.label }}
          </el-tag>
        </div>
      </template>
      <div style="display: flex; flex-direction: column; gap: 12px">
        <div>
          <span style="color: #909399; font-size: 13px">推荐科室</span>
          <div style="font-size: 18px; font-weight: 600; color: #303133; margin-top: 4px">{{ result.department }}</div>
        </div>
        <div>
          <span style="color: #909399; font-size: 13px">就医建议</span>
          <div style="margin-top: 4px; line-height: 1.6; color: #606266">{{ result.advice }}</div>
        </div>
        <el-tag v-if="result.degraded" type="warning" effect="plain">已启用规则分诊</el-tag>
        <el-button v-if="result.department !== '未分诊'" type="primary" size="large" style="margin-top: 8px; width: 200px" @click="emit('goBooking')">
          去挂号
        </el-button>
        <el-alert v-else title="请描述您的症状以获取科室推荐" type="info" :closable="false" style="margin-top: 8px" />
      </div>
    </el-card>
  </div>
</template>
