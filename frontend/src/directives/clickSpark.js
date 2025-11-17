// A lightweight Vue directive that draws radial "spark" lines on click.
// Usage: v-click-spark="{ color: 'rgb(153,255,133)', sparkCount: 20 }"

const dpr = () => Math.max(1, Math.min(2, window.devicePixelRatio || 1))

let overlayCanvas = null
let ctx = null
let animations = []
let rafId = 0
let attachedCount = 0

function ensureOverlay() {
  if (overlayCanvas) return
  overlayCanvas = document.createElement('canvas')
  overlayCanvas.setAttribute('data-click-spark', 'true')
  Object.assign(overlayCanvas.style, {
    position: 'fixed',
    left: '0',
    top: '0',
    width: '100vw',
    height: '100vh',
    pointerEvents: 'none',
    zIndex: '500',
  })
  document.body.appendChild(overlayCanvas)
  ctx = overlayCanvas.getContext('2d')
  resize()
  window.addEventListener('resize', resize)
}

function cleanupOverlayIfNeeded() {
  if (attachedCount <= 0 && overlayCanvas) {
    window.removeEventListener('resize', resize)
    cancelAnimationFrame(rafId)
    rafId = 0
    animations = []
    overlayCanvas.remove()
    overlayCanvas = null
    ctx = null
  }
}

function resize() {
  if (!overlayCanvas) return
  const ratio = dpr()
  const w = Math.floor(window.innerWidth * ratio)
  const h = Math.floor(window.innerHeight * ratio)
  overlayCanvas.width = w
  overlayCanvas.height = h
  overlayCanvas.style.width = '100vw'
  overlayCanvas.style.height = '100vh'
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
}

function easeOutCubic(t) {
  const p = Math.min(1, Math.max(0, t))
  return 1 - Math.pow(1 - p, 3)
}

function tick() {
  if (!ctx) return
  ctx.clearRect(0, 0, window.innerWidth, window.innerHeight)
  const now = performance.now()
  animations = animations.filter(a => {
    const t = (now - a.start) / a.duration
    if (t >= 1) return false
    const p = easeOutCubic(t)
    const r = a.radius * p
    const len = a.size * (1 - p) * a.extraScale
    const alpha = (1 - p)
    ctx.lineWidth = a.lineWidth
    for (let i = 0; i < a.count; i++) {
      const angle = a.angles[i]
      const sx = a.x + Math.cos(angle) * r
      const sy = a.y + Math.sin(angle) * r
      const ex = a.x + Math.cos(angle) * (r + len)
      const ey = a.y + Math.sin(angle) * (r + len)
      ctx.beginPath()
      ctx.moveTo(sx, sy)
      ctx.lineTo(ex, ey)
      ctx.strokeStyle = `rgba(${a.rgb.r},${a.rgb.g},${a.rgb.b},${alpha})`
      ctx.stroke()
    }
    return true
  })
  if (animations.length > 0) {
    rafId = requestAnimationFrame(tick)
  } else {
    rafId = 0
  }
}

function createSpark(x, y, opts = {}) {
  const {
    color = 'rgb(153,255,133)',
    sparkCount = 20,
    sparkSize = 12,
    sparkRadius = 60,
    duration = 600,
    extraScale = 1,
    lineWidth = 2,
  } = opts

  const match = /rgba?\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)/.exec(color)
  const rgb = match
    ? { r: Number(match[1]), g: Number(match[2]), b: Number(match[3]) }
    : { r: 153, g: 255, b: 133 }

  const angles = []
  const step = (Math.PI * 2) / sparkCount
  for (let i = 0; i < sparkCount; i++) {
    // 少量随机扰动，让线条更生动
    angles.push(i * step + (Math.random() - 0.5) * 0.2)
  }

  animations.push({
    x,
    y,
    rgb,
    count: sparkCount,
    size: sparkSize,
    radius: sparkRadius,
    duration,
    extraScale,
    angles,
    lineWidth,
    start: performance.now(),
  })
  if (!rafId) rafId = requestAnimationFrame(tick)
}

function onClick(e, binding) {
  ensureOverlay()
  const opts = binding?.value || {}
  createSpark(e.clientX, e.clientY, opts)
}

export const clickSparkDirective = {
  mounted(el, binding) {
    attachedCount++
    el.__clickSparkHandler__ = (e) => onClick(e, binding)
    el.addEventListener('click', el.__clickSparkHandler__)
  },
  updated(el, binding) {
    // 更新时直接替换处理器的绑定参数
    el.__clickSparkHandler__ && el.removeEventListener('click', el.__clickSparkHandler__)
    el.__clickSparkHandler__ = (e) => onClick(e, binding)
    el.addEventListener('click', el.__clickSparkHandler__)
  },
  unmounted(el) {
    el.__clickSparkHandler__ && el.removeEventListener('click', el.__clickSparkHandler__)
    delete el.__clickSparkHandler__
    attachedCount--
    cleanupOverlayIfNeeded()
  },
}

// Convenience default export
export default clickSparkDirective