<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">数据分析仪表盘</h1>
      <p class="page-description">统一筛选、卡片概览、联动趋势与AI洞察</p>
    </div>

    <!-- 筛选栏组件 -->
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>筛选条件</span>
          <div class="header-actions">
            <el-button :loading="loading" @click="refreshSummary">刷新</el-button>
          </div>
        </div>
      </template>
      <FilterBar v-model="filterParams" />
    </el-card>

    <!-- 卡片网格组件 -->
    <CardGrid
      :summaryData="summaryData"
      :activeMetricKey="activeMetricKey"
      :visibleKeys="visibleKeys"
      @cardClick="onCardClick"
      @aiClick="onAIClick"
    />

    <!-- 趋势模块组件 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>趋势分析</span>
          <div class="header-actions">
            <el-tag v-if="activeMetricKey" type="primary" size="small">指标：{{ activeMetricKey }}</el-tag>
          </div>
        </div>
      </template>
      <TrendChartModule :metricKey="activeMetricKey" :filterParams="filterParams" />
    </el-card>

    <!-- 排行榜（置于趋势分析下方，联动指标与筛选） -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>排行榜</span>
          <div class="header-actions">
            <el-tag v-if="activeMetricKey" type="primary" size="small">指标：{{ metricDict[activeMetricKey]?.name || activeMetricKey }}</el-tag>
          </div>
        </div>
      </template>
      <RankingList :metricKey="activeMetricKey" :filterParams="filterParams" />
    </el-card>

    <!-- 团队绩效表（管理员/超管可见） -->
    <AdminTeamPerformance
      v-if="authStore.isAdmin || authStore.isSuperAdmin"
      :filterParams="filterParams"
    />

    <!-- AI洞察弹窗 -->
    <el-dialog v-model="aiDialogVisible" title="AI洞察" width="620px">
      <div style="white-space: pre-wrap; min-height: 120px;">{{ aiInsightText || '—' }}</div>
      <template #footer>
        <el-button @click="aiDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import FilterBar from '@/components/FilterBar.vue'
import CardGrid from '@/components/CardGrid.vue'
import TrendChartModule from '@/components/TrendChartModule.vue'
import RankingList from '@/components/RankingList.vue'
import AdminTeamPerformance from '@/components/AdminTeamPerformance.vue'
import api from '@/utils/api'
import { getWeekStartEnd, getMonthStartEnd, getTodayString } from '@/utils/date'
import { useAuthStore } from '@/stores/auth'

// 核心状态
const loading = ref(false)
const authStore = useAuthStore()
// 根据当前用户身份确定默认视角：超级管理员默认“ALL”，否则取用户身份（CC/SS/LP）
const defaultRole = authStore?.isSuperAdmin ? 'ALL' : String(authStore?.user?.identity_type || 'CC').toUpperCase()
const filterParams = ref({
  timeRange: 'month',
  dateRange: [],
  groupId: null,
  role: defaultRole,
  userId: null
})
const summaryData = reactive({})
const activeMetricKey = ref('')
const roleScope = computed(() => filterParams.value.role || 'CC')
const visibleKeys = computed(() => {
  if (authStore.isSuperAdmin) {
    return [
      'task_completion_rate',
      'report_submission_rate',
      'period_sales_amount',
      'sales_achievement_rate',
      'period_new_sign_amount',
      'new_sign_count',
      'new_sign_achievement_rate',
      'period_referral_amount',
      'referral_count',
      'referral_achievement_rate',
      'period_total_renewal_amount',
      'total_renewal_achievement_rate',
      'period_upgrade_amount',
      'upgrade_count',
      'upgrade_rate'
    ]
  }
  const common = ['task_completion_rate', 'report_submission_rate', 'period_sales_amount']
  if (roleScope.value === 'CC') {
    return common.concat([
      'period_new_sign_amount',
      'new_sign_count',
      'new_sign_achievement_rate',
      'period_referral_amount',
      'referral_count',
      'referral_achievement_rate'
    ])
  }
  if (roleScope.value === 'SS') {
    return common.concat([
      'period_total_renewal_amount',
      'total_renewal_achievement_rate',
      'period_upgrade_amount',
      'upgrade_count',
      'upgrade_rate'
    ])
  }
  return common
})

