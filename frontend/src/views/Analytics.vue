<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">数据分析</h1>
      <p class="page-description">统一筛选、卡片概览、联动趋势与AI洞察</p>
    </div>

    <!-- 全局筛选器 -->
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>筛选条件</span>
          <div class="header-actions">
            <el-button :loading="loading" @click="refreshAll">刷新</el-button>
          </div>
        </div>
      </template>
      <div class="filters-bar">
        <!-- 时间范围选择 -->
        <el-radio-group v-model="timeRange" @change="onTimeRangeChange">
          <el-radio-button label="today">今日</el-radio-button>
          <el-radio-button label="week">本周</el-radio-button>
          <el-radio-button label="month">本月</el-radio-button>
          <el-radio-button label="custom">自定义</el-radio-button>
        </el-radio-group>

        <el-date-picker
          v-if="timeRange === 'custom'"
          v-model="customDateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="refreshAll"
        />

        <!-- 组织选择（管理员/超管可见） -->
        <el-select
          v-if="isAdminOrSuper"
          v-model="selectedGroupId"
          placeholder="选择组织"
          clearable
          style="width: 200px"
          @change="refreshAll"
        >
          <el-option label="全部组织" :value="null" />
          <el-option v-for="g in userGroups" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>

        <!-- 身份视角（仅超管可见） -->
        <el-select
          v-if="isSuperAdmin"
          v-model="roleScope"
          placeholder="选择视角"
          style="width: 200px"
          @change="refreshAll"
        >
          <el-option label="CC(顾问)视角" value="CC" />
          <el-option label="SS(班主任)视角" value="SS" />
          <el-option label="LP(英文辅导)视角" value="LP" />
          <el-option label="全局视角" value="ALL" />
        </el-select>

        <!-- 用户筛选（管理员/超管可见） -->
        <el-select
          v-if="isAdminOrSuper"
          v-model="selectedUserId"
          placeholder="选择用户"
          filterable
          clearable
          style="width: 220px"
          @change="refreshAll"
        >
          <el-option label="全部用户" :value="null" />
          <el-option v-for="u in userOptions" :key="u.id" :label="u.username" :value="u.id" />
        </el-select>
      </div>
    </el-card>

    <!-- 数据卡片网格（点击联动趋势） -->
    <div class="stats-grid">
      <el-card
        v-for="card in cards"
        :key="card.metricKey"
        class="stat-card"
        :class="{ active: activeMetricKey === card.metricKey }"
        @click="activateCard(card.metricKey)"
      >
        <div class="stat-content">
          <div class="stat-value">{{ formatCardValue(card) }}</div>
          <div class="stat-label">{{ card.title }}</div>
        </div>
        <div class="stat-icon">
          <el-tag size="small" type="info">{{ card.metricKey }}</el-tag>
        </div>
        <div class="card-actions">
          <el-button size="small" text type="primary" :loading="aiLoadingMap[card.metricKey]" @click.stop="fetchAIInsight(card.metricKey)">AI</el-button>
        </div>
      </el-card>
    </div>

    <!-- 联动趋势图 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>趋势分析</span>
          <div class="header-actions">
            <el-tag v-if="activeMetricKey" type="primary" size="small">指标：{{ activeMetricKey }}</el-tag>
          </div>
        </div>
      </template>
      <div class="chart-container">
        <v-chart :option="trendOption" :loading="loading" style="height: 320px" />
      </div>
    </el-card>

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
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import api from '@/utils/api'
import { getWeekStartEnd, getMonthStartEnd, getTodayString } from '@/utils/date'
import { useAuthStore } from '@/stores/auth'

