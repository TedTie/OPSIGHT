<template>
  <div>
    <!-- 浮动球本体 -->
    <div
      ref="ballRef"
      class="ai-ball"
      :style="ballStyle"
      @click="onBallClick"
    >
      <span class="ai-ball-core"></span>
      <span class="ai-ball-glow"></span>
      <span class="ai-ball-ring"></span>
      <el-icon class="ai-ball-glyph"><i-tabler-sparkles /></el-icon>
    </div>

    <!-- 聊天弹窗 -->
    <div
      v-if="isOpen"
      ref="chatRef"
      class="ai-chat"
      :style="chatStyle"
    >
      <div class="ai-chat-header">
        <div class="ai-chat-title">AI 助手</div>
        <button class="ai-chat-close" @click="isOpen = false">✕</button>
      </div>
      <div class="ai-chat-body">
        <div v-if="welcomeText" class="ai-welcome">{{ welcomeText }}</div>
        <div v-if="recommendedQuestions.length" class="ai-recommend">
          <div class="label">推荐问题：</div>
          <div class="chips">
            <button
              v-for="(q, idx) in recommendedQuestions"
              :key="idx"
              class="chip"
              @click="useQuestion(q)"
            >{{ q }}</button>
          </div>
        </div>
        <div class="ai-messages">
          <div
            v-for="(m, i) in messages"
            :key="i"
            class="msg"
            :class="m.role"
          >
            <div class="msg-content">{{ m.content }}</div>
          </div>
        </div>
      </div>
      <div class="ai-chat-input">
        <input
          v-model="inputText"
          type="text"
          placeholder="请输入问题，回车发送"
          @keydown.enter.prevent="send"
        />
        <button class="send-btn" @click="send" :disabled="sending">发送</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useDraggable, useStorage } from '@vueuse/core'
import { getAISystemKnowledge, postAIChat } from '@/utils/ai'

// 位置持久化
const storedPos = useStorage('ai-ball-position', {
  x: Math.max(window.innerWidth - 80, 16),
  y: Math.max(window.innerHeight - 120, 16)
})

const ballRef = ref(null)
const { x, y, isDragging } = useDraggable(ballRef, {
  initialValue: { x: storedPos.value.x, y: storedPos.value.y }
})

// 打开状态与聊天数据
const isOpen = ref(false)
const chatRef = ref(null)
const inputText = ref('')
const sending = ref(false)
const messages = ref([])
const welcomeText = ref('你好！我是系统向导，帮你快速找到功能入口。')
const recommendedQuestions = ref([
  '如何查看我的任务进度？',
  '如何提交当天的日报？',
  '哪里可以设置月度目标？'
])

// 计算样式
const ballStyle = computed(() => ({
  left: x.value + 'px',
  top: y.value + 'px'
}))

const chatStyle = computed(() => {
  const gap = 12
  const width = 320
  const height = 380
  const screenMid = window.innerWidth / 2
  const onRight = x.value > screenMid
  const left = onRight ? x.value - width - gap : x.value + 48 + gap
  const top = Math.min(Math.max(y.value - height / 2, 12), window.innerHeight - height - 12)
  return {
    left: left + 'px',
    top: top + 'px',
    width: width + 'px',
    height: height + 'px'
  }
})

// 位置记忆
watch([x, y, isDragging], () => {
  if (!isDragging.value) {
    storedPos.value = { x: x.value, y: y.value }
  }
})

// 点击浮动球
function onBallClick() {
  if (isDragging.value) return
  isOpen.value = !isOpen.value
  if (isOpen.value && messages.value.length === 0) {
    // 加载系统知识（用于增强欢迎语或推荐问题）
    fetchSystemKnowledge()
  }
}

function useQuestion(q) {
  inputText.value = q
  send()
}

async function fetchSystemKnowledge() {
  try {
    const { data } = await getAISystemKnowledge()
    if (data?.welcome) welcomeText.value = data.welcome
    if (Array.isArray(data?.recommended)) recommendedQuestions.value = data.recommended
  } catch (e) {
    // 静默失败，保留默认欢迎与推荐
  }
}

async function send() {
  const text = (inputText.value || '').trim()
  if (!text || sending.value) return
  sending.value = true
  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  try {
    const { data } = await postAIChat({ question: text })
    const answer = data?.answer || '抱歉，我未能理解你的问题。'
    messages.value.push({ role: 'assistant', content: answer })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '网络异常或服务不可用，请稍后再试。' })
  } finally {
    sending.value = false
  }
}

// 点击外部关闭
function onDocClick(ev) {
  const ballEl = ballRef.value
  const chatEl = chatRef.value
  if (!isOpen.value) return
  const target = ev.target
  if (ballEl && ballEl.contains(target)) return
  if (chatEl && chatEl.contains(target)) return
  isOpen.value = false
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
})
</script>

<style scoped>
.ai-ball {
  position: fixed;
  z-index: 3000;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  cursor: grab;
  user-select: none;
  overflow: visible;
  transform: translateZ(0);
}
.ai-ball:active { cursor: grabbing; }

