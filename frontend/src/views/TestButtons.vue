<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">按钮测试页面</h1>
      <p class="page-description">测试Element Plus按钮组件</p>
    </div>
    
    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>基础按钮测试</span>
        </div>
      </template>
      
      <div class="button-test-section">
        <h3>基础按钮</h3>
        <div class="button-group">
          <el-button>默认按钮</el-button>
          <el-button type="primary">主要按钮</el-button>
          <el-button type="success">成功按钮</el-button>
          <el-button type="info">信息按钮</el-button>
          <el-button type="warning">警告按钮</el-button>
          <el-button type="danger">危险按钮</el-button>
        </div>
        
        <h3>带图标的按钮</h3>
        <div class="button-group">
          <el-button type="primary" :icon="Plus">创建</el-button>
          <el-button type="success" :icon="Check">保存</el-button>
          <el-button type="danger" :icon="Delete">删除</el-button>
        </div>
        
        <h3>加载状态按钮</h3>
        <div class="button-group">
          <el-button type="primary" :loading="loading" @click="toggleLoading">
            {{ loading ? '加载中...' : '点击加载' }}
          </el-button>
        </div>
        
        <h3>禁用状态按钮</h3>
        <div class="button-group">
          <el-button disabled>禁用按钮</el-button>
          <el-button type="primary" disabled>禁用主要按钮</el-button>
        </div>
      </div>
    </el-card>
    
    <!-- 玻璃拟态卡片示例（独立类 .glass-card，可复用） -->
    <div class="glass-demo bubble-bg">
      <div class="glass-card">
        <div class="glass-demo-content">
          <h3 style="margin: 0 0 8px 0;">Glass 卡片示例</h3>
          <p style="margin: 0;">这是一个玻璃拟态卡片示例，背景会被模糊处理，便于复用。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Plus from '~icons/tabler/plus'
import Check from '~icons/tabler/check'
import Delete from '~icons/tabler/trash'

const loading = ref(false)

const toggleLoading = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
  }, 2000)
}
</script>

<style scoped>
.button-test-section {
  padding: 20px 0;
}

.button-test-section h3 {
  margin: 20px 0 10px 0;
  color: #303133;
}

.button-group {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.glass-demo {
  padding: 16px;
  margin-top: 16px;
}

.glass-demo-content {
  min-height: 100px;
}
</style>