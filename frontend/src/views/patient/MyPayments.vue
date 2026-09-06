<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getMyPaymentsApi, type BillingItem } from '@/api/modules/billing'
import { ElMessage } from 'element-plus'

const payments = ref<BillingItem[]>([])
const loading = ref(false)
const activeTab = ref('pending')

const pendingPayments = computed(() => payments.value.filter(p => p.status === 'pending'))
const paidPayments = computed(() => payments.value.filter(p => p.status === 'paid'))

async function fetchPayments() {
  loading.value = true
  try {
    payments.value = await getMyPaymentsApi()
  } catch {
    ElMessage.error('获取缴费记录失败')
  } finally {
    loading.value = false
  }
}

function statusLabel(status: string) {
  const map: Record<string, string> = { pending: '待缴费', paid: '已缴费', cancelled: '已取消' }
  return map[status] || status
}

function statusType(status: string) {
  const map: Record<string, string> = { pending: 'warning', paid: 'success', cancelled: 'info' }
  return map[status] || status
}

function kindLabel(kind: string) {
  const map: Record<string, string> = { prescription: '处方缴费', lab: '检验缴费' }
  return map[kind] || kind
}

onMounted(fetchPayments)
</script>

<template>
  <div style="background: #fff; border-radius: 8px; padding: 20px">
    <h3 style="margin-bottom: 16px">缴费记录</h3>
    <el-alert v-if="pendingPayments.length > 0" :title="`您有 ${pendingPayments.length} 项待缴费，请到收费窗口完成缴费后，检验/取药流程才会开始`" type="warning" :closable="false" style="margin-bottom: 16px" />

    <el-tabs v-model="activeTab">
      <el-tab-pane :label="`待缴费 (${pendingPayments.length})`" name="pending">
        <el-table :data="pendingPayments" v-loading="loading" stripe>
          <el-table-column label="项目" min-width="150"><template #default="{ row }">{{ kindLabel(row.kind) }}</template></el-table-column>
          <el-table-column label="金额" width="120">
            <template #default="{ row }"><span style="color: #f56c6c; font-weight: 600">&yen;{{ Number(row.amount).toFixed(2) }}</span></template>
          </el-table-column>
          <el-table-column prop="created_at" label="日期" width="180" />
          <el-table-column label="操作" width="160">
            <template #default><el-tag type="warning" size="small">请到收费窗口缴费</el-tag></template>
          </el-table-column>
        </el-table>
        <div v-if="pendingPayments.length === 0 && !loading" style="text-align: center; padding: 40px; color: #909399">暂无待缴费项目</div>
      </el-tab-pane>

      <el-tab-pane :label="`已缴费 (${paidPayments.length})`" name="paid">
        <el-table :data="paidPayments" v-loading="loading" stripe>
          <el-table-column label="项目" min-width="150"><template #default="{ row }">{{ kindLabel(row.kind) }}</template></el-table-column>
          <el-table-column label="金额" width="120">
            <template #default="{ row }"><span>&yen;{{ Number(row.amount).toFixed(2) }}</span></template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }"><el-tag :type="statusType(row.status) as any">{{ statusLabel(row.status) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="created_at" label="日期" width="180" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
