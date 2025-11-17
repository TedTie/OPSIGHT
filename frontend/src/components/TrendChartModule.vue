<template>
  <div class="trend-module">
    <div v-if="!metricKey" class="empty">请选择一个指标查看趋势</div>
    <div v-else>
      <div class="toolbar">
        <el-button size="small" :loading="loading" @click="fetchTrend">刷新趋势</el-button>
      </div>
      <v-chart class="chart" :option="chartOption" autoresize />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import api from '@/utils/api'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent, DataZoomComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'

use([CanvasRenderer, LineChart, TitleComponent, TooltipComponent, GridComponent, DataZoomComponent, LegendComponent])

const props = defineProps({
  metricKey: { type: String, default: '' },
  filterParams: { type: Object, required: true }
})

const loading = ref(false)
const seriesData = ref([])

async function fetchTrend() {
  if (!props.metricKey) return
  loading.value = true
  try {
    const [start, end] = props.filterParams?.dateRange || []
    const role = props.filterParams?.role || 'CC'
    const isCC = role === 'CC'
    const isSS = role === 'SS'

    // 映射后端指标
    let metrics = []
    if (props.metricKey === 'period_sales_amount') {
      metrics = isCC ? ['new_sign_amount', 'referral_amount']
        : isSS ? ['renewal_amount', 'upgrade_amount']
        : ['new_sign_amount', 'referral_amount', 'renewal_amount', 'upgrade_amount']
    } else if (props.metricKey === 'period_new_sign_amount') {
      metrics = ['new_sign_amount']
    } else if (props.metricKey === 'period_referral_amount') {
      metrics = ['referral_amount']
    } else if (props.metricKey === 'period_renewal_amount') {
      metrics = ['renewal_amount']
    } else if (props.metricKey === 'period_upgrade_amount') {
      metrics = ['upgrade_amount']
    } else if (props.metricKey === 'period_total_renewal_amount') {
      metrics = ['renewal_amount', 'upgrade_amount']
    } else if (props.metricKey === 'referral_count') {
      metrics = ['referral_count']
    } else if (props.metricKey === 'renewal_count') {
      metrics = ['renewal_count']
    } else if (props.metricKey === 'upgrade_count') {
      metrics = ['upgrade_count']
    } else {
      seriesData.value = []
      loading.value = false
      return
    }

    const identity_type = isCC ? 'CC' : isSS ? 'SS' : undefined
    const { data } = await api.get('/analytics/trend', {
      params: {
        start_date: start,
        end_date: end,
        identity_type,
        metrics,
        group_id: props.filterParams?.groupId || undefined,
        user_id: props.filterParams?.userId || undefined
      }
    })
    const raw = data?.series || []
    seriesData.value = raw.map(item => {
      const val = (() => {
        if (props.metricKey === 'period_sales_amount') {
          const ns = Number(item.new_sign_amount || 0)
          const rf = Number(item.referral_amount || 0)
          const rn = Number(item.renewal_amount || 0)
          const ug = Number(item.upgrade_amount || 0)
          return ns + rf + rn + ug
        }
        if (props.metricKey === 'period_total_renewal_amount') {
          const rn = Number(item.renewal_amount || 0)
          const ug = Number(item.upgrade_amount || 0)
          return rn + ug
        }
        const kmap = {
          period_new_sign_amount: 'new_sign_amount',
          period_referral_amount: 'referral_amount',
          period_renewal_amount: 'renewal_amount',
          period_upgrade_amount: 'upgrade_amount',
          referral_count: 'referral_count',
          renewal_count: 'renewal_count',
          upgrade_count: 'upgrade_count'
        }
        const k = kmap[props.metricKey]
        return Number(item[k] || 0)
      })()
      return { date: item.date, value: val }
    })
  } catch (err) {
    ElMessage.error('获取趋势数据失败')
  } finally {
    loading.value = false
  }
}

watch(() => props.metricKey, () => { fetchTrend() })
watch(() => props.filterParams, () => { fetchTrend() }, { deep: true })

const chartOption = computed(() => {
  const dates = seriesData.value.map(i => i.date)
  const values = seriesData.value.map(i => i.value)
  return {
    title: { text: '指标趋势' },
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, bottom: 60 },
    dataZoom: [{ type: 'inside' }, { type: 'slider' }],
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value' },
    legend: { data: ['值'] },
    series: [{ name: '值', type: 'line', data: values, smooth: true }]
  }
})

// 注册组件
defineOptions({ name: 'TrendChartModule', components: { 'v-chart': VChart } })
</script>

<style scoped>
.trend-module { min-height: 280px; }
.empty { color: #909399; padding: 16px 0; }
.chart { height: 360px; width: 100%; }
.toolbar { margin-bottom: 8px; }
</style>