use([CanvasRenderer, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const authStore = useAuthStore()
const currentUser = computed(() => authStore.user)
const isSuperAdmin = computed(() => !!currentUser.value?.is_super_admin || currentUser.value?.role === 'super_admin')
const isAdmin = computed(() => !!currentUser.value?.is_admin || currentUser.value?.role === 'admin')
const isAdminOrSuper = computed(() => isSuperAdmin.value || isAdmin.value)

// 全局筛选状态
const loading = ref(false)
const timeRange = ref('month')
const customDateRange = ref([])
const selectedGroupId = ref(null)
const selectedUserId = ref(null)
const roleScope = ref('CC')
const userOptions = ref([])
const userGroups = ref([])

// 数据与卡片
const summary = reactive({})
const cards = computed(() => buildCardsFromSummary(summary, roleScope.value))
const activeMetricKey = ref('')

// 趋势图配置
const trendSeries = ref([])
const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '3%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: trendSeries.value.map(d => d.date) },
  yAxis: { type: 'value' },
  series: [{ name: activeMetricKey.value || '指标', type: 'line', smooth: true, data: trendSeries.value.map(d => d.value) }]
}))

// AI洞察
const aiDialogVisible = ref(false)
const aiInsightText = ref('')
const aiLoadingMap = reactive({})

// 初始化
onMounted(() => {
  initTimeByRange()
  fetchUsersAndGroups()
  refreshAll()
})

// 构建卡片（固定15项指标，缺失值显示为—）
function buildCardsFromSummary(s, role) {
  const schema = [
    { metricKey: 'task_completion_rate', title: '任务完成率', unit: '%', isPercent: true },
    { metricKey: 'period_sales_amount', title: '销售总额', unit: 'USD' },
    { metricKey: 'period_referral_amount', title: '转介绍金额', unit: 'USD' },
    { metricKey: 'period_renewal_amount', title: '续费金额', unit: 'USD' },
    { metricKey: 'period_upgrade_amount', title: '升级金额', unit: 'USD' },
    { metricKey: 'referral_count', title: '转介绍单量', unit: '单' },
    { metricKey: 'renewal_count', title: '续费单量', unit: '单' },
    { metricKey: 'upgrade_count', title: '升级单量', unit: '单' },
    { metricKey: 'report_submission_rate', title: '日报提交率', unit: '%', isPercent: true },
    { metricKey: 'new_leads_count', title: '新增线索', unit: '个' },
    { metricKey: 'call_count', title: '通话单量', unit: '单' },
    { metricKey: 'conversion_rate', title: '转化率', unit: '%', isPercent: true },
    { metricKey: 'active_students', title: '活跃学员', unit: '人' },
    { metricKey: 'refund_rate', title: '退款率', unit: '%', isPercent: true },
    { metricKey: 'course_completion_rate', title: '课程完成率', unit: '%', isPercent: true }
  ]
  const list = schema.map(conf => ({ ...conf, value: s[conf.metricKey] }))
  if (!activeMetricKey.value && list.length) activeMetricKey.value = list[0].metricKey
  return list
}

// 时间范围变化
function onTimeRangeChange() {
  initTimeByRange()
  refreshAll()
}

function initTimeByRange() {
  if (timeRange.value === 'today') {
    const t = getTodayString()
    customDateRange.value = [t, t]
  } else if (timeRange.value === 'week') {
    customDateRange.value = getWeekStartEnd(new Date())
  } else if (timeRange.value === 'month') {
    customDateRange.value = getMonthStartEnd(new Date())
  }
}

// 刷新汇总与趋势
async function refreshAll() {
  await fetchSummary()
  if (activeMetricKey.value) await fetchTrend(activeMetricKey.value)
}

// 获取用户/组织选项（占位实现）
async function fetchUsersAndGroups() {
  try {
    // 可对接实际接口：/admin/users, /admin/groups
    userOptions.value = []
    userGroups.value = []
  } catch {}
}

// 构建请求参数
function buildParams(extra = {}) {
  const [start, end] = customDateRange.value || []
  const params = {
    start_date: start,
    end_date: end,
    group_id: selectedGroupId.value || undefined,
    user_id: selectedUserId.value || undefined,
    ...extra
  }
  return params
}