// 指标字典（与卡片网格一致，用于显示友好名称）
const metricDict = {
  task_completion_rate: { name: '任务完成率' },
  period_sales_amount: { name: '销售总额' },
  sales_achievement_rate: { name: '销售目标达成率' },
  period_new_sign_amount: { name: '新单金额' },
  new_sign_count: { name: '新单单量' },
  new_sign_achievement_rate: { name: '新单目标达成率' },
  period_referral_amount: { name: '转介绍金额' },
  referral_count: { name: '转介绍单量' },
  referral_achievement_rate: { name: '转介绍目标达成率' },
  period_total_renewal_amount: { name: '总续费金额' },
  total_renewal_achievement_rate: { name: '总续费目标达成率' },
  period_upgrade_amount: { name: '升舱金额' },
  upgrade_count: { name: '升舱单量' },
  upgrade_rate: { name: '升舱率' },
  report_submission_rate: { name: '日报提交率' }
}

// 初始化日期范围
function initTimeByRange() {
  const v = filterParams.value.timeRange
  if (v === 'today') {
    const t = getTodayString()
    filterParams.value.dateRange = [t, t]
  } else if (v === 'week') {
    filterParams.value.dateRange = getWeekStartEnd(new Date())
  } else if (v === 'month') {
    filterParams.value.dateRange = getMonthStartEnd(new Date())
  }
}

