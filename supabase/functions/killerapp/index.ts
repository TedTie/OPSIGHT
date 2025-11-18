import { serve } from "https://deno.land/std@0.224.0/http/server.ts"

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, apikey, X-Client-Info, X-Requested-With"
}

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json", ...corsHeaders } })
}

function notFound() { return json({ detail: "Not Found" }, 404) }

async function parseBody(req: Request) {
  const text = await req.text()
  try { return JSON.parse(text || "{}") } catch { return {} }
}

serve(async (req: Request): Promise<Response> => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders })
  const u = new URL(req.url)
  const path = u.pathname.replace(/^\/+/, "")
  // URL pattern: /killerapp/<...>
  const parts = path.split("/")
  const afterFn = parts.slice(1).join("/")

  const defaultAISettings = { provider: "openrouter", api_key: "", base_url: "https://openrouter.ai/api/v1", model_name: "openai/gpt-5", max_tokens: 2000, temperature: 0.7 }
  const defaultSystemSettings = { system_name: "KillerApp", timezone: "Asia/Shanghai", language: "zh-CN", auto_analysis: true, data_retention_days: 90 }
  // deno-lint-ignore prefer-const
  let aiSettingsStore = { ...defaultAISettings }
  // deno-lint-ignore prefer-const
  let systemSettingsStore = { ...defaultSystemSettings }
  const personalGoalsStore: Record<string, Record<string, any>> = {}
  const mockUsers = [
    { id: 101, username: "alice", identity_type: "CC", group_id: 1, group_name: "销售一组" },
    { id: 102, username: "bob", identity_type: "CC", group_id: 1, group_name: "销售一组" },
    { id: 201, username: "charlie", identity_type: "SS", group_id: 2, group_name: "教务一组" },
    { id: 202, username: "diana", identity_type: "SS", group_id: 2, group_name: "教务一组" },
    { id: 301, username: "eve", identity_type: "LP", group_id: 3, group_name: "产品一组" }
  ]

  if (afterFn.startsWith("api/v1/ai/system-knowledge") && req.method === "GET") {
    return json({ welcome: "你好！我是系统向导，帮你快速找到功能入口。", recommended: ["如何查看我的任务进度？", "如何提交当天的日报？", "哪里可以设置月度目标？"] })
  }

  if (afterFn.startsWith("api/v1/ai/chat") && req.method === "POST") {
    const body = await parseBody(req) as { question?: string }
    const q = String(body.question || "")
    let answer = "这是 AI 向导的示例回答：请在系统中查找对应功能入口。"
    if (/任务|进度/.test(q)) answer = "任务进度可在“任务管理”与“仪表盘”查看。"
    else if (/日报|提交/.test(q)) answer = "提交日报请进入“日报”页面，点击新建后填写并提交。"
    else if (/目标|月度/.test(q)) answer = "月度目标可在“分析/目标管理”页进行设置与查看。"
    return json({ answer })
  }

  if ((afterFn.startsWith("auth/login") || afterFn.startsWith("api/v1/auth/login")) && req.method === "POST") {
    const body = await parseBody(req) as { username?: string, password?: string }
    const username = String(body.username || "").trim().toLowerCase()
    const password = String(body.password || "").trim()
    if (username === "admin" && password.length > 0) {
      return json({ user: { id: 1, username: "admin", role: "super_admin" } })
    }
    return json({ detail: "用户名不存在或账户已被禁用" }, 401)
  }

  if ((afterFn.startsWith("auth/logout") || afterFn.startsWith("api/v1/auth/logout")) && req.method === "POST") {
    return json({ success: true })
  }

  if ((afterFn.startsWith("auth/me") || afterFn.startsWith("api/v1/auth/me")) && req.method === "GET") {
    return json({ id: 1, username: "demo", role: "super_admin" })
  }

  if (afterFn.startsWith("api/v1/analytics/summary") && req.method === "GET") {
    const idt = (u.searchParams.get("identity_type") || "").toUpperCase()
    if (idt === "CC") return json({ month: { actual_amount: 250000, new_sign_amount: 215000, referral_amount: 35000, referral_count: 12 }, progress_display: { amount_rate: 0.8, new_sign_achievement_rate: 0.72, referral_achievement_rate: 0.35 } })
    if (idt === "SS") return json({ month: { actual_amount: 200000, renewal_amount: 120000, upgrade_amount: 80000, renewal_count: 24, upgrade_count: 9 }, progress_display: { total_renewal_achievement_rate: 0.6 } })
    return json({ month: { actual_amount: 0 } })
  }

  if (afterFn.startsWith("api/v1/analytics/trend") && req.method === "GET") {
    const now = new Date()
    const series: any[] = []
    for (let i = 9; i >= 0; i--) {
      const d = new Date(now)
      d.setDate(now.getDate() - i)
      const day = d.toISOString().slice(0, 10)
      const ns = Math.round(60000 + Math.random() * 40000)
      const rf = Math.round(15000 + Math.random() * 20000)
      const rn = Math.round(50000 + Math.random() * 40000)
      const ug = Math.round(20000 + Math.random() * 30000)
      series.push({ date: day, new_sign_amount: ns, referral_amount: rf, renewal_amount: rn, upgrade_amount: ug, referral_count: Math.floor(1 + Math.random() * 5), renewal_count: Math.floor(3 + Math.random() * 8), upgrade_count: Math.floor(1 + Math.random() * 4) })
    }
    return json({ series })
  }

  if (afterFn.startsWith("api/v1/analytics/data") && req.method === "GET") {
    const metrics = { task_completion_rate: 0.82, report_submission_rate: 0.93, call_count: 180, new_leads_count: 45, conversion_rate: 0.23, active_students: 620, refund_rate: 0.015, course_completion_rate: 0.71 }
    return json({ metrics })
  }

  if (afterFn.startsWith("api/v1/analytics/ai-insight") && req.method === "POST") {
    return json({ insight: "这是基于模拟原始数据的AI洞察示例：销售额波动主要受周末促销影响，建议在周中增加转介绍活动以平滑趋势。" })
  }

  if (afterFn.startsWith("api/v1/analytics/ai-insight-summary") && req.method === "POST") {
    return json({ insight: "AI洞察：当前期间销售节奏稳定，升级贡献占比较高。建议优化转介绍活动以提升转化率。" })
  }

  if (afterFn.startsWith("api/v1/goals/monthly") && req.method === "GET") {
    const year = Number(u.searchParams.get("year") || new Date().getFullYear())
    const month = Number(u.searchParams.get("month") || (new Date().getMonth() + 1))
    const cc_new = 300000
    const cc_ref = 100000
    const ss_total = 120000
    const goals = [
      { id: 1, identity_type: "CC", scope: "global", year, month, amount_target: cc_new + cc_ref, new_sign_target_amount: cc_new, referral_target_amount: cc_ref, renewal_total_target_amount: 0, upgrade_target_count: 8, renewal_target_count: 0, notes: null, created_at: null, updated_at: null },
      { id: 2, identity_type: "SS", scope: "global", year, month, amount_target: ss_total, new_sign_target_amount: 0, referral_target_amount: 0, renewal_total_target_amount: ss_total, upgrade_target_count: 12, renewal_target_count: 0, notes: null, created_at: null, updated_at: null }
    ]
    return json(goals)
  }

  if (afterFn.startsWith("api/v1/goals/monthly") && req.method === "POST") {
    const payload = await parseBody(req) as any
    return json({ id: Math.floor(Math.random() * 10000), ...payload })
  }

  if (afterFn.startsWith("api/v1/goals/monthly/personal") && req.method === "GET") {
    const identity_type = (u.searchParams.get("identity_type") || "").toUpperCase()
    const group_id = u.searchParams.get("group_id") || ""
    const year = u.searchParams.get("year") || ""
    const month = u.searchParams.get("month") || ""
    const user_id = u.searchParams.get("user_id") || null
    const key = `${identity_type}|${group_id}|${year}|${month}`
    const bucket = personalGoalsStore[key] || {}
    let items = Object.values(bucket)
    if (user_id) items = items.filter((it: any) => String(it.user_id) === String(user_id))
    return json({ items })
  }

  if (afterFn.startsWith("api/v1/goals/monthly/personal") && req.method === "POST") {
    const payload = await parseBody(req) as any
    const arr = Array.isArray(payload) ? payload : (payload.items || [])
    for (const it of arr) {
      const identity_type = String(it.identity_type || "").toUpperCase()
      const group_id = it.group_id ?? ""
      const year = it.year ?? ""
      const month = it.month ?? ""
      const key = `${identity_type}|${group_id}|${year}|${month}`
      if (!personalGoalsStore[key]) personalGoalsStore[key] = {}
      const userKey = String(it.user_id)
      personalGoalsStore[key][userKey] = { identity_type, group_id, user_id: it.user_id, year, month, new_sign_target_amount: Number(it.new_sign_target_amount || 0), referral_target_amount: Number(it.referral_target_amount || 0), renewal_total_target_amount: Number(it.renewal_total_target_amount || 0), upgrade_target_count: Number(it.upgrade_target_count || 0) }
    }
    return json({ success: true, saved: arr.length })
  }

  if (afterFn.startsWith("api/v1/users") && req.method === "GET") {
    const page = Number(u.searchParams.get("page") || "1")
    const size = Number(u.searchParams.get("size") || "10")
    const start = (page - 1) * size
    const items = mockUsers.slice(start, start + size)
    return json({ items, total: mockUsers.length, page, size })
  }

  if (afterFn.startsWith("api/v1/groups/") && afterFn.endsWith("/members") && req.method === "GET") {
    const parts2 = afterFn.split("/")
    const gid = parts2[3]
    const items = mockUsers.filter(m => String(m.group_id) === String(gid)).map(m => ({ id: m.id, username: m.username, identity_type: m.identity_type, group_id: m.group_id, group_name: m.group_name }))
    return json({ items, total: items.length, page: 1, size: items.length })
  }

  if (afterFn.startsWith("api/v1/groups") && req.method === "GET") {
    const uniq = new Map<string, any>()
    for (const u2 of mockUsers) {
      if (u2.group_id != null) {
        const gid = String(u2.group_id)
        if (!uniq.has(gid)) uniq.set(gid, { id: u2.group_id, name: u2.group_name, description: "", member_count: 0 })
      }
    }
    const items = Array.from(uniq.values())
    return json({ items, total: items.length, page: 1, size: items.length })
  }

  if (afterFn.startsWith("api/v1/admin/metrics") && req.method === "GET") {
    const items = [
      { id: 1, key: "period_sales_amount", name: "期间销售总额", is_active: true, default_roles: ["CC", "SS"] },
      { id: 2, key: "task_completion_rate", name: "任务完成率", is_active: true, default_roles: ["CC", "SS", "LP"] },
      { id: 3, key: "report_submission_rate", name: "日报提交率", is_active: true, default_roles: ["CC", "SS", "LP"] }
    ]
    return json(items)
  }

  if (afterFn.startsWith("api/v1/admin/metrics/") && req.method === "PUT") {
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/settings/ai") && req.method === "GET") {
    return json(aiSettingsStore)
  }

  if (afterFn.startsWith("api/v1/settings/ai") && req.method === "PUT") {
    const payload = await parseBody(req) as any
    aiSettingsStore = {
      ...aiSettingsStore,
      provider: payload.provider ?? aiSettingsStore.provider,
      api_key: payload.api_key ?? aiSettingsStore.api_key,
      base_url: payload.base_url ?? aiSettingsStore.base_url,
      model_name: payload.model_name ?? aiSettingsStore.model_name,
      max_tokens: Number(payload.max_tokens ?? aiSettingsStore.max_tokens),
      temperature: Number(payload.temperature ?? aiSettingsStore.temperature)
    }
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/settings/system") && req.method === "GET") {
    return json(systemSettingsStore)
  }

  if (afterFn.startsWith("api/v1/settings/system") && req.method === "PUT") {
    const payload = await parseBody(req) as any
    systemSettingsStore = {
      ...systemSettingsStore,
      system_name: payload.system_name ?? systemSettingsStore.system_name,
      timezone: payload.timezone ?? systemSettingsStore.timezone,
      language: payload.language ?? systemSettingsStore.language,
      auto_analysis: payload.auto_analysis ?? systemSettingsStore.auto_analysis,
      data_retention_days: Number(payload.data_retention_days ?? systemSettingsStore.data_retention_days)
    }
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/settings/ai/test") && req.method === "POST") {
    const payload = await parseBody(req) as any
    const hasKey = !!(payload.api_key || aiSettingsStore.api_key)
    const provider = (payload.provider || aiSettingsStore.provider || "").toLowerCase()
    const ok = hasKey && ["openrouter", "openai", "claude"].includes(provider)
    const responseText = ok ? "服务可用，认证通过" : "缺少有效密钥或不支持的提供商"
    return json({ success: ok, response: responseText, message: ok ? "OK" : "Failed" })
  }

  if (afterFn.startsWith("api/v1/settings/export") && req.method === "GET") {
    return json({ message: "数据导出完成（模拟）" })
  }

  if (afterFn.startsWith("api/v1/settings/clear-cache") && req.method === "POST") {
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/settings/reset") && req.method === "POST") {
    aiSettingsStore = { ...defaultAISettings }
    systemSettingsStore = { ...defaultSystemSettings }
    return json({ success: true })
  }

  return notFound()
})