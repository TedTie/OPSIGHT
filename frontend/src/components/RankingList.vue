<template>
  <div class="ranking-container">
    <div class="header-row">
      <span class="title">排行榜</span>
      <el-tag v-if="metricKey" type="primary" size="small">指标：{{ metricName }}</el-tag>
      <el-button class="refresh-btn" :loading="loading" @click="fetchRankingData">刷新</el-button>
    </div>

    <el-empty v-if="!loading && (!top10 || top10.length === 0)" description="暂无排名数据" />

    <div v-else class="ranking-content">
      <!-- 领奖台区域（Top 3） -->
      <div class="podium-wrap">
        <div class="podium-banner"></div>
        <div class="podium">
          <!-- 第二名 -->
          <div v-if="top3[1]" class="podium-item second">
            <div class="avatar-wrap">
              <el-avatar :size="68" :src="top3[1].avatar_url" />
              <span class="medal medal-silver" aria-hidden="true">🥈</span>
            </div>
            <div class="podium-name" :title="top3[1].name || '—'">{{ top3[1].name || '—' }}</div>
            <div class="podium-value">{{ top3[1].formatted_value ?? top3[1].value ?? '—' }}</div>
          </div>

          <!-- 第一名（居中更大更高） -->
          <div v-if="top3[0]" class="podium-item first">
            <div class="avatar-wrap">
              <el-avatar :size="88" :src="top3[0].avatar_url" />
              <span class="medal medal-gold" aria-hidden="true">🥇</span>
            </div>
            <div class="podium-name" :title="top3[0].name || '—'">{{ top3[0].name || '—' }}</div>
            <div class="podium-value">{{ top3[0].formatted_value ?? top3[0].value ?? '—' }}</div>
          </div>

          <!-- 第三名 -->
          <div v-if="top3[2]" class="podium-item third">
            <div class="avatar-wrap">
              <el-avatar :size="68" :src="top3[2].avatar_url" />
              <span class="medal medal-bronze" aria-hidden="true">🥉</span>
            </div>
            <div class="podium-name" :title="top3[2].name || '—'">{{ top3[2].name || '—' }}</div>
            <div class="podium-value">{{ top3[2].formatted_value ?? top3[2].value ?? '—' }}</div>
          </div>
        </div>
      </div>

      <!-- 列表区域（第4名以后） -->
      <div class="rank-list">
        <div v-for="item in others" :key="item.user_id || item.rank" class="rank-row">
          <div class="rank-num">{{ item.rank }}</div>
          <el-avatar :size="36" :src="item.avatar_url" />
          <div class="row-name" :title="item.name || '—'">{{ item.name || '—' }}</div>
          <div class="row-value">{{ item.formatted_value ?? item.value ?? '—' }}</div>
        </div>
      </div>
    </div>

    <!-- 我的排名（不在Top10时显示） -->
    <el-card v-if="currentUserRank && !isCurrentInTop10" class="my-rank-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>我的排名</span>
          <el-tag type="success" size="small">不在Top10，单独显示</el-tag>
        </div>
      </template>
      <div class="my-rank-row">
        <el-tag size="small">第 {{ currentUserRank.rank }} 名</el-tag>
        <div class="user-cell">
          <el-avatar :size="28" :src="currentUserRank.avatar_url" />
          <span class="name">{{ currentUserRank.name || '—' }}</span>
        </div>
        <span class="value">{{ currentUserRank.formatted_value ?? currentUserRank.value ?? '—' }}</span>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const props = defineProps({
  metricKey: { type: String, default: '' },
  filterParams: { type: Object, required: true }
})

const loading = ref(false)
const top10 = ref([])
const currentUserRank = ref(null)

// 指标字典（与卡片网格一致）
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

const metricName = computed(() => metricDict[props.metricKey]?.name || props.metricKey)

const isCurrentInTop10 = computed(() => {
  const uid = currentUserRank.value?.user_id
  if (!uid || !Array.isArray(top10.value)) return false
  return top10.value.some(it => it.user_id === uid)
})

async function fetchRankingData() {
  if (!props.metricKey) {
    // 若没有有效指标，清空数据
    top10.value = []
    currentUserRank.value = null
    return
  }
  loading.value = true
  try {
    const [start, end] = props.filterParams?.dateRange || []
    const query = {
      metric_key: props.metricKey,
      start_date: start,
      end_date: end,
      group_id: props.filterParams?.groupId || undefined,
      user_id: props.filterParams?.userId || undefined,
      role_scope: props.filterParams?.role || undefined
    }
    const { data } = await api.get('/analytics/ranking', {
      params: query,
      suppressErrorMessage: true
    })
    const list = Array.isArray(data?.top_10) ? data.top_10 : []
    console.log('[RankingList] Fetched top10:', list)
    top10.value = list
    currentUserRank.value = data?.current_user_rank || null
    console.log('[RankingList] Fetched currentUserRank:', currentUserRank.value)
  } catch (err) {
    // 如果后端尚未提供该接口或返回错误，给出温和提示
    ElMessage.warning('获取排行榜失败')
    top10.value = []
    currentUserRank.value = null
  } finally {
    loading.value = false
  }
}