// 刷新汇总数据
async function refreshSummary() {
  loading.value = true
  try {
    const [start, end] = filterParams.value.dateRange || []
    const group_id = filterParams.value.groupId || undefined
    const user_id = filterParams.value.userId || undefined
    const roleScope = filterParams.value.role || 'CC'

    // 计算 year/month（用于 /analytics/summary 月度聚合）
    const refDateStr = end || start || getTodayString()
    const refDate = new Date(refDateStr)
    const y = refDate.getFullYear()
    const m = refDate.getMonth() + 1

    // 统一数据（用于任务完成率、日报提交率）
    const { data: dataUnified } = await api.get('/analytics/data', {
      params: {
        start_date: start,
        end_date: end,
        group_id,
        user_id,
        role_scope: roleScope
      }
    })
    const unified = dataUnified?.metrics || {}

    // 身份月度汇总（用于金额与单量精细项）
    let ccMonth = null
    let ssMonth = null
    let ccGoal = null
    let ssGoal = null
    let ccPersonal = null
    let ssPersonal = null
    if (roleScope === 'CC' || roleScope === 'ALL') {
      try {
        const { data: cc } = await api.get('/analytics/summary', {
          params: { identity_type: 'CC', group_id, user_id, year: y, month: m }
        })
        ccMonth = cc?.month || null
        ccGoal = cc?.goal || null
        // 个人目标（仅个人视角）
        if (user_id) {
          try {
            const { data: pg } = await api.get('/goals/monthly/personal', {
              params: { identity_type: 'CC', group_id, user_id, year: y, month: m },
              suppressErrorMessage: true
            })
            const item = Array.isArray(pg?.items) ? pg.items[0] : null
            ccPersonal = item || null
          } catch {}
        }
      } catch {}
    }
    if (roleScope === 'SS' || roleScope === 'ALL') {
      try {
        const { data: ss } = await api.get('/analytics/summary', {
          params: { identity_type: 'SS', group_id, user_id, year: y, month: m }
        })
        ssMonth = ss?.month || null
        ssGoal = ss?.goal || null
        // 个人目标（仅个人视角）
        if (user_id) {
          try {
            const { data: pg } = await api.get('/goals/monthly/personal', {
              params: { identity_type: 'SS', group_id, user_id, year: y, month: m },
              suppressErrorMessage: true
            })
            const item = Array.isArray(pg?.items) ? pg.items[0] : null
            ssPersonal = item || null
          } catch {}
        }
      } catch {}
    }

    // 组装指定的15项指标（严格按你的要求）
    const cm = ccMonth || {}
    const sm = ssMonth || {}
    const cg = ccGoal || {}
    const sg = ssGoal || {}

    // 2. 销售总额（身份聚合）
    // 注意：0 是有效值，不应显示为 “—”，因此不要使用 `|| null` 处理
    const ccSalesAmount = Number(cm.new_sign_amount || 0) + Number(cm.referral_amount || 0)
    const ssSalesAmount = Number(sm.renewal_amount || 0) + Number(sm.upgrade_amount || 0)
    const period_sales_amount = (() => {
      if (roleScope === 'CC') return ccSalesAmount
      if (roleScope === 'SS') return ssSalesAmount
      return ccSalesAmount + ssSalesAmount
    })()

    // 10. 总续费金额（SS）
    // 0 也应如实展示，不再将 0 转为空
    const period_total_renewal_amount = (() => {
      const totalSS = Number(sm.renewal_amount || 0) + Number(sm.upgrade_amount || 0)
      if (roleScope === 'SS' || roleScope === 'ALL') return totalSS
      return null
    })()

    // 1 & 15：来自 /analytics/data
    const assembled = {
      task_completion_rate: unified.task_completion_rate ?? null,
      report_submission_rate: unified.report_submission_rate ?? null,
      // 2: 销售总额
      period_sales_amount,
      // 4: 新单金额（CC/ALL）
      period_new_sign_amount: (roleScope === 'CC' || roleScope === 'ALL') ? (cm.new_sign_amount ?? null) : null,
      // 5: 新单单量（CC/ALL）
      new_sign_count: (roleScope === 'CC' || roleScope === 'ALL') ? (cm.new_sign_count ?? null) : null,
      // 7: 转介绍金额（CC/ALL）
      period_referral_amount: (roleScope === 'CC' || roleScope === 'ALL') ? (cm.referral_amount ?? null) : null,
      // 8: 转介绍单量（CC/ALL）
      referral_count: (roleScope === 'CC' || roleScope === 'ALL') ? (cm.referral_count ?? null) : null,
      // 10: 总续费金额（SS/ALL）
      period_total_renewal_amount,
      // 12: 升舱金额（SS/ALL）
      period_upgrade_amount: (roleScope === 'SS' || roleScope === 'ALL') ? (sm.upgrade_amount ?? null) : null,
      // 13: 升舱单量（SS/ALL）
      upgrade_count: (roleScope === 'SS' || roleScope === 'ALL') ? (sm.upgrade_count ?? null) : null,
      // 额外：若需要单独展示续费金额（非必需项，此处不输出）
    }

    // 3: 销售目标达成率（ALL/CC/SS）
    const amountTargetAll = (() => {
      if (user_id) {
        // 个人视角：不做回退，缺失则视为 0，最终 >0 才计算
        if (roleScope === 'CC') {
          const a = Number(ccPersonal?.new_sign_target_amount || 0)
          const b = Number(ccPersonal?.referral_target_amount || 0)
          return a + b
        }
        if (roleScope === 'SS') {
          return Number(ssPersonal?.renewal_total_target_amount || 0)
        }
        const a = Number(ccPersonal?.new_sign_target_amount || 0) + Number(ccPersonal?.referral_target_amount || 0)
        const b = Number(ssPersonal?.renewal_total_target_amount || 0)
        return a + b
      }
      // 非个人视角：保持现有逻辑（组织/全局）
      if (roleScope === 'CC') return Number(cg.amount_target || 0)
      if (roleScope === 'SS') return Number(sg.amount_target || 0)
      return Number(cg.amount_target || 0) + Number(sg.amount_target || 0)
    })()
    assembled.sales_achievement_rate = (amountTargetAll > 0 && period_sales_amount != null)
      ? (Number(period_sales_amount) / amountTargetAll * 100)
      : null

    // 6: 新单目标达成率（ALL/CC）
    const newSignTarget = user_id
      ? Number(ccPersonal?.new_sign_target_amount || 0)
      : Number(cg.new_sign_target_amount || 0)
    assembled.new_sign_achievement_rate = ((roleScope === 'CC' || roleScope === 'ALL') && newSignTarget > 0 && assembled.period_new_sign_amount != null)
      ? (Number(assembled.period_new_sign_amount) / newSignTarget * 100)
      : null

    // 9: 转介绍目标达成率（ALL/CC）
    const referralTarget = user_id
      ? Number(ccPersonal?.referral_target_amount || 0)
      : Number(cg.referral_target_amount || 0)
    assembled.referral_achievement_rate = ((roleScope === 'CC' || roleScope === 'ALL') && referralTarget > 0 && assembled.period_referral_amount != null)
      ? (Number(assembled.period_referral_amount) / referralTarget * 100)
      : null

    // 11: 总续费目标达成率（ALL/SS）
    const renewalTotalTarget = user_id
      ? Number(ssPersonal?.renewal_total_target_amount || 0)
      : Number(sg.renewal_total_target_amount || 0)
    assembled.total_renewal_achievement_rate = ((roleScope === 'SS' || roleScope === 'ALL') && renewalTotalTarget > 0 && period_total_renewal_amount != null)
      ? (Number(period_total_renewal_amount) / renewalTotalTarget * 100)
      : null

    // 14: 升舱率（ALL/SS）——人数分母：升舱单量 / 升舱人数目标 × 100%
    const upgradeTargetCount = user_id
      ? Number(ssPersonal?.upgrade_target_count || 0)
      : Number(sg.upgrade_target_count || 0)
    const computedUpgradeRate = (upgradeTargetCount > 0 && assembled.upgrade_count != null)
      ? (Number(assembled.upgrade_count) / upgradeTargetCount * 100)
      : null
    if (user_id) {
      // 个人视角：不回退，没目标为空
      assembled.upgrade_rate = computedUpgradeRate
    } else {
      const progressUpgradeRate = sm?.progress?.upgrade_rate ?? null
      assembled.upgrade_rate = computedUpgradeRate ?? progressUpgradeRate ?? null
    }

    // 同步对象内容
    for (const k of Object.keys(summaryData)) delete summaryData[k]
    Object.assign(summaryData, assembled)
    if (!activeMetricKey.value) activeMetricKey.value = 'task_completion_rate'
  } catch (err) {
    ElMessage.error('获取汇总数据失败')
  } finally {
    loading.value = false
  }
}

