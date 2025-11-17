<template>
  <el-card
    class="data-card hover-effect"
    :class="{ active: isActive }"
    @click="onClick"
    @mousemove="onMouseMove"
    @mouseleave="onMouseLeave"
    :style="mouseStyle"
  >
    <div class="card-top">
      <div class="title">{{ title }}</div>
      <el-button text type="primary" @click.stop="emit('aiClick', metricKey)">AI洞察</el-button>
    </div>
    <div class="value">{{ displayValue }}</div>
    <div class="unit" v-if="unit">{{ unit }}</div>
  </el-card>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  unit: { type: String, default: '' },
  metricKey: { type: String, required: true },
  isActive: { type: Boolean, default: false }
})
const emit = defineEmits(['cardClick', 'aiClick'])

const displayValue = computed(() => {
  if (props.value === null || props.value === undefined || props.value === '') return '—'
  // 货币统一使用 USD 显示（当单位为 USD 或包含 USD 的复合单位时）
  if (typeof props.value === 'number' && typeof props.unit === 'string' && props.unit.includes('USD')) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(props.value)
  }
  // 默认：千分位
  if (typeof props.value === 'number') return props.value.toLocaleString()
  return props.value
})

function onClick() {
  emit('cardClick', props.metricKey)
}

// 悬浮高亮效果：跟随鼠标位置的渐变光斑
const mouseStyle = ref({})
function onMouseMove(e) {
  const rect = e.currentTarget.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  mouseStyle.value = {
    '--mouse-x': `${x}px`,
    '--mouse-y': `${y}px`
  }
}
function onMouseLeave() {
  mouseStyle.value = {}
}
</script>

<style scoped>
.data-card {
  cursor: pointer;
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-md);
}
.data-card.active { border-color: var(--el-color-primary); }
.card-top { display: flex; justify-content: space-between; align-items: center; }
.title { font-weight: 600; }
.value { font-size: 20px; margin-top: 8px; }
.unit { color: #909399; margin-top: 2px; }

/* 悬浮渐变光效（参考卡片hover效果） */
.hover-effect::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(600px circle at var(--mouse-x, -100px) var(--mouse-y, -100px), rgba(16, 185, 129, 0.14), transparent 60%),
    radial-gradient(500px circle at var(--mouse-x, -100px) var(--mouse-y, -100px), rgba(14, 165, 233, 0.12), transparent 55%),
    radial-gradient(400px circle at var(--mouse-x, -100px) var(--mouse-y, -100px), rgba(99, 102, 241, 0.12), transparent 50%);
  opacity: 0;
  transition: opacity 0.25s ease;
}
.hover-effect:hover::before { opacity: 1; }
.hover-effect:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
</style>