<script setup lang="ts">
defineProps<{
  role: 'user' | 'assistant'
  content: string
}>()
</script>

<template>
  <div :style="{ display: 'flex', justifyContent: role === 'user' ? 'flex-end' : 'flex-start' }">
    <div
      :style="{
        maxWidth: '70%',
        padding: '12px 16px',
        borderRadius: role === 'user' ? '12px 12px 0 12px' : '12px 12px 12px 0',
        backgroundColor: role === 'user' ? '#409eff' : '#f4f4f5',
        color: role === 'user' ? '#fff' : '#303133',
        lineHeight: '1.6',
        fontSize: '14px',
        wordBreak: 'break-word'
      }"
    >
      <span class="message-content">{{ content }}</span>
    </div>
  </div>
</template>

<style scoped>
.message-content {
  white-space: pre-wrap;
}
</style>