// 获取汇总数据
async function fetchSummary() {
  loading.value = true
  try {
    const [start, end] = customDateRange.value || []
    // 计算 year/month（用于 /analytics/summary 月度聚合）
    const refDateStr = end || start || getTodayString()
    const refDate = new Date(refDateStr)
    const y = refDate.getFullYear()
    const m = refDate.getMonth() + 1

    const group_id = selectedGroupId.value || undefined
    const user_id = selectedUserId.value || undefined

    // 统一数据（ALL/CC/SS/LP）
    const { data: dataUnified } = await api.get('/analytics/data', {
      params: {
        ...buildParams(),
        role_scope: roleScope.value || undefined
      }
    })
    const metrics = dataUnified?.metrics || {}

    // 身份月度汇总（用于金额与单量精细项）
    let ccMonth = null
    let ssMonth = null
    if (roleScope.value === 'CC' || roleScope.value === 'ALL') {
      try {
        const { data: cc } = await api.get('/analytics/summary', {
          params: { identity_type: 'CC', group_id, user_id, year: y, month: m }
        })
        ccMonth = cc?.month || null
      } catch {}
    }
    if (roleScope.value === 'SS' || roleScope.value === 'ALL') {
      try {
        const { data: ss } = await api.get('/analytics/summary', {
          params: { identity_type: 'SS', group_id, user_id, year: y, month: m }
        })
        ssMonth = ss?.month || null
      } catch {}
    }

    // 组装15项指标
    const assembled = {
      task_completion_rate: metrics.task_completion_rate ?? null,
      report_submission_rate: metrics.report_submission_rate ?? null,
      call_count: metrics.call_count ?? null,
      new_leads_count: metrics.new_leads_count ?? null,
      conversion_rate: metrics.conversion_rate ?? null,
      active_students: metrics.active_students ?? null,
      refund_rate: metrics.refund_rate ?? null,
      course_completion_rate: metrics.course_completion_rate ?? null
    }

    // 金额与单量（根据视角拼接）
    if (roleScope.value === 'CC') {
      const cm = ccMonth || {}
      assembled.period_sales_amount = cm.actual_amount ?? null
      assembled.period_referral_amount = cm.referral_amount ?? null
      assembled.period_renewal_amount = null
      assembled.period_upgrade_amount = null
      assembled.referral_count = cm.referral_count ?? null
      assembled.renewal_count = null
      assembled.upgrade_count = null
    } else if (roleScope.value === 'SS') {
      const sm = ssMonth || {}
      assembled.period_sales_amount = sm.actual_amount ?? null
      assembled.period_referral_amount = null
      assembled.period_renewal_amount = sm.renewal_amount ?? null
      assembled.period_upgrade_amount = sm.upgrade_amount ?? null
      assembled.referral_count = null
      assembled.renewal_count = sm.renewal_count ?? null
      assembled.upgrade_count = sm.upgrade_count ?? null
    } else {
      // ALL：汇总 CC 与 SS
      const cm = ccMonth || {}
      const sm = ssMonth || {}
      const ccSales = (cm.actual_amount ?? 0) || 0
      const ssSales = (sm.actual_amount ?? 0) || 0
      assembled.period_sales_amount = ccSales + ssSales
      assembled.period_referral_amount = cm.referral_amount ?? null
      assembled.period_renewal_amount = sm.renewal_amount ?? null
      assembled.period_upgrade_amount = sm.upgrade_amount ?? null
      assembled.referral_count = cm.referral_count ?? null
      assembled.renewal_count = sm.renewal_count ?? null
      assembled.upgrade_count = sm.upgrade_count ?? null
    }

    // 写入 summary 响应对象
    for (const k of Object.keys(summary)) delete summary[k]
    Object.assign(summary, assembled)
  } catch (err) {
    ElMessage.error('获取汇总数据失败')
  } finally {
    loading.value = false
  }
}