// 卡片点击
function onCardClick(metricKey) {
  activeMetricKey.value = metricKey
}

// AI洞察（统一路由：/api/v1/ai/answer）
const aiDialogVisible = ref(false)
const aiInsightText = ref('')
async function onAIClick(metricKey) {
  try {
    const [start, end] = filterParams.value.dateRange || []
    const question = `请生成当前筛选范围下的AI总结，并重点关注指标：${metricKey}`
    const body = {
      question,
      output_target: filterParams.value.userId ? 'personal' : 'team',
      role_scope: filterParams.value.role || undefined,
      group_id: filterParams.value.groupId || undefined,
      user_id: filterParams.value.userId || undefined,
      start_date: start,
      end_date: end,
      page_context: 'analytics_dashboard',
      identity_hint: filterParams.value.role || undefined
    }
    const { data } = await api.post('/ai/answer', body)
    aiInsightText.value = data?.answer || '—'
    aiDialogVisible.value = true
  } catch (err) {
    ElMessage.error('获取AI洞察失败')
  }
}

onMounted(() => {
  // 如未初始化用户状态，先尝试恢复
  if (!authStore.user) {
    try { authStore.initAuth() } catch {}
  }
  // 超级管理员强制默认视角为“全局”
  if (authStore.isSuperAdmin && filterParams.value.role !== 'ALL') {
    filterParams.value.role = 'ALL'
  }
  initTimeByRange()
  refreshSummary()
})

// 监听筛选条件变化，自动刷新
import { watch } from 'vue'
watch(filterParams, () => { refreshSummary() }, { deep: true })
</script>

<style scoped>
.page-container { padding: 24px; }
.page-header { margin-bottom: 16px; }
.page-title { font-size: 22px; font-weight: 600; margin: 0 0 6px; }
.page-description { color: #909399; margin: 0; }
.content-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.chart-card { margin-top: 8px; }
</style>