watch(() => props.metricKey, () => { fetchRankingData() })
watch(() => props.filterParams, () => { fetchRankingData() }, { deep: true })

onMounted(() => {
  fetchRankingData()
})

// 派生出 Top3 与后续列表
const top3 = computed(() => (Array.isArray(top10.value) ? top10.value.slice(0, 3) : []))
const others = computed(() => (Array.isArray(top10.value) ? top10.value.slice(3) : []))
</script>

<style scoped>
.ranking-container { margin-top: 8px; }
.header-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.title { font-weight: 600; }
.refresh-btn { margin-left: auto; }

/* 领奖台区域 */
.podium-wrap { position: relative; margin-bottom: 16px; overflow: visible; }
.podium-banner {
  position: absolute;
  inset: 0 0 auto 0;
  height: 200px;
  background: linear-gradient(135deg, #DFFBF1 0%, #ECFFF8 100%);
  border-radius: var(--radius-xl);
  opacity: 0.9;
}
.ranking-content, .podium, .rank-list, .podium-item { position: relative; z-index: 1; }
.podium { position: relative; display: flex; align-items: flex-end; justify-content: center; gap: 28px; padding: 28px 20px 54px; }

/* Podium Cards with Colored Backgrounds */
.podium-item { 
  text-align: center;
  padding: 20px 16px;
  border-radius: var(--radius-lg);
  min-width: 140px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.6);
  transition: transform 0.3s ease;
}

.podium-item:hover {
  transform: translateY(-8px) !important;
}

/* First Place - Gold Gradient */
.podium-item.first {
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
  transform: translateY(-16px);
  min-width: 160px;
  box-shadow: 0 12px 32px rgba(255, 215, 0, 0.3);
}

/* Second Place - Silver Gradient */
.podium-item.second {
  background: linear-gradient(135deg, #E8E8E8 0%, #C0C0C0 100%);
  transform: translateY(0);
  box-shadow: 0 8px 24px rgba(192, 192, 192, 0.3);
}

/* Third Place - Bronze Gradient */
.podium-item.third {
  background: linear-gradient(135deg, #CD7F32 0%, #B87333 100%);
  transform: translateY(0);
  box-shadow: 0 8px 24px rgba(205, 127, 50, 0.3);
}

.podium-item .podium-name { 
  font-weight: 700; 
  margin-top: 12px; 
  line-height: 1.3; 
  color: var(--text-strong);
  white-space: normal; 
  word-break: break-word; 
}

.podium-item .podium-value { 
  margin-top: 8px; 
  line-height: 1.2; 
  font-weight: 600;
  font-size: 16px;
  color: var(--text-normal);
}

.avatar-wrap { position: relative; display: inline-block; }
.avatar-wrap :deep(.el-avatar) { 
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15); 
  border: 3px solid rgba(255, 255, 255, 0.8); 
}

.medal { 
  position: absolute; 
  bottom: -8px; 
  left: 50%; 
  transform: translateX(-50%); 
  font-size: 20px; 
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); 
}

/* 列表区域 */
.rank-list { display: flex; flex-direction: column; gap: 10px; }
.rank-row {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: space-between;
  padding: 14px 16px;
  border-radius: var(--radius-md);
  background: rgba(255,255,255,0.90);
  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.6);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.2s ease;
}

.rank-row:hover {
  background: rgba(255,255,255,0.95);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.rank-num { width: 32px; text-align: center; font-weight: 700; color: var(--text-strong); font-size: 16px; }
.row-name { flex: 1; color: var(--text-strong); font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.row-value { color: var(--color-primary); font-weight: 700; font-size: 15px; }

/* 我的排名卡片保持 */
.user-cell { display: flex; align-items: center; gap: 8px; }
.name { color: var(--text-strong); }
.my-rank-card { margin-top: 12px; }
.my-rank-row { display: flex; align-items: center; gap: 12px; }
.value { font-weight: 600; color: var(--text-strong); }

/* 响应式 */
@media (max-width: 768px) {
  .podium { gap: 16px; padding: 20px 16px 40px; }
  .podium-item { min-width: 110px; padding: 16px 12px; }
  .podium-item.first { min-width: 130px; transform: translateY(-12px); }
  .rank-row { padding: 12px 14px; }
}
</style>