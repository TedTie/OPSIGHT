<template>
  <span class="text-flip" aria-hidden="true">
    <span
      v-for="(ch, i) in chars"
      :key="i + '-' + ch"
      class="flip-char"
      :style="{ '--delay': `${i * stagger}ms`, '--dur': `${duration}ms` }"
    >
      {{ ch }}
    </span>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  text: { type: String, required: true },
  duration: { type: Number, default: 600 },
  stagger: { type: Number, default: 60 }
})

const chars = computed(() => Array.from(props.text))
</script>

<style scoped>
.text-flip {
  display: inline-block;
  perspective: 800px;
}

.flip-char {
  display: inline-block;
  transform-origin: 50% 100%;
  /* 使用品牌渐变着色 */
  background: var(--brand-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  opacity: 0;
  animation: flipIn var(--dur) cubic-bezier(0.2, 0.68, 0, 1.01) both;
  animation-delay: var(--delay);
}

@keyframes flipIn {
  0% { transform: rotateX(90deg) translateY(12px); opacity: 0; }
  100% { transform: rotateX(0deg) translateY(0); opacity: 1; }
}
</style>