// 获取趋势数据
async function fetchTrend(metricKey) {
  loading.value = true
  try {
    const [start, end] = customDateRange.value || []
    // 映射到后端支持的趋势指标
    const isCC = roleScope.value === 'CC'
    const isSS = roleScope.value === 'SS'
    let metrics = []
    let identity_type = undefined
    if (metricKey === 'period_sales_amount') {
      metrics = isSS ? ['renewal_amount', 'upgrade_amount'] : ['new_sign_amount', 'referral_amount']
    } else if (metricKey === 'period_referral_amount') {
      metrics = ['referral_amount']
    } else if (metricKey === 'period_renewal_amount') {
      metrics = ['renewal_amount']
    } else if (metricKey === 'period_upgrade_amount') {
      metrics = ['upgrade_amount']
    } else if (metricKey === 'referral_count') {
      metrics = ['referral_count']
    } else if (metricKey === 'renewal_count') {
      metrics = ['renewal_count']
    } else if (metricKey === 'upgrade_count') {
      metrics = ['upgrade_count']
    } else {
      // 其他指标暂不支持趋势
      trendSeries.value = []
      loading.value = false
      return
    }
    if (isCC) identity_type = 'CC'
    if (isSS) identity_type = 'SS'

    const { data } = await api.get('/analytics/trend', {
      params: {
        start_date: start,
        end_date: end,
        identity_type,
        metrics
      }
    })
    const series = data?.series || []
    trendSeries.value = series.map(item => {
      const v = (() => {
        if (metricKey === 'period_sales_amount') {
          const ns = Number(item.new_sign_amount || 0)
          const rf = Number(item.referral_amount || 0)
          const rn = Number(item.renewal_amount || 0)
          const ug = Number(item.upgrade_amount || 0)
          // ALL 兼容：汇总可能包含全部四项
          return ns + rf + rn + ug
        }
        const kmap = {
          period_referral_amount: 'referral_amount',
          period_renewal_amount: 'renewal_amount',
          period_upgrade_amount: 'upgrade_amount',
          referral_count: 'referral_count',
          renewal_count: 'renewal_count',
          upgrade_count: 'upgrade_count'
        }
        const k = kmap[metricKey]
        return Number(item[k] || 0)
      })()
      return { date: item.date, value: v }
    })
  } catch (err) {
    ElMessage.error('获取趋势数据失败')
  } finally {
    loading.value = false
  }
}

// 激活卡片
function activateCard(metricKey) {
  activeMetricKey.value = metricKey
  fetchTrend(metricKey)
}

// AI洞察（统一路由：/api/v1/ai/answer）
async function fetchAIInsight(metricKey) {
  aiLoadingMap[metricKey] = true
  try {
    const [start, end] = customDateRange.value || []
    // 构建问题文本：强调当前指标
    const question = `请生成当前筛选范围下的AI总结，并重点关注指标：${metricKey}`
    const body = {
      question,
      output_target: selectedUserId.value ? 'personal' : 'team',
      role_scope: roleScope.value || undefined,
      group_id: selectedGroupId.value || undefined,
      user_id: selectedUserId.value || undefined,
      start_date: start,
      end_date: end,
      page_context: 'analytics',
      identity_hint: roleScope.value || undefined
    }
    const { data } = await api.post('/ai/answer', body)
    aiInsightText.value = data?.answer || '—'
    aiDialogVisible.value = true
  } catch (err) {
    ElMessage.error('获取AI洞察失败')
  } finally {
    aiLoadingMap[metricKey] = false
  }
}

// 展示格式
function formatCardValue(card) {
  const v = card.value
  if (v === null || v === undefined) return '—'
  if (card.isPercent) return `${Number(v).toFixed(0)}%`
  if (card.unit === 'USD') return formatCurrency(v)
  return `${v} ${card.unit || ''}`
}

function formatCurrency(v) {
  if (v === null || v === undefined) return '—'
  const num = Number(v) || 0
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(num)
}
</script>

<style scoped>
.page-container { padding: 24px; }
.page-header { margin-bottom: 16px; }
.page-title { font-size: 22px; font-weight: 600; margin: 0 0 6px; }
.page-description { color: #909399; margin: 0; }

.filters-bar { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.content-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }

.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 16px 0; }
.stat-card { cursor: pointer; }
.stat-card.active { border-color: #409eff; }
.stat-content .stat-value { font-size: 24px; font-weight: 700; color: #303133; }
.stat-content .stat-label { color: #909399; font-size: 13px; margin-top: 4px; }
.card-actions { margin-top: 8px; }

.chart-card { margin-top: 8px; }
.chart-container { width: 100%; height: 320px; }
</style>