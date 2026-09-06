<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getMyAppointmentsApi, type Appointment } from '@/api/modules/appointments'
import { getMyPaymentsApi, type BillingItem } from '@/api/modules/billing'
import { getMyReportsApi, type LabReport } from '@/api/modules/lab'

const router = useRouter()
const pendingPayments = ref<BillingItem[]>([])
const recentAppointments = ref<Appointment[]>([])
const recentReports = ref<LabReport[]>([])

const steps = [
  { title: '智能分诊', desc: '描述症状，AI 推荐科室', icon: 'ChatDotRound', route: '/patient/triage' },
  { title: '预约挂号', desc: '选择医生和时段', icon: 'Calendar', route: '/patient/book' },
  { title: '到院就诊', desc: '按预约时间到诊室等候', icon: 'OfficeBuilding', route: '' },
  { title: '缴费', desc: '检验/处方费用在收费窗口缴纳', icon: 'Wallet', route: '/patient/payments' },
  { title: '检验取药', desc: '缴费后到检验科/药房', icon: 'FirstAidKit', route: '' },
  { title: '查看报告', desc: '检验报告含 AI 解读', icon: 'Document', route: '/patient/reports' },
]

async function fetchData() {
  try {
    const [appts, pays, reps] = await Promise.all([getMyAppointmentsApi(), getMyPaymentsApi(), getMyReportsApi()])
    recentAppointments.value = appts.filter(a => a.status === 'booked')
    pendingPayments.value = pays.filter(p => p.status === 'pending')
    recentReports.value = reps.slice(0, 3)
  } catch { /* ignore */ }
}

function urgencyType(u: string) {
  return { emergency: 'danger', high: 'warning', medium: '', low: 'success' }[u] || ''
}

onMounted(fetchData)
</script>

<template>
  <div style="display: flex; flex-direction: column; gap: 20px">
    <!-- 就诊流程 -->
    <div style="background: #fff; border-radius: 8px; padding: 24px">
      <h3 style="margin-bottom: 20px">就诊流程指引</h3>
      <div style="display: flex; gap: 0; align-items: flex-start; overflow-x: auto">
        <div v-for="(step, i) in steps" :key="i" style="display: flex; align-items: center; min-width: 140px">
          <div style="display: flex; flex-direction: column; align-items: center; gap: 8px; cursor: pointer" @click="step.route && router.push(step.route)">
            <div style="width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 600">{{ i + 1 }}</div>
            <div style="font-weight: 600; font-size: 14px; color: #303133">{{ step.title }}</div>
            <div style="font-size: 12px; color: #909399; text-align: center; max-width: 120px">{{ step.desc }}</div>
          </div>
          <div v-if="i < steps.length - 1" style="flex: 1; height: 2px; background: #dcdfe6; min-width: 24px; margin: 0 4px; margin-top: -30px" />
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px">
      <!-- 待缴费提醒 -->
      <div style="background: #fff; border-radius: 8px; padding: 20px">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px">
          <h4 style="margin: 0">待缴费</h4>
          <el-button v-if="pendingPayments.length" type="primary" link size="small" @click="router.push('/patient/payments')">查看全部</el-button>
        </div>
        <div v-if="pendingPayments.length === 0" style="color: #909399; font-size: 13px">暂无待缴费项目</div>
        <div v-for="p in pendingPayments" :key="p.id" style="padding: 8px 0; border-bottom: 1px solid #f0f0f0">
          <div style="display: flex; justify-content: space-between">
            <span>{{ p.kind === 'prescription' ? '处方缴费' : '检验缴费' }}</span>
            <span style="color: #f56c6c; font-weight: 600">¥{{ Number(p.amount).toFixed(2) }}</span>
          </div>
          <div style="font-size: 12px; color: #e6a23c; margin-top: 4px">请到收费窗口完成缴费</div>
        </div>
      </div>

      <!-- 近期预约 -->
      <div style="background: #fff; border-radius: 8px; padding: 20px">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px">
          <h4 style="margin: 0">待就诊</h4>
          <el-button type="primary" link size="small" @click="router.push('/patient/book')">去预约</el-button>
        </div>
        <div v-if="recentAppointments.length === 0" style="color: #909399; font-size: 13px">暂无预约</div>
        <div v-for="a in recentAppointments" :key="a.id" style="padding: 8px 0; border-bottom: 1px solid #f0f0f0">
          <div style="font-weight: 500">{{ a.doctor_name }} · {{ a.department_name }}</div>
          <div style="font-size: 12px; color: #909399; margin-top: 4px">{{ a.work_date }} {{ a.slot === 'am' ? '上午' : '下午' }}</div>
        </div>
      </div>

      <!-- 近期报告 -->
      <div style="background: #fff; border-radius: 8px; padding: 20px">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px">
          <h4 style="margin: 0">检验报告</h4>
          <el-button type="primary" link size="small" @click="router.push('/patient/reports')">查看全部</el-button>
        </div>
        <div v-if="recentReports.length === 0" style="color: #909399; font-size: 13px">暂无报告</div>
        <div v-for="r in recentReports" :key="r.id" style="padding: 8px 0; border-bottom: 1px solid #f0f0f0">
          <div style="font-weight: 500">{{ r.item_name || '检验报告' }}</div>
          <div style="font-size: 12px; margin-top: 4px">
            <el-tag v-if="r.ai_status === 'pending'" size="small" type="warning">AI 解读中...</el-tag>
            <span v-else style="color: #67c23a">已生成</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
