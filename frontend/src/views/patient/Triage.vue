<script setup lang="ts">
import { ref, reactive, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createTriageSession, sendTriageMessage, getTriageSessionsApi, getTriageMessagesApi, type TriageChatMessage, type TriageResult, type TriageSession } from '@/api/modules/triage'
import ChatMessage from '@/components/ChatMessage.vue'
import TriageResultCard from '@/components/TriageResult.vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const chatContainer = ref<HTMLElement | null>(null)
const userInput = ref('')
const isLoading = ref(false)
const triageResult = ref<TriageResult | null>(null)
const sessionId = ref<number | null>(null)
const historySessions = ref<TriageSession[]>([])
const showHistory = ref(false)

const messages = reactive<TriageChatMessage[]>([
  { role: 'assistant', content: '您好！我是智能分诊助手。请描述您的症状，我会为您推荐合适的科室。' }
])

async function ensureSession() {
  if (sessionId.value) return sessionId.value
  const session = await createTriageSession()
  sessionId.value = session.id
  return session.id
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

async function handleSend() {
  const text = userInput.value.trim()
  if (!text || isLoading.value) return

  messages.push({ role: 'user', content: text })
  userInput.value = ''
  isLoading.value = true
  scrollToBottom()

  const assistantMsg = reactive<TriageChatMessage>({ role: 'assistant', content: '' })
  messages.push(assistantMsg)
  scrollToBottom()

  try {
    const id = await ensureSession()
    const response = await sendTriageMessage(id, text)

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error('No reader')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          if (data === '[DONE]') continue

          try {
            const parsed = JSON.parse(data)
            if (parsed.type === 'delta') assistantMsg.content += parsed.content || ''
            if (parsed.type === 'result' && parsed.result) triageResult.value = parsed.result
            if (parsed.type === 'error') throw new Error(parsed.message || '分诊请求失败')
          } catch {
            assistantMsg.content += data
          }
          scrollToBottom()
        }
      }
    }

  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '网络错误'
    assistantMsg.content = `抱歉，分诊服务暂时不可用：${msg}`
    ElMessage.error('分诊请求失败')
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

function handleGoBooking() {
  if (triageResult.value) {
    router.push({ path: '/patient/book', query: { department: triageResult.value.department } })
  }
}

async function fetchHistory() {
  try {
    historySessions.value = await getTriageSessionsApi()
  } catch { /* ignore */ }
}

async function loadSession(session: TriageSession) {
  try {
    const msgs = await getTriageMessagesApi(session.id)
    messages.length = 0
    msgs.forEach(m => messages.push(m))
    sessionId.value = session.id
    triageResult.value = session.result_json
    showHistory.value = false
    scrollToBottom()
  } catch {
    ElMessage.error('加载历史会话失败')
  }
}

function resetChat() {
  messages.length = 0
  messages.push({ role: 'assistant', content: '您好！我是智能分诊助手。请描述您的症状，我会为您推荐合适的科室。' })
  triageResult.value = null
  sessionId.value = null
}

onMounted(() => {
  fetchHistory()
  scrollToBottom()
})
</script>

<template>
  <div style="height: calc(100vh - 140px); display: flex; flex-direction: column; background: #fff; border-radius: 8px; overflow: hidden">
    <div style="padding: 16px 20px; border-bottom: 1px solid #e8e8e8; display: flex; align-items: center; justify-content: space-between">
      <div style="display: flex; align-items: center; gap: 8px">
        <el-icon style="color: #409eff; font-size: 24px"><ChatDotRound /></el-icon>
        <span style="font-size: 18px; font-weight: 600">智能分诊</span>
      </div>
      <div style="display: flex; gap: 8px">
        <el-button text @click="showHistory = !showHistory">{{ showHistory ? '返回对话' : '历史会话' }}</el-button>
        <el-button text @click="resetChat">新建会话</el-button>
      </div>
    </div>

    <div ref="chatContainer" style="flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px">
      <template v-if="showHistory">
        <div v-if="historySessions.length === 0" style="text-align: center; color: #909399; padding: 40px">暂无历史会话</div>
        <div v-for="s in historySessions" :key="s.id" style="padding: 12px 16px; border: 1px solid #e8e8e8; border-radius: 8px; cursor: pointer" @click="loadSession(s)">
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span style="font-weight: 500">会话 #{{ s.id }}</span>
            <el-tag :type="s.status === 'completed' ? 'success' : 'info'" size="small">{{ s.status === 'completed' ? '已完成' : '进行中' }}</el-tag>
          </div>
          <div style="color: #909399; font-size: 12px; margin-top: 4px">{{ s.created_at }}</div>
          <div v-if="s.result_json" style="color: #409eff; font-size: 13px; margin-top: 4px">推荐科室：{{ s.result_json.department }}</div>
        </div>
      </template>
      <template v-else>
        <ChatMessage v-for="(msg, index) in messages" :key="index" :role="msg.role" :content="msg.content" />
        <TriageResultCard v-if="triageResult" :result="triageResult" @go-booking="handleGoBooking" />
      </template>
    </div>

    <div style="padding: 16px 20px; border-top: 1px solid #e8e8e8; display: flex; gap: 12px; background: #fafafa">
      <el-input
        v-model="userInput"
        placeholder="请描述您的症状..."
        size="large"
        :disabled="isLoading"
        @keyup.enter="handleSend"
      />
      <el-button type="primary" size="large" :loading="isLoading" :disabled="!userInput.trim()" @click="handleSend">
        发送
      </el-button>
    </div>
  </div>
</template>