/* 玻璃态核心（品牌渐变） */
.ai-ball-core {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: var(--brand-gradient);
  box-shadow: 0 12px 28px rgba(16, 185, 129, 0.25), 0 18px 36px rgba(99, 102, 241, 0.20);
  filter: saturate(1.05);
}

/* 内部高光与微妙纹理 */
.ai-ball-core::before {
  content: '';
  position: absolute;
  inset: 2px;
  border-radius: 50%;
  background:
    radial-gradient(120% 120% at 30% 30%, rgba(255,255,255,0.45), transparent 40%),
    radial-gradient(100% 100% at 70% 70%, rgba(255,255,255,0.18), transparent 45%),
    conic-gradient(from 180deg at 50% 50%, rgba(255,255,255,0.06), rgba(0,0,0,0.08), rgba(255,255,255,0.06));
  mix-blend-mode: screen;
}

/* 外部柔光 */
.ai-ball-glow {
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  background: radial-gradient(60% 60% at 50% 50%, rgba(16,185,129,0.25), transparent 70%);
  filter: blur(8px);
  opacity: 0.9;
  pointer-events: none;
}

/* 轻微呼吸动画 */
@keyframes breathe {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.04); }
}
.ai-ball-core { animation: breathe 4s ease-in-out infinite; }

/* 细环与交互波纹 */
.ai-ball-ring {
  position: absolute;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.22) inset;
  background:
    radial-gradient(120% 120% at 50% 50%, rgba(255,255,255,0.12), transparent 60%);
  opacity: 0.7;
}
.ai-ball:active .ai-ball-ring {
  animation: ripple 500ms ease-out;
}
@keyframes ripple {
  0% { transform: scale(1); opacity: 0.8; }
  100% { transform: scale(1.2); opacity: 0; }
}

/* 图标（Tabler） */
.ai-ball-glyph {
  position: relative;
  font-size: 22px;
  color: #ffffff;
  filter: drop-shadow(0 2px 6px rgba(0,0,0,0.15));
}

.ai-chat {
  position: fixed;
  z-index: 3001;
  background: rgba(255,255,255,0.82);
  backdrop-filter: blur(10px) saturate(1.05);
  border-radius: 14px;
  box-shadow: 0 18px 36px rgba(2, 8, 23, 0.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.35);
  opacity: 0;
  transform: translateY(8px) scale(0.98);
  animation: chatIn 280ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
.ai-chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: linear-gradient(180deg, rgba(255,255,255,0.65), rgba(255,255,255,0.35));
  border-bottom: 1px solid rgba(255,255,255,0.45);
}
.ai-chat-title { font-weight: 600; letter-spacing: 0.2px; }
.ai-chat-close {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 16px;
  color: #374151;
}
.ai-chat-body {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
}
.ai-welcome { color: #4b5563; margin-bottom: 8px; }
.ai-recommend .label { color: #6b7280; margin-bottom: 6px; }
.chips { display: flex; gap: 6px; flex-wrap: wrap; }
.chip {
  border: 1px solid rgba(16,185,129,0.35);
  background: rgba(255,255,255,0.9);
  padding: 4px 10px;
  border-radius: 12px;
  cursor: pointer;
}
.ai-messages { display: flex; flex-direction: column; gap: 10px; }
.msg { display: flex; }
.msg.user { justify-content: flex-end; }
.msg.assistant { justify-content: flex-start; }
.msg-content {
  max-width: 80%;
  background: rgba(255,255,255,0.9);
  border: 1px solid rgba(229,231,235,0.8);
  padding: 8px 12px;
  border-radius: 10px;
  white-space: pre-wrap;
  box-shadow: 0 4px 12px rgba(2, 8, 23, 0.06);
}
.msg.user .msg-content {
  background: rgba(236,245,255,0.95);
  border-color: rgba(217,236,255,0.9);
}

.ai-chat-input {
  display: flex;
  gap: 8px;
  padding: 10px;
  border-top: 1px solid rgba(255,255,255,0.45);
  background: linear-gradient(180deg, rgba(255,255,255,0.6), rgba(255,255,255,0.4));
}
.ai-chat-input input {
  flex: 1;
  border: 1px solid rgba(220,223,230,0.85);
  border-radius: 8px;
  padding: 8px 10px;
  background: rgba(255,255,255,0.92);
}
.send-btn {
  border: none;
  background: var(--brand-gradient);
  color: #fff;
  border-radius: 8px;
  padding: 8px 14px;
  cursor: pointer;
  box-shadow: 0 6px 16px rgba(14, 165, 233, 0.25);
}
.send-btn:disabled { opacity: 0.6; cursor: not-allowed; }

@keyframes chatIn {
  0% { opacity: 0; transform: translateY(8px) scale(0.98); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}
</style>
.chip:hover {
  border-color: rgba(99,102,241,0.45);
  background: rgba(255,255,255,0.95);
}