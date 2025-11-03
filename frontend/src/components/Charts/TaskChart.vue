<template>
  <div class="chart-container">
    <v-chart
      :option="chartOption"
      :style="{ height: height, width: '100%' }"
      autoresize
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart, LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'

// 注册必要的组件
use([
  CanvasRenderer,
  PieChart,
  BarChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const props = defineProps({
  type: {
    type: String,
    default: 'pie',
    validator: (value) => ['pie', 'bar', 'line'].includes(value)
  },
  data: {
    type: Array,
    default: () => []
  },
  title: {
    type: String,
    default: ''
  },
  height: {
    type: String,
    default: '300px'
  }
})

// 饼图配置
const pieOption = computed(() => ({
  title: {
    text: props.title,
    left: 'center',
    textStyle: {
      fontSize: 16,
      fontWeight: 'normal'
    }
  },
  tooltip: {
    trigger: 'item',
    formatter: '{a} <br/>{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    left: 'left'
  },
  series: [
    {
      name: props.title,
      type: 'pie',
      radius: '50%',
      data: props.data,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }
  ]
}))

// 柱状图配置
const barOption = computed(() => ({
  title: {
    text: props.title,
    left: 'center',
    textStyle: {
      fontSize: 16,
      fontWeight: 'normal'
    }
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: props.data.map(item => item.name)
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: props.title,
      type: 'bar',
      data: props.data.map(item => item.value),
      itemStyle: {
        color: '#409EFF'
      }
    }
  ]
}))

// 折线图配置
const lineOption = computed(() => ({
  title: {
    text: props.title,
    left: 'center',
    textStyle: {
      fontSize: 16,
      fontWeight: 'normal'
    }
  },
  tooltip: {
    trigger: 'axis'
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: props.data.map(item => item.name)
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: props.title,
      type: 'line',
      data: props.data.map(item => item.value),
      smooth: true,
      itemStyle: {
        color: '#67C23A'
      }
    }
  ]
}))

// 根据类型选择配置
const chartOption = computed(() => {
  switch (props.type) {
    case 'pie':
      return pieOption.value
    case 'bar':
      return barOption.value
    case 'line':
      return lineOption.value
    default:
      return pieOption.value
  }
})
</script>

<style scoped>
.chart-container {
  width: 100%;
}
</style>