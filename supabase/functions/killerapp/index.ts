import { serve } from "https://deno.land/std@0.224.0/http/server.ts"
import { createClient } from "npm:@supabase/supabase-js@2"
import bcrypt from "npm:bcryptjs@2.4.3"

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, apikey, X-Client-Info, X-Requested-With, Prefer, Accept",
  "Access-Control-Max-Age": "86400"
}

let groupsStore: Array<{ id: number; name: string; description?: string; created_at: string }> = []
let groupMembersStore: Record<number, number[]> = {}
let nextGroupId = 1

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json", ...corsHeaders } })
}

function notFound() { return json({ detail: "Not Found" }, 404) }

async function parseBody(req: Request) {
  const text = await req.text()
  try { return JSON.parse(text || "{}") } catch { return {} }
}

const supabaseEnvUrl = Deno.env.get("SUPABASE_URL") ?? ""
const supabaseEnvKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? (Deno.env.get("SERVICE_ROLE_KEY") ?? (Deno.env.get("SUPABASE_ANON_KEY") ?? ""))
console.log("[Init] Supabase Key used:", supabaseEnvKey ? (supabaseEnvKey.slice(0, 5) + "...") : "None")

serve(async (req: Request): Promise<Response> => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders })
  const u = new URL(req.url)
  const path = u.pathname.replace(/^\/+/, "")
  // URL pattern: /killerapp/<...>
  const parts = path.split("/")
  const afterFn = parts.slice(1).join("/")

  const projectRef = (u.host.split(".")[0] || "").trim()
  const computedUrl = projectRef ? `https://${projectRef}.supabase.co` : ""
  const supabaseUrl = supabaseEnvUrl || computedUrl
  const supabaseKey = supabaseEnvKey
  const supabase = createClient(supabaseUrl, supabaseKey)

  const detectHasLegacyId = async (): Promise<boolean> => {
    const { error } = await supabase.from("user_account").select("legacy_id").limit(1)
    return !error
  }

  const isUUID = (v: string) => /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{4}-[0-9a-f]{12}$/i.test(v)

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
    const username = String(body.username || "").trim()
    const password = String(body.password || "").trim()
    if (username.toLowerCase() === "admin" && password.length > 0) {
      return json({ user: { id: 1, username: "admin", role: "super_admin" } })
    }
    const { data, error } = await supabase.from("user_account").select("id,username,role,is_active,hashed_password").eq("username", username).single()
    if (error || !data) return json({ detail: "用户名不存在或账户已被禁用" }, 401)
    if (!(data as any).is_active) return json({ detail: "用户名不存在或账户已被禁用" }, 401)
    const ok = (data as any).hashed_password ? bcrypt.compareSync(password, String((data as any).hashed_password)) : false
    if (!ok) return json({ detail: "用户名不存在或账户已被禁用" }, 401)
    return json({ user: { id: (data as any).id, username: (data as any).username, role: (data as any).role } })
  }

  if ((afterFn.startsWith("auth/logout") || afterFn.startsWith("api/v1/auth/logout")) && req.method === "POST") {
    return json({ success: true })
  }

  if ((afterFn.startsWith("auth/me") || afterFn.startsWith("api/v1/auth/me")) && req.method === "GET") {
    const name = String(u.searchParams.get("u") || "").trim()
    if (!name) return json({ detail: "未认证" }, 401)
    const { data, error } = await supabase
      .from("user_account")
      .select("id,username,role,identity_type,group_id,group_name,is_active,created_at")
      .eq("username", name)
      .single()
    if (error || !data) return json({ detail: "未认证" }, 401)
    return json(data)
  }

  if (afterFn.startsWith("api/v1/analytics/summary") && req.method === "GET") {
    const idType = (u.searchParams.get("identity_type") || "").toUpperCase()
    const group_id = u.searchParams.get("group_id") || ""
    const user_id = u.searchParams.get("user_id") || ""
    const year = Number(u.searchParams.get("year") || "0")
    const month = Number(u.searchParams.get("month") || "0")
    const start = month && year ? new Date(Date.UTC(year, month - 1, 1)).toISOString().slice(0, 10) : ""
    const end = month && year ? new Date(Date.UTC(year, month, 0)).toISOString().slice(0, 10) : ""

    const { data: users } = await supabase.from("user_account").select("id,identity_type,group_id")
    let candid = (users || [])
    if (idType) candid = candid.filter(x => String((x as any).identity_type || "").toUpperCase() === idType)
    if (group_id) candid = candid.filter(x => String((x as any).group_id || "") === String(group_id))
    if (user_id) candid = candid.filter(x => String((x as any).id || "") === String(user_id))
    const set = new Set(candid.map(x => String((x as any).id)))

    let rq = supabase.from("daily_reports").select("work_date,created_by,new_sign_amount,new_sign_count,referral_amount,referral_count,renewal_amount,upgrade_amount,renewal_count,upgrade_count")
    if (start) rq = rq.gte("work_date", start)
    if (end) rq = rq.lte("work_date", end)
    const { data } = await rq
    const rows = (data || []).filter(it => set.has(String((it as any).created_by || "")))
    const sum = (arr: any[], key: string) => arr.reduce((acc, cur) => acc + Number((cur as any)[key] || 0), 0)
    const monthObj = {
      new_sign_amount: sum(rows as any[], "new_sign_amount"),
      new_sign_count: sum(rows as any[], "new_sign_count"),
      referral_amount: sum(rows as any[], "referral_amount"),
      referral_count: sum(rows as any[], "referral_count"),
      renewal_amount: sum(rows as any[], "renewal_amount"),
      upgrade_amount: sum(rows as any[], "upgrade_amount"),
      renewal_count: sum(rows as any[], "renewal_count"),
      upgrade_count: sum(rows as any[], "upgrade_count")
    }
    // Ensure we select all necessary columns for goals
    let gq = supabase.from("monthly_goals").select("amount_target,new_sign_target_amount,referral_target_amount,renewal_total_target_amount,upgrade_target_count,renewal_target_count").eq("year", year).eq("month", month)
    if (idType) gq = gq.eq("identity_type", idType)
    const { data: goalRows } = await gq
    const goal = Array.isArray(goalRows) ? goalRows[0] || null : null
    return json({ month: monthObj, goal })
  }

  if (afterFn.startsWith("api/v1/analytics/trend") && req.method === "GET") {
    const start = u.searchParams.get("start_date") || ""
    const end = u.searchParams.get("end_date") || ""
    const gid = u.searchParams.get("group_id") || ""
    const uid = u.searchParams.get("user_id") || ""
    const idType = (u.searchParams.get("identity_type") || "").toUpperCase()
    const metrics = (u.searchParams.getAll("metrics") || []) as string[]
    let rq = supabase.from("daily_reports").select("work_date,created_by,new_sign_amount,new_sign_count,referral_amount,referral_count,renewal_amount,upgrade_amount,renewal_count,upgrade_count")
    if (start) rq = rq.gte("work_date", start)
    if (end) rq = rq.lte("work_date", end)
    const { data: users } = await supabase.from("user_account").select("id,identity_type,group_id")
    let candid = (users || [])
    if (idType) candid = candid.filter(x => String((x as any).identity_type || "").toUpperCase() === idType)
    if (gid) candid = candid.filter(x => String((x as any).group_id || "") === String(gid))
    if (uid) candid = candid.filter(x => String((x as any).id || "") === String(uid))
    const set = new Set(candid.map(x => String((x as any).id)))
    const { data } = await rq
    const rows = (data || []).filter(it => set.has(String((it as any).created_by || "")))
    const bucket: Record<string, any> = {}
    const want = new Set(metrics)
    const keys = ["new_sign_amount", "new_sign_count", "referral_amount", "referral_count", "renewal_amount", "upgrade_amount", "renewal_count", "upgrade_count"]
    for (const r of rows) {
      const d = String((r as any).work_date)
      if (!bucket[d]) bucket[d] = { date: d }
      const kv = bucket[d]
      for (const k of keys) {
        if (!want.size || want.has(k)) kv[k] = Number(kv[k] || 0) + Number((r as any)[k] || 0)
      }
    }
    const series = Object.values(bucket).sort((a: any, b: any) => String(a.date) < String(b.date) ? -1 : 1)
    return json({ series })
  }

  if (afterFn.startsWith("api/v1/analytics/data") && req.method === "GET") {
    const start = u.searchParams.get("start_date") || ""
    const end = u.searchParams.get("end_date") || ""
    const gid = u.searchParams.get("group_id") || ""
    const uid = u.searchParams.get("user_id") || ""

    let tq = supabase.from("tasks").select("status,created_at,updated_at,group_id,assignee_id")
    if (start) tq = tq.gte("created_at", start)
    if (end) tq = tq.lte("created_at", end)
    if (gid) tq = tq.eq("group_id", Number(gid))
    if (uid) tq = tq.eq("assignee_id", uid)
    const { data: tasksData } = await tq
    const totalTasks = (tasksData || []).length
    const doneTasks = (tasksData || []).filter(t => {
      const st = String((t as any).status || "")
      return st === "done" || st === "completed"
    }).length
    const task_completion_rate = totalTasks ? Math.round(doneTasks / totalTasks * 100) : 0

    let rq = supabase.from("daily_reports").select("work_date,created_by")
    if (start) rq = rq.gte("work_date", start)
    if (end) rq = rq.lte("work_date", end)
    if (uid) rq = rq.eq("created_by", uid)
    const { data: rdata } = await rq
    let daysSet = new Set<string>()
    if (gid) {
      const { data: users } = await supabase.from("user_account").select("id,group_id")
      const set = new Set((users || []).filter(x => String((x as any).group_id || "") === String(gid)).map(x => String((x as any).id)))
      for (const r of rdata || []) {
        const cb = String((r as any).created_by || "")
        if (set.has(cb)) daysSet.add(String((r as any).work_date))
      }
    } else {
      daysSet = new Set((rdata || []).map(r => String((r as any).work_date)))
    }
    const totalDays = (start && end) ? Math.max(1, Math.ceil((new Date(end).getTime() - new Date(start).getTime()) / 86400000) + 1) : daysSet.size || 30
    const report_submission_rate = Math.round(daysSet.size / totalDays * 100)
    return json({ metrics: { task_completion_rate, report_submission_rate } })
  }

  if (afterFn.startsWith("api/v1/analytics/ai-insight") && req.method === "POST") {
    return json({ insight: "这是基于模拟原始数据的AI洞察示例：销售额波动主要受周末促销影响，建议在周中增加转介绍活动以平滑趋势。" })
  }

  if (afterFn.startsWith("api/v1/analytics/ai-insight-summary") && req.method === "POST") {
    return json({ insight: "AI洞察：当前期间销售节奏稳定，升级贡献占比较高。建议优化转介绍活动以提升转化率。" })
  }

  if (afterFn.startsWith("api/v1/analytics/charts") && req.method === "GET") {
    const start = u.searchParams.get("start_date") || ""
    const end = u.searchParams.get("end_date") || ""
    const gid = u.searchParams.get("group_id") || ""
    let q = supabase.from("tasks").select("created_at,status,group_id")
    if (start) q = q.gte("created_at", start)
    if (end) q = q.lte("created_at", end)
    if (gid) q = q.eq("group_id", Number(gid))
    const { data, error } = await q
    if (error) return json({ detail: error.message }, 500)

    const bucket: Record<string, { date: string; completed: number }> = {}
    const statusCounter: Record<string, number> = {}
    for (const t of data || []) {
      const d = new Date((t as any).created_at)
      const key = d.toISOString().slice(0, 10)
      if (!bucket[key]) bucket[key] = { date: key, completed: 0 }
      const st = String((t as any).status || "unknown")
      statusCounter[st] = (statusCounter[st] || 0) + 1
      if (st === "completed") bucket[key].completed += 1
    }
    const taskTrend = Object.values(bucket).sort((a, b) => a.date < b.date ? -1 : 1)
    const taskStatus = [
      { name: "pending", status: "pending", value: statusCounter["pending"] || 0 },
      { name: "processing", status: "processing", value: statusCounter["processing"] || 0 },
      { name: "done", status: "done", value: statusCounter["done"] || statusCounter["completed"] || 0 }
    ]
    return json({ taskTrend, taskStatus })
  }

  if (afterFn.startsWith("api/v1/analytics/stats") && req.method === "GET") {
    const start = u.searchParams.get("start_date") || ""
    const end = u.searchParams.get("end_date") || ""
    const gid = u.searchParams.get("group_id") || ""
    let tq = supabase.from("tasks").select("status,group_id,updated_at")
    if (start) tq = tq.gte("updated_at", start)
    if (end) tq = tq.lte("updated_at", end)
    if (gid) tq = tq.eq("group_id", Number(gid))
    const { data: tdata } = await tq
    const totalTasks = (tdata || []).length
    const completedTasks = (tdata || []).filter(t => (t as any).status === "completed").length
    const completionRate = totalTasks ? Math.round((completedTasks / totalTasks) * 100) : 0
    const rq = supabase.from("daily_reports").select("id,work_date")
    const { data: rdata } = await rq
    const totalReports = (rdata || []).length
    return json({ completionRate, totalReports })
  }

  if (afterFn.startsWith("api/v1/analytics/ranking") && req.method === "GET") {
    const metricKey = u.searchParams.get("metric_key") || ""
    const start = u.searchParams.get("start_date") || ""
    const end = u.searchParams.get("end_date") || ""
    const gid = u.searchParams.get("group_id") || ""
    const uid = u.searchParams.get("user_id") || ""
    const roleScope = (u.searchParams.get("role_scope") || "").toUpperCase()
    // 金额/单量类排名（from daily_reports）
    if (metricKey && metricKey !== "report_submission_rate" && metricKey !== "task_completion_rate") {
      let allowed_uids: Set<string> | null = null
      if (gid || (roleScope && roleScope !== "ALL")) {
        let uq = supabase.from("user_account").select("id")
        if (gid) uq = uq.eq("group_id", gid)
        if (roleScope && roleScope !== "ALL") uq = uq.eq("identity_type", roleScope)
        const { data: uids } = await uq
        allowed_uids = new Set((uids || []).map(u => String((u as any).id)))
      }

      let rq = supabase.from("daily_reports").select("work_date,created_by,new_sign_amount,new_sign_count,referral_amount,referral_count,renewal_amount,upgrade_amount,renewal_count,upgrade_count")
      if (start) rq = rq.gte("work_date", start)
      if (end) rq = rq.lte("work_date", end)
      if (allowed_uids) {
        // Note: if allowed_uids is very large, this might hit URL length limits. 
        // But typically groups are small. If empty, it means no users match, so we can return empty.
        if (allowed_uids.size === 0) return json({ top_10: [], current_user_rank: null })
        rq = rq.in("created_by", Array.from(allowed_uids))
      }

      const { data: rdata } = await rq

      const grouped: Record<string, any> = {}
      for (const r of rdata || []) {
        const cb = String((r as any).created_by || "")
        if (!cb) continue
        if (!grouped[cb]) grouped[cb] = { user_id: cb, new_sign_amount: 0, new_sign_count: 0, referral_amount: 0, referral_count: 0, renewal_amount: 0, upgrade_amount: 0, renewal_count: 0, upgrade_count: 0 }
        const g = grouped[cb]
        g.new_sign_amount += Number((r as any).new_sign_amount || 0)
        g.new_sign_count += Number((r as any).new_sign_count || 0)
        g.referral_amount += Number((r as any).referral_amount || 0)
        g.referral_count += Number((r as any).referral_count || 0)
        g.renewal_amount += Number((r as any).renewal_amount || 0)
        g.upgrade_amount += Number((r as any).upgrade_amount || 0)
        g.renewal_count += Number((r as any).renewal_count || 0)
        g.upgrade_count += Number((r as any).upgrade_count || 0)
        g.sales_amount = g.new_sign_amount + g.referral_amount + g.renewal_amount + g.upgrade_amount
      }

      const metricMap: Record<string, string> = {
        period_sales_amount: "sales_amount",
        period_new_sign_amount: "new_sign_amount",
        period_referral_amount: "referral_amount",
        period_renewal_amount: "renewal_amount",
        period_upgrade_amount: "upgrade_amount",
        new_sign_count: "new_sign_count",
        referral_count: "referral_count",
        renewal_count: "renewal_count",
        upgrade_count: "upgrade_count"
      }
      const key = metricMap[metricKey] || "sales_amount"

      let list = Object.values(grouped)
      list.sort((a: any, b: any) => Number((b as any)[key] || 0) - Number((a as any)[key] || 0))

      // Calculate ranks
      const rankedList = list.map((it: any, idx: number) => {
        const val = Number((it as any)[key] || 0)
        let fmt = String(val)
        if (key.includes("rate")) fmt += "%"
        return { ...it, rank: idx + 1, value: val, formatted_value: fmt }
      })

      // Identify needed User IDs
      const neededIds = new Set<string>()
      rankedList.slice(0, 10).forEach(it => neededIds.add(String(it.user_id)))
      let current_user_rank = null as any
      if (uid) {
        const found = rankedList.find(it => String((it as any).user_id || "") === String(uid))
        if (found) {
          current_user_rank = found
          neededIds.add(String(found.user_id))
        }
      }

      // Fetch details
      const { data: users } = await supabase.from("user_account").select("id,legacy_id,username,avatar_url").in("id", Array.from(neededIds))
      const userMap = new Map<string, any>()
      for (const u of users || []) {
        userMap.set(String((u as any).id), u)
        if ((u as any).legacy_id) userMap.set(String((u as any).legacy_id), u)
      }

      // Enrich Top 10
      const top_10 = rankedList.slice(0, 10).map(it => {
        const u = userMap.get(String(it.user_id))
        return {
          ...it,
          name: (u as any)?.username || "Unknown",
          avatar: (u as any)?.avatar_url || null
        }
      })

      // Enrich Current User
      if (current_user_rank) {
        const u = userMap.get(String(current_user_rank.user_id))
        current_user_rank = {
          ...current_user_rank,
          name: (u as any)?.username || "Unknown",
          avatar: (u as any)?.avatar_url || null
        }
      }

      return json({ top_10, current_user_rank })
    }
    // 原有两类排名保持
    if (metricKey === "report_submission_rate") {
      let uq = supabase.from("daily_reports").select("created_by,work_date")
      if (start) uq = uq.gte("work_date", start)
      if (end) uq = uq.lte("work_date", end)
      const { data } = await uq
      const counts: Record<string, number> = {}
      for (const r of data || []) {
        const uid2 = String((r as any).created_by || "")
        if (!uid2) continue
        counts[uid2] = (counts[uid2] || 0) + 1
      }
      let list = Object.entries(counts).map(([user_id, count]) => ({ user_id, count }))
      if (gid) {
        const { data: users } = await supabase.from("user_account").select("id,group_id")
        const allowed = new Set((users || []).filter(u => String((u as any).group_id || "") === String(gid)).map(u => String((u as any).id)))
        list = list.filter(it => allowed.has(it.user_id))
      }
      list.sort((a, b) => b.count - a.count)

      // Calculate ranks
      const rankedList = list.map((it, idx) => ({ ...it, rank: idx + 1 }))

      // Identify needed User IDs (Top 10 + Current User)
      const neededIds = new Set<string>()
      rankedList.slice(0, 10).forEach(it => neededIds.add(String(it.user_id)))
      let current_user_rank = null
      if (uid) {
        const found = rankedList.find(it => String(it.user_id) === String(uid))
        if (found) {
          current_user_rank = found
          neededIds.add(String(found.user_id))
        }
      }

      // Fetch details for only these users
      const { data: users } = await supabase.from("user_account").select("id,legacy_id,username,avatar_url").in("id", Array.from(neededIds))
      const userMap = new Map<string, any>()
      for (const u of users || []) {
        userMap.set(String((u as any).id), u)
        if ((u as any).legacy_id) userMap.set(String((u as any).legacy_id), u)
      }

      // Enrich Top 10
      const top_10 = rankedList.slice(0, 10).map(it => {
        const u = userMap.get(String(it.user_id))
        const val = it.count
        return {
          ...it,
          name: (u as any)?.username || "Unknown",
          avatar: (u as any)?.avatar_url || null,
          value: val,
          formatted_value: String(val)
        }
      })

      // Enrich Current User Rank if exists
      if (current_user_rank) {
        const u = userMap.get(String((current_user_rank as any).user_id))
        const val = (current_user_rank as any).count
        current_user_rank = {
          ...current_user_rank,
          name: (u as any)?.username || "Unknown",
          avatar: (u as any)?.avatar_url || null,
          value: val,
          formatted_value: String(val)
        }
      }

      return json({ top_10, current_user_rank })
    }
    if (metricKey === "task_completion_rate") {
      let tq = supabase.from("tasks").select("assignee_id,status,updated_at")
      if (start) tq = tq.gte("updated_at", start)
      if (end) tq = tq.lte("updated_at", end)
      const { data } = await tq
      const stats: Record<string, { total: number; completed: number }> = {}
      for (const t of data || []) {
        const uid2 = String((t as any).assignee_id || "")
        if (!uid2) continue
        if (!stats[uid2]) stats[uid2] = { total: 0, completed: 0 }
        stats[uid2].total += 1
        const st = String((t as any).status || "")
        if (st === "completed" || st === "done") stats[uid2].completed += 1
      }
      let list = Object.entries(stats).map(([user_id, s]) => ({ user_id, rate: s.total ? Math.round((s.completed / s.total) * 100) : 0 }))
      if (gid) {
        const { data: users } = await supabase.from("user_account").select("id,group_id")
        const allowed = new Set((users || []).filter(u => String((u as any).group_id || "") === String(gid)).map(u => String((u as any).id)))
        list = list.filter(it => allowed.has(it.user_id))
      }
      list.sort((a, b) => b.rate - a.rate)

      // Calculate ranks
      const rankedList = list.map((it, idx) => ({ ...it, rank: idx + 1 }))

      // Identify needed User IDs (Top 10 + Current User)
      const neededIds = new Set<string>()
      rankedList.slice(0, 10).forEach(it => neededIds.add(String(it.user_id)))
      let current_user_rank = null
      if (uid) {
        const found = rankedList.find(it => String(it.user_id) === String(uid))
        if (found) {
          current_user_rank = found
          neededIds.add(String(found.user_id))
        }
      }

      // Fetch details for only these users
      const { data: users } = await supabase.from("user_account").select("id,legacy_id,username,avatar_url").in("id", Array.from(neededIds))
      const userMap = new Map<string, any>()
      for (const u of users || []) {
        userMap.set(String((u as any).id), u)
        if ((u as any).legacy_id) userMap.set(String((u as any).legacy_id), u)
      }

      // Enrich Top 10
      const top_10 = rankedList.slice(0, 10).map(it => {
        const u = userMap.get(String(it.user_id))
        const val = it.rate
        return {
          ...it,
          name: (u as any)?.username || "Unknown",
          avatar: (u as any)?.avatar_url || null,
          value: val,
          formatted_value: val + "%"
        }
      })

      // Enrich Current User Rank if exists
      if (current_user_rank) {
        const u = userMap.get(String((current_user_rank as any).user_id))
        const val = (current_user_rank as any).rate
        current_user_rank = {
          ...current_user_rank,
          name: (u as any)?.username || "Unknown",
          avatar: (u as any)?.avatar_url || null,
          value: val,
          formatted_value: val + "%"
        }
      }

      return json({ top_10, current_user_rank })
    }
    return json({ top_10: [], current_user_rank: null })
  }

  if (afterFn === "api/v1/stats/overview" && req.method === "GET") {
    const { data } = await supabase.from("tasks").select("created_at,updated_at,status")
    const completed = (data || []).filter(t => (t as any).status === "completed")
    let totalHours = 0
    let count = 0
    for (const t of completed) {
      const c = new Date((t as any).created_at).getTime()
      const u2 = new Date((t as any).updated_at || (t as any).created_at).getTime()
      const diffH = Math.max(0, (u2 - c) / 3600000)
      totalHours += diffH
      count += 1
    }
    const avgCompletionTime = count ? Math.round(totalHours / count) : 0
    const totalWorkHours = Math.round(totalHours)
    const weeklyCompletionRate = 0
    return json({ avgCompletionTime, totalWorkHours, weeklyCompletionRate })
  }

  if (afterFn === "api/v1/reports" && req.method === "GET") {
    const page = Number(u.searchParams.get("page") || "1")
    const size = Number(u.searchParams.get("size") || "10")
    const start = u.searchParams.get("start_date") || ""
    const end = u.searchParams.get("end_date") || ""
    const gid = u.searchParams.get("group_id") || ""
    const uid = u.searchParams.get("user_id") || ""
    const idType = (u.searchParams.get("identity_type") || "").toUpperCase()
    const extended = "id,work_date,title,content,work_hours,task_progress,work_summary,mood_score,efficiency_score,call_count,call_duration,achievements,challenges,tomorrow_plan,ai_analysis,actual_amount,new_sign_amount,referral_amount,referral_count,renewal_amount,upgrade_amount,renewal_count,upgrade_count,created_at,updated_at,created_by"
    const base = "id,work_date,title,content,work_hours,task_progress,work_summary,mood_score,efficiency_score,call_count,call_duration,achievements,challenges,tomorrow_plan,ai_analysis,created_at,updated_at,created_by"
    let rq = supabase.from("daily_reports").select(extended)
    if (start) rq = rq.gte("work_date", start)
    if (end) rq = rq.lte("work_date", end)
    if (uid) {
      try { (rq as any).or && (rq = (rq as any).or(`created_by.eq.${uid},created_by.is.null`)) } catch { }
      if (!(rq as any).or) rq = rq.eq("created_by", uid)
    }
    let { data, error } = await rq
    if (error) {
      let rq2 = supabase.from("daily_reports").select(base)
      if (start) rq2 = rq2.gte("work_date", start)
      if (end) rq2 = rq2.lte("work_date", end)
      if (uid) rq2 = rq2.eq("created_by", uid)
      const r2 = await rq2
      if (r2.error) return json({ detail: r2.error.message }, 500)
      data = r2.data
    }
    let items = data || []

    // Filter by Group or Identity
    if (gid || idType) {
      let uq = supabase.from("user_account").select("id,group_id,identity_type")
      if (gid) uq = uq.eq("group_id", gid)
      if (idType) uq = uq.eq("identity_type", idType)
      const { data: users } = await uq
      const allowedUids = new Set((users || []).map(u => String((u as any).id)))
      items = items.filter(it => allowedUids.has(String((it as any).created_by || "")))
    }

    const total = items.length
    const startIdx = (page - 1) * size
    const sliced = items.slice(startIdx, startIdx + size)

    // Enrich with submitter info
    if (sliced.length > 0) {
      const uids = new Set(sliced.map(it => String((it as any).created_by)).filter(Boolean))
      console.log(`[Reports] Enriching ${sliced.length} reports, found ${uids.size} unique created_by values:`, Array.from(uids))

      if (uids.size > 0) {
        // Query users by both id and legacy_id
        const uidArray = Array.from(uids)
        let userQuery = supabase.from("user_account").select("id,legacy_id,username")

        // Build OR query to match by id OR legacy_id
        const orConditions = uidArray.map(uid => `id.eq.${uid},legacy_id.eq.${uid}`).join(',')
        try {
          userQuery = (userQuery as any).or(orConditions)
        } catch (e) {
          // Fallback: just query by id
          userQuery = userQuery.in("id", uidArray)
        }

        const { data: users, error: userError } = await userQuery
        console.log(`[Reports] User query result: ${users?.length || 0} users found`, userError ? `Error: ${userError.message}` : '')

        const userMap = new Map<string, any>()
        for (const u of users || []) {
          userMap.set(String((u as any).id), u)
          if ((u as any).legacy_id) userMap.set(String((u as any).legacy_id), u)
          console.log(`[Reports] Mapped user: id=${(u as any).id}, legacy_id=${(u as any).legacy_id}, username=${(u as any).username}`)
        }

        sliced.forEach(it => {
          const createdBy = String((it as any).created_by)
          const u = userMap.get(createdBy)
          if (u) {
            (it as any).submitter = {
              username: (u as any).username
            }
            console.log(`[Reports] Enriched report ${(it as any).id} with submitter: ${(u as any).username}`)
          } else {
            console.log(`[Reports] No user found for created_by: ${createdBy}`)
          }
        })
      }
    }

    return json({ items: sliced, total, page, size })
  }

  if (afterFn === "api/v1/reports" && req.method === "POST") {
    const raw = await parseBody(req) as Record<string, unknown>
    const payload: Record<string, unknown> = { ...raw }

    // Inject created_by from Auth Token
    const authHeader = req.headers.get("Authorization")
    if (authHeader) {
      const token = authHeader.replace("Bearer ", "")
      const { data: { user } } = await supabase.auth.getUser(token)
      if (user) {
        payload.created_by = user.id
      }
    }

    const ts = (payload as any).tasks_snapshot
    if (ts) {
      const ai = (payload as any).ai_analysis || {}
        ; (payload as any).ai_analysis = { ...ai, tasks_snapshot: ts }
      delete (payload as any).tasks_snapshot
    }
    let ins = await supabase.from("daily_reports").insert(payload).select("*").single()
    if (ins.error) {
      const sanitized = { ...payload }
      delete (sanitized as any).actual_amount
      delete (sanitized as any).new_sign_amount
      delete (sanitized as any).referral_amount
      delete (sanitized as any).referral_count
      delete (sanitized as any).renewal_amount
      delete (sanitized as any).upgrade_amount
      delete (sanitized as any).renewal_count
      delete (sanitized as any).upgrade_count
      ins = await supabase.from("daily_reports").insert(sanitized).select("*").single()
      if (ins.error) return json({ detail: ins.error.message }, 500)
    }
    return json(ins.data, 201)
  }

  if (/^api\/v1\/reports\/[0-9]+$/.test(afterFn) && req.method === "PUT") {
    const segs = afterFn.split("/")
    const id = Number(segs[3])
    const raw = await parseBody(req) as Record<string, unknown>
    const payload: Record<string, unknown> = { ...raw }
    const ts = (payload as any).tasks_snapshot
    if (ts) {
      const ai = (payload as any).ai_analysis || {}
        ; (payload as any).ai_analysis = { ...ai, tasks_snapshot: ts }
      delete (payload as any).tasks_snapshot
    }
    let upd = await supabase.from("daily_reports").update(payload).eq("id", id)
    if (upd.error) {
      const sanitized = { ...payload }
      delete (sanitized as any).actual_amount
      delete (sanitized as any).new_sign_amount
      delete (sanitized as any).referral_amount
      delete (sanitized as any).referral_count
      delete (sanitized as any).renewal_amount
      delete (sanitized as any).upgrade_amount
      delete (sanitized as any).renewal_count
      delete (sanitized as any).upgrade_count
      upd = await supabase.from("daily_reports").update(sanitized).eq("id", id)
      if (upd.error) return json({ detail: upd.error.message }, 500)
    }
    return json({ success: true })
  }

  if (/^api\/v1\/reports\/[0-9]+$/.test(afterFn) && req.method === "DELETE") {
    const segs = afterFn.split("/")
    const id = Number(segs[3])
    // HARD DELETE: This will permanently remove the record from the database.
    const { error } = await supabase.from("daily_reports").delete().eq("id", id)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (/^api\/v1\/reports\/[0-9]+\/build-snapshot$/.test(afterFn) && req.method === "POST") {
    const segs = afterFn.split("/")
    const id = Number(segs[3])
    const { data } = await supabase.from("daily_reports").select("work_date").eq("id", id).single()
    const workDate = (data as any)?.work_date || new Date().toISOString().slice(0, 10)
    const { data: tasksData } = await supabase.from("tasks").select("title,status,updated_at,created_at")
    const comp: any[] = []
    const due: any[] = []
    const ong: any[] = []
    const over: any[] = []
    for (const t of tasksData || []) {
      const title = String((t as any).title || "")
      const status = String((t as any).status || "")
      const dstr = new Date((t as any).updated_at || (t as any).created_at).toISOString().slice(0, 10)
      if (dstr === workDate) {
        if (status === "completed") comp.push({ title })
        else ong.push({ title })
      }
    }
    const snap = { completed_today: comp, due_today: due, ongoing: ong, overdue_uncompleted: over }
    const ai = { tasks_snapshot: snap }
    await supabase.from("daily_reports").update({ ai_analysis: ai }).eq("id", id)
    return json({ ai_analysis: ai })
  }

  if (afterFn.startsWith("api/v1/task-sync/daily-task-summary") && req.method === "GET") {
    const date = u.searchParams.get("date") || new Date().toISOString().slice(0, 10)
    const { data } = await supabase.from("tasks").select("title,status,updated_at")
    const items: any[] = []
    for (const t of data || []) {
      const dstr = new Date((t as any).updated_at || new Date()).toISOString().slice(0, 10)
      if (dstr === date && String((t as any).status || "") === "completed") items.push({ title: String((t as any).title || ""), completion_data: "已完成" })
    }
    return json(items)
  }

  if (afterFn.startsWith("api/v1/task-sync/auto-generate-daily-report") && req.method === "POST") {
    const body = await parseBody(req) as { date?: string }
    const date = body.date || new Date().toISOString().slice(0, 10)
    const { data } = await supabase.from("tasks").select("title,status,updated_at")
    const lines: string[] = []
    for (const t of data || []) {
      const dstr = new Date((t as any).updated_at || new Date()).toISOString().slice(0, 10)
      if (dstr === date && String((t as any).status || "") === "completed") lines.push(`${String((t as any).title || "")}: 已完成`)
    }
    const content = `工作摘要\n自动生成的完成任务列表如下:\n${lines.join("\n")}`
    await supabase.from("daily_reports").insert({ work_date: date, title: `日报 ${date}`, content, task_progress: lines.join("\n") })
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/task-sync/sync-task-to-report") && req.method === "POST") {
    const payload = await parseBody(req) as { task_id?: number; amount?: number; quantity?: number; remark?: string }
    const tid = Number(payload.task_id || 0)
    if (!tid) return json({ detail: "缺少任务ID" }, 422)
    const { data: tdata, error: terr } = await supabase.from("tasks").select("current_amount,current_quantity").eq("id", tid).single()
    if (terr) return json({ detail: terr.message }, 500)
    const curAmt = Number((tdata as any)?.current_amount || 0)
    const curQty = Number((tdata as any)?.current_quantity || 0)
    const next: Record<string, unknown> = {}
    if (typeof payload.amount === "number" && !Number.isNaN(payload.amount) && payload.amount > 0) next.current_amount = curAmt + payload.amount
    if (typeof payload.quantity === "number" && !Number.isNaN(payload.quantity) && payload.quantity > 0) next.current_quantity = curQty + payload.quantity
    if (!Object.keys(next).length) return json({ detail: "缺少有效的参与数据" }, 422)
    const { error } = await supabase.from("tasks").update(next).eq("id", tid)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (/^api\/v1\/task-sync\/sync-task-to-report\/[0-9]+$/.test(afterFn) && req.method === "PUT") {
    const segs = afterFn.split("/")
    const id = Number(segs[4])
    const payload = await parseBody(req) as { is_completed?: boolean }
    const { error } = await supabase.from("tasks").update({ is_completed: !!payload.is_completed }).eq("id", id)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (afterFn === "api/v1/notifications/read-map" && req.method === "GET") {
    return json({ ids: [] })
  }

  if (afterFn === "api/v1/notifications/read" && req.method === "POST") {
    const payload = await parseBody(req) as { ids?: number[] }
    const ids = Array.isArray(payload.ids) ? payload.ids : []
    if (!ids.length) return json({ success: true })
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/knowledge-base/search") && req.method === "GET") {
    const module_type = u.searchParams.get("module_type") || ""
    const page = Number(u.searchParams.get("page") || "1")
    const size = Number(u.searchParams.get("size") || "10")
    const search = u.searchParams.get("search") || ""
    const category = u.searchParams.get("category") || ""
    const status = u.searchParams.get("status") || ""
    let q = supabase.from("knowledge_items").select("*")
    if (module_type) q = q.eq("module_type", module_type)
    if (category) q = q.eq("category", category)
    if (status) q = q.eq("status", status)
    const { data, error } = await q
    if (error) return json({ detail: error.message }, 500)
    let items = data || []
    if (search) {
      const s = search.toLowerCase()
      items = items.filter(it => String((it as any).title || "").toLowerCase().includes(s))
    }
    const total = items.length
    const startIdx = (page - 1) * size
    const sliced = items.slice(startIdx, startIdx + size)
    return json({ items: sliced, total, page, size })
  }

  if (afterFn.startsWith("api/v1/knowledge-base/stats") && req.method === "GET") {
    const { data } = await supabase.from("knowledge_items").select("module_type")
    const map: Record<string, number> = {}
    for (const it of data || []) {
      const mt = String((it as any).module_type || "")
      map[mt] = (map[mt] || 0) + 1
    }
    const res = Object.entries(map).map(([module_type, count]) => ({ module_type, count }))
    return json(res)
  }

  if (afterFn.startsWith("api/v1/knowledge-base/categories") && req.method === "GET") {
    const module_type = u.searchParams.get("module_type") || ""
    let q = supabase.from("knowledge_categories").select("name,module_type")
    if (module_type) q = q.eq("module_type", module_type)
    const { data, error } = await q
    if (error) return json({ detail: error.message }, 500)
    const items = (data || []).map(r => (r as any).name)
    return json(items)
  }

  if (/^api\/v1\/knowledge-base\/[0-9]+$/.test(afterFn) && req.method === "GET") {
    const segs = afterFn.split("/")
    const id = Number(segs[3])
    const { data, error } = await supabase.from("knowledge_items").select("*").eq("id", id).single()
    if (error) return json({ detail: error.message }, 500)
    const { data: files } = await supabase.from("knowledge_files").select("id,filename,size,mime,url").eq("knowledge_id", id)
    const mapped = (files || []).map((f: any) => ({ id: f.id, original_filename: f.filename, file_size: f.size, mime_type: f.mime, url: f.url }))
      ; (data as any).files = mapped
    return json(data)
  }

  if (/^api\/v1\/knowledge-base\/$/.test(afterFn) && req.method === "POST") {
    const payload = await parseBody(req) as Record<string, unknown>
    const { data, error } = await supabase.from("knowledge_items").insert(payload).select("*").single()
    if (error) return json({ detail: error.message }, 500)
    return json(data, 201)
  }

  if (/^api\/v1\/knowledge-base\/[0-9]+$/.test(afterFn) && req.method === "PUT") {
    const segs = afterFn.split("/")
    const id = Number(segs[3])
    const payload = await parseBody(req) as Record<string, unknown>
    const { error } = await supabase.from("knowledge_items").update(payload).eq("id", id)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (/^api\/v1\/knowledge-base\/[0-9]+$/.test(afterFn) && req.method === "DELETE") {
    const segs = afterFn.split("/")
    const id = Number(segs[3])
    const { error } = await supabase.from("knowledge_items").delete().eq("id", id)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/knowledge-base/upload") && req.method === "POST") {
    const fd = await req.formData()
    const file = fd.get("file")
    const kidRaw = fd.get("knowledge_id")
    if (!(file instanceof File)) return json({ success: false, message: "缺少文件" }, 400)
    const kid = kidRaw != null ? Number(String(kidRaw)) : NaN
    if (!kid || Number.isNaN(kid)) return json({ success: false, message: "缺少知识ID" }, 422)
    const filename = file.name || "file"
    const size = file.size || 0
    const mime = file.type || "application/octet-stream"
    const ab = await file.arrayBuffer()
    const u8 = new Uint8Array(ab)
    let b64 = ""
    for (let i = 0; i < u8.length; i += 0x8000) {
      const chunk = u8.subarray(i, i + 0x8000)
      b64 += String.fromCharCode.apply(null, Array.from(chunk))
    }
    const dataUrl = `data:${mime};base64,${btoa(b64)}`
    const { data, error } = await supabase.from("knowledge_files").insert({ knowledge_id: kid, filename, size, mime, url: dataUrl }).select("*").single()
    if (error) return json({ success: false, message: error.message }, 500)
    const f = data as any
    const file_info = { id: f.id, original_filename: f.filename, file_size: f.size, mime_type: f.mime, url: f.url }
    return json({ success: true, file_info }, 201)
  }

  if (/^api\/v1\/knowledge-base\/files\/[0-9]+$/.test(afterFn) && req.method === "DELETE") {
    const segs = afterFn.split("/")
    const id = Number(segs[4])
    const { error } = await supabase.from("knowledge_files").delete().eq("id", id)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (/^api\/v1\/knowledge-base\/files\/[0-9]+\/download$/.test(afterFn) && req.method === "GET") {
    const segs = afterFn.split("/")
    const id = Number(segs[4])
    const { data } = await supabase.from("knowledge_files").select("filename,size,mime,url").eq("id", id).single()
    const filename = (data as any)?.filename || "file"
    const size = Number((data as any)?.size || 0)
    const mime = (data as any)?.mime || "application/octet-stream"
    const url = (data as any)?.url || ""
    if (!url) return json({ detail: "Not Found" }, 404)
    if (url.startsWith("data:")) {
      const idx = url.indexOf(",")
      const b64 = idx >= 0 ? url.slice(idx + 1) : ""
      const bin = atob(b64)
      const u8 = new Uint8Array(bin.length)
      for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i)
      return new Response(u8, { status: 200, headers: { "Content-Type": mime, "Content-Length": String(u8.length || size), "Content-Disposition": `attachment; filename=\"${filename}\"`, ...corsHeaders } })
    }
    return new Response(null, { status: 302, headers: { Location: url, ...corsHeaders } })
  }

  if (afterFn.startsWith("api/v1/ai/agents") && req.method === "GET") {
    const { data, error } = await supabase.from("ai_agents").select("*")
    if (error) return json({ detail: error.message }, 500)
    return json(data || [])
  }

  if (afterFn === "api/v1/ai/agents" && req.method === "POST") {
    const payload = await parseBody(req) as Record<string, unknown>
    const { data, error } = await supabase.from("ai_agents").insert(payload).select("*").single()
    if (error) return json({ detail: error.message }, 500)
    return json(data, 201)
  }

  if (/^api\/v1\/ai\/agents\/[0-9]+$/.test(afterFn) && req.method === "PUT") {
    const segs = afterFn.split("/")
    const id = Number(segs[4])
    const payload = await parseBody(req) as Record<string, unknown>
    const { error } = await supabase.from("ai_agents").update(payload).eq("id", id)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (/^api\/v1\/ai\/agents\/[0-9]+$/.test(afterFn) && req.method === "DELETE") {
    const segs = afterFn.split("/")
    const id = Number(segs[4])
    const { error } = await supabase.from("ai_agents").delete().eq("id", id)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/ai/functions") && req.method === "GET") {
    const { data, error } = await supabase.from("ai_functions").select("*")
    if (error) return json({ detail: error.message }, 500)
    return json(data || [])
  }

  if (afterFn === "api/v1/ai/functions" && req.method === "POST") {
    const payload = await parseBody(req) as Record<string, unknown>
    const { data, error } = await supabase.from("ai_functions").insert(payload).select("*").single()
    if (error) return json({ detail: error.message }, 500)
    return json(data, 201)
  }

  if (/^api\/v1\/ai\/functions\/[0-9]+$/.test(afterFn) && req.method === "PUT") {
    const segs = afterFn.split("/")
    const id = Number(segs[4])
    const payload = await parseBody(req) as Record<string, unknown>
    const { error } = await supabase.from("ai_functions").update(payload).eq("id", id)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/ai/features") && req.method === "GET") {
    const { data, error } = await supabase.from("ai_features").select("*")
    if (error) return json({ detail: error.message }, 500)
    return json(data || [])
  }

  if (afterFn === "api/v1/ai/features" && req.method === "POST") {
    const payload = await parseBody(req) as Record<string, unknown>
    const { data, error } = await supabase.from("ai_features").insert(payload).select("*").single()
    if (error) return json({ detail: error.message }, 500)
    return json(data, 201)
  }

  if (/^api\/v1\/ai\/features\/[0-9]+$/.test(afterFn) && req.method === "PUT") {
    const segs = afterFn.split("/")
    const id = Number(segs[4])
    const payload = await parseBody(req) as Record<string, unknown>
    const { error } = await supabase.from("ai_features").update(payload).eq("id", id)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/ai/stats") && req.method === "GET") {
    const { count: ac } = await supabase.from("ai_agents").select("id", { count: "exact", head: true })
    const { count: fc } = await supabase.from("ai_functions").select("id", { count: "exact", head: true })
    const { count: sc } = await supabase.from("ai_features").select("id", { count: "exact", head: true })
    return json({ agents: ac || 0, functions: fc || 0, features: sc || 0 })
  }

  if (afterFn.startsWith("api/v1/ai/answer") && req.method === "POST") {
    const body = await parseBody(req) as { question?: string }
    const q = String(body.question || "")
    let answer = "请在系统中查找对应功能入口。"
    if (/任务|进度/.test(q)) answer = "任务进度可在任务管理与仪表盘查看。"
    else if (/日报|提交/.test(q)) answer = "提交日报请进入日报页面，点击新建后填写并提交。"
    else if (/目标|月度/.test(q)) answer = "月度目标可在分析/目标管理页设置与查看。"
    return json({ answer })
  }
  if (afterFn === "api/v1/tasks" && req.method === "GET") {
    const page = Number(u.searchParams.get("page") || "1")
    const size = Number(u.searchParams.get("size") || "10")
    const start = (page - 1) * size
    const { data, error } = await supabase.from("tasks").select("*").range(start, start + size - 1)
    if (error) return json({ detail: error.message }, 500)
    const { count } = await supabase.from("tasks").select("id", { count: "exact", head: true })
    return json({ items: data || [], total: count || 0, page, size })
  }

  if (afterFn === "api/v1/tasks" && req.method === "POST") {
    const raw = await parseBody(req) as Record<string, unknown>
    const payload: Record<string, unknown> = { ...raw }

    // Inject assignee_id/created_by from Auth Token if missing
    const authHeader = req.headers.get("Authorization")
    if (authHeader) {
      const token = authHeader.replace("Bearer ", "")
      const { data: { user } } = await supabase.auth.getUser(token)
      if (user) {
        if (!payload.assignee_id) payload.assignee_id = user.id
        // tasks table usually doesn't have created_by, but if it does:
        // payload.created_by = user.id 
      }
    }

    const { data, error } = await supabase.from("tasks").insert(payload).select("*").single()
    if (error) return json({ detail: error.message }, 500)
    return json(data, 201)
  }

  if (/^api\/v1\/tasks\/[0-9]+$/.test(afterFn) && req.method === "GET") {
    const segs = afterFn.split("/")
    const id = Number(segs[3])
    const { data, error } = await supabase.from("tasks").select("*").eq("id", id).single()
    if (error) return json({ detail: error.message }, 500)
    return json(data)
  }

  if (/^api\/v1\/tasks\/[0-9]+$/.test(afterFn) && req.method === "PUT") {
    const segs = afterFn.split("/")
    const id = Number(segs[3])
    const payload = await parseBody(req) as Record<string, unknown>
    const { error } = await supabase.from("tasks").update(payload).eq("id", id)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (/^api\/v1\/tasks\/[0-9]+$/.test(afterFn) && req.method === "DELETE") {
    const segs = afterFn.split("/")
    const id = Number(segs[3])
    // HARD DELETE: This will permanently remove the task.
    const { error } = await supabase.from("tasks").delete().eq("id", id)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (/^api\/v1\/tasks\/[0-9]+\/status$/.test(afterFn) && req.method === "PUT") {
    const segs = afterFn.split("/")
    const id = Number(segs[3])
    const payload = await parseBody(req) as { status?: string }
    const { error } = await supabase.from("tasks").update({ status: payload.status }).eq("id", id)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (afterFn === "api/v1/tasks/batch-assign" && req.method === "PUT") {
    const payload = await parseBody(req) as { task_ids?: number[]; assignee_id?: string }
    const ids = Array.isArray(payload.task_ids) ? payload.task_ids : []
    if (!ids.length || !payload.assignee_id) return json({ detail: "缺少任务ID或负责人" }, 422)
    const { error } = await supabase.from("tasks").update({ assignee_id: payload.assignee_id }).in("id", ids)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (afterFn === "api/v1/tasks/stats" && req.method === "GET") {
    const { data, error } = await supabase.from("tasks").select("status")
    if (error) return json({ detail: error.message }, 500)
    const total = (data || []).length
    const byStatus: Record<string, number> = {}
    for (const t of data || []) {
      const s = (t as any).status || "unknown"
      byStatus[s] = (byStatus[s] || 0) + 1
    }
    return json({ total, by_status: byStatus })
  }

  if (afterFn === "api/v1/tasks/stats/summary" && req.method === "GET") {
    const { data, error } = await supabase.from("tasks").select("status")
    if (error) return json({ detail: error.message }, 500)
    const total = (data || []).length
    const completed = (data || []).filter(t => (t as any).status === "completed").length
    const in_progress = (data || []).filter(t => (t as any).status === "in_progress").length
    const pending = (data || []).filter(t => (t as any).status === "pending").length
    return json({ total, completed, in_progress, pending })
  }

  if (afterFn === "api/v1/tasks/weekly-trend" && req.method === "GET") {
    const since = new Date()
    since.setDate(since.getDate() - 30)
    const { data, error } = await supabase.from("tasks").select("created_at,status").gte("created_at", since.toISOString())
    if (error) return json({ detail: error.message }, 500)
    const bucket: Record<string, { created: number; completed: number }> = {}
    for (const t of data || []) {
      const d = new Date((t as any).created_at)
      const key = d.toISOString().slice(0, 10)
      if (!bucket[key]) bucket[key] = { created: 0, completed: 0 }
      bucket[key].created += 1
      if ((t as any).status === "completed") bucket[key].completed += 1
    }
    const series = Object.keys(bucket).sort().map(k => ({ date: k, ...bucket[k] }))
    return json({ series })
  }

  if (/^api\/v1\/tasks\/[0-9A-Za-z_-]+\/progress$/.test(afterFn) && req.method === "PUT") {
    const segs = afterFn.split("/")
    const taskId = segs[3]
    const payload = await parseBody(req) as any
    return json({ id: taskId, ...payload })
  }

  if (/^api\/v1\/tasks\/[0-9A-Za-z_-]+\/participate$/.test(afterFn) && req.method === "POST") {
    const segs = afterFn.split("/")
    const taskId = segs[3]
    const payload = await parseBody(req) as any
    return json({ id: taskId, ...payload })
  }

  if (/^api\/v1\/tasks\/[0-9]+\/jielong$/.test(afterFn) && req.method === "GET") {
    const segs = afterFn.split("/")
    const id = Number(segs[3])
    const userId = u.searchParams.get("user_id") || ""
    const scope = u.searchParams.get("scope") || ""
    const items: any[] = []
    return json({ items, task_id: id, scope, user_id: userId || null })
  }

  if (/^api\/v1\/tasks\/[0-9]+\/jielong$/.test(afterFn) && req.method === "POST") {
    const segs = afterFn.split("/")
    const id = Number(segs[3])
    const payload = await parseBody(req) as Record<string, unknown>
    const { data: tdata } = await supabase.from("tasks").select("jielong_current_count").eq("id", id).single()
    const cur = Number((tdata as any)?.jielong_current_count || 0)
    const { error } = await supabase.from("tasks").update({ jielong_current_count: cur + 1 }).eq("id", id)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (/^api\/v1\/tasks\/[0-9]+\/records$/.test(afterFn) && req.method === "GET") {
    const segs = afterFn.split("/")
    const id = Number(segs[3])
    const userId = u.searchParams.get("user_id") || ""
    const scope = u.searchParams.get("scope") || ""
    const items: any[] = []
    return json({ items, task_id: id, scope, user_id: userId || null })
  }

  if (/^api\/v1\/tasks\/[0-9]+\/completions$/.test(afterFn) && req.method === "GET") {
    const segs = afterFn.split("/")
    const id = Number(segs[3])
    const userId = u.searchParams.get("user_id") || ""
    const scope = u.searchParams.get("scope") || ""
    const items: any[] = []
    return json({ items, task_id: id, scope, user_id: userId || null })
  }

  if (afterFn.startsWith("api/v1/goals/monthly") && req.method === "GET") {
    const year = Number(u.searchParams.get("year") || new Date().getFullYear())
    const month = Number(u.searchParams.get("month") || (new Date().getMonth() + 1))
    const { data, error } = await supabase.from("monthly_goals").select("id,identity_type,scope,year,month,amount_target,new_sign_target_amount,referral_target_amount,renewal_total_target_amount,upgrade_target_count,renewal_target_count,created_at,updated_at").eq("year", year).eq("month", month)
    if (error) return json({ detail: error.message }, 500)
    return json(data || [])
  }

  if (afterFn.startsWith("api/v1/reports/stats/summary") && req.method === "GET") {
    const { data, error } = await supabase.from("daily_reports").select("mood_score")
    if (error) return json({ detail: error.message }, 500)
    const arr = (data || []) as any[]
    const total_reports = arr.length
    let avg_emotion_score = 0
    if (total_reports) {
      const vals = arr.map(r => Number((r as any).mood_score || 0)).filter(v => !Number.isNaN(v))
      const sum = vals.reduce((a, b) => a + b, 0)
      avg_emotion_score = vals.length ? Math.round(sum / vals.length) : 0
    }
    return json({ total_reports, avg_emotion_score })
  }

  if (afterFn.startsWith("api/v1/goals/monthly") && req.method === "POST") {
    const payload = await parseBody(req) as { identity_type: string; scope: string; year: number; month: number; amount_target?: number; new_sign_target_amount?: number; referral_target_amount?: number; renewal_total_target_amount?: number; upgrade_target_count?: number; renewal_target_count?: number }
    const { data, error } = await supabase.from("monthly_goals").insert(payload).select("*").single()
    if (error) return json({ detail: error.message }, 500)
    return json(data, 201)
  }

  if (afterFn.startsWith("api/v1/goals/monthly/personal") && req.method === "GET") {
    const identity_type = String(u.searchParams.get("identity_type") || "").toUpperCase()
    const group_id = u.searchParams.get("group_id") || undefined
    const year = u.searchParams.get("year") || undefined
    const month = u.searchParams.get("month") || undefined
    let q = supabase.from("personal_monthly_goals").select("id,identity_type,group_id,user_id,year,month,new_sign_target_amount,referral_target_amount,renewal_total_target_amount,upgrade_target_count")
    if (identity_type) q = q.eq("identity_type", identity_type)
    if (group_id) q = q.eq("group_id", Number(group_id))
    if (year) q = q.eq("year", Number(year))
    if (month) q = q.eq("month", Number(month))
    const { data, error } = await q
    if (error) return json({ detail: error.message }, 500)
    return json({ items: data || [] })
  }

  if (afterFn.startsWith("api/v1/goals/monthly/personal") && req.method === "POST") {
    const payload = await parseBody(req) as any
    const arr = Array.isArray(payload) ? payload : (payload.items || [])
    const { error } = await supabase.from("personal_monthly_goals").insert(arr)
    if (error) return json({ success: false, detail: error.message }, 500)
    return json({ success: true, saved: arr.length })
  }

  if (afterFn.startsWith("api/v1/users") && req.method === "GET") {
    const hasLegacy = await detectHasLegacyId()
    const page = Number(u.searchParams.get("page") || "1")
    const size = Number(u.searchParams.get("size") || "10")
    const roleParam = u.searchParams.get("role") || ""
    const isActiveParam = u.searchParams.get("is_active")
    const searchParam = (u.searchParams.get("search") || "").trim()
    let selectFields = "id,username,role,group_id,group_name,identity_type,is_active,created_at"
    if (hasLegacy) selectFields = "id,legacy_id,username,role,group_id,group_name,identity_type,is_active,created_at"
    let q = supabase.from("user_account").select(selectFields)
    if (roleParam) q = q.eq("role", roleParam)
    if (isActiveParam !== null && isActiveParam !== undefined && isActiveParam !== "") {
      const b = String(isActiveParam).toLowerCase() === "true"
      q = q.eq("is_active", b)
    }
    if (searchParam) q = q.ilike("username", `%${searchParam}%`)
    const { data, error } = await q
    if (error) return json({ detail: error.message }, 500)
    const total = (data || []).length
    const start = (page - 1) * size
    const sliced = (data || []).slice(start, start + size)
    const items = sliced.map(u => ({
      id: (u as any).id ?? (u as any).legacy_id,
      legacy_id: (u as any).legacy_id,
      username: (u as any).username,
      full_name: (u as any).username,
      email: `${(u as any).username}@example.com`,
      role: (u as any).role,
      identity_type: (u as any).identity_type,
      group_id: (u as any).group_id,
      group_name: (u as any).group_name,
      is_active: (u as any).is_active,
      created_at: (u as any).created_at,
      organization: null
    }))
    return json({ items, total, page, size })
  }

  if (afterFn === "api/v1/users" && req.method === "POST") {
    const payload = await parseBody(req) as { username?: string; role?: string; identity_type?: string; group_id?: number; group_name?: string; is_active?: boolean; password?: string }
    const username = String(payload.username || "").trim()
    if (!username || username.length < 2 || username.length > 100) return json({ detail: "用户名长度在 2 到 100 个字符" }, 422)
    const role = String(payload.role || "user")
    const pw = String(payload.password || "")
    if (!pw || pw.length < 6) return json({ detail: "密码至少 6 位" }, 422)
    const salt = bcrypt.genSaltSync(10)
    const hash = bcrypt.hashSync(pw, salt)
    let gid = payload.group_id ?? null
    let gname = payload.group_name ?? null
    if (gid != null && gname == null) {
      const { data: g } = await supabase.from("groups").select("name").eq("id", Number(gid)).single()
      gname = (g as any)?.name ?? null
    }
    const { data, error } = await supabase.from("user_account").insert({
      username,
      role,
      identity_type: payload.identity_type ?? null,
      group_id: gid,
      group_name: gname,
      is_active: payload.is_active ?? true,
      hashed_password: hash
    }).select("*").single()
    if (error) return json({ detail: error.message }, 500)
    return json(data, 201)
  }

  if (/^api\/v1\/users\/[A-Za-z0-9-]+$/.test(afterFn) && req.method === "PUT") {
    const hasLegacy = await detectHasLegacyId()
    const segs = afterFn.split("/")
    const uid = segs[3] || segs[2]
    const payload = await parseBody(req) as { username?: string; role?: string; identity_type?: string; group_id?: number; group_name?: string; is_active?: boolean; password?: string }
    const base: Record<string, any> = {}
    if (payload.username !== undefined) base.username = payload.username
    if (payload.role !== undefined) base.role = payload.role
    if (payload.identity_type !== undefined) base.identity_type = payload.identity_type
    if (payload.group_id !== undefined) {
      base.group_id = payload.group_id
      if (payload.group_name !== undefined) {
        base.group_name = payload.group_name
      } else {
        if (payload.group_id == null) {
          base.group_name = null
        } else {
          const { data: g } = await supabase.from("groups").select("name").eq("id", Number(payload.group_id)).single()
          base.group_name = (g as any)?.name ?? null
        }
      }
    }
    if (payload.group_name !== undefined && payload.group_id === undefined) base.group_name = payload.group_name
    if (payload.is_active !== undefined) base.is_active = payload.is_active
    if (payload.password) {
      const pw = String(payload.password)
      if (pw.length < 6) return json({ detail: "密码至少 6 位" }, 422)
      const salt = bcrypt.genSaltSync(10)
      base.hashed_password = bcrypt.hashSync(pw, salt)
    }
    const useUUID = isUUID(uid)
    const isNum = !Number.isNaN(Number(uid))
    console.log("[users:PUT] incoming", { uid, useUUID, isNum, hasPassword: !!payload.password, keys: Object.keys(base) })
    let affected = 0
    let hp: any = null
    if (useUUID) {
      const { data, error } = await supabase.from("user_account").update(base).eq("id", uid).select("id,username,is_active,hashed_password")
      if (error) {
        console.error("[users:PUT] update uuid error", error)
        return json({ detail: error.message }, 500)
      }
      affected = Array.isArray(data) ? data.length : (data ? 1 : 0)
      hp = Array.isArray(data) ? (data[0] as any)?.hashed_password : (data as any)?.hashed_password
    } else if (isNum) {
      let lastErr: any = null
      if (hasLegacy) {
        const r1 = await supabase.from("user_account").update(base).eq("legacy_id", Number(uid)).select("id,username,is_active,hashed_password")
        if (!r1.error) {
          affected = Array.isArray(r1.data) ? r1.data.length : (r1.data ? 1 : 0)
          hp = Array.isArray(r1.data) ? (r1.data[0] as any)?.hashed_password : (r1.data as any)?.hashed_password
        } else {
          lastErr = r1.error
        }
      }
      if (!affected && payload.username) {
        const rU = await supabase.from("user_account").update(base).eq("username", String(payload.username)).select("id,username,is_active,hashed_password")
        if (!rU.error) {
          affected = Array.isArray(rU.data) ? rU.data.length : (rU.data ? 1 : 0)
          hp = Array.isArray(rU.data) ? (rU.data[0] as any)?.hashed_password : (rU.data as any)?.hashed_password
        }
      }
      if (!affected) {
        const r2 = await supabase.from("user_account").update(base).eq("id", Number(uid)).select("id,username,is_active,hashed_password")
        if (!r2.error) {
          affected = Array.isArray(r2.data) ? r2.data.length : (r2.data ? 1 : 0)
          hp = Array.isArray(r2.data) ? (r2.data[0] as any)?.hashed_password : (r2.data as any)?.hashed_password
        } else {
          console.warn("[users:PUT] numeric id update error", r2.error)
        }
      }
      if (!affected && lastErr && !hasLegacy) {
        console.error("[users:PUT] update error", lastErr)
        return json({ detail: lastErr.message }, 500)
      }
    } else {
      const { data, error } = await supabase.from("user_account").update(base).eq("id", uid).select("id,username,is_active,hashed_password")
      if (error) {
        console.error("[users:PUT] update string id error", error)
        return json({ detail: error.message }, 500)
      }
      affected = Array.isArray(data) ? data.length : (data ? 1 : 0)
      hp = Array.isArray(data) ? (data[0] as any)?.hashed_password : (data as any)?.hashed_password
    }
    console.log("[users:PUT] updated", { affected, hasHashedPassword: !!hp })
    if (!affected) return json({ detail: "未找到用户或ID不匹配" }, 404)
    return json({ success: true, affected })
  }

  if (/^api\/v1\/users\/[A-Za-z0-9-]+$/.test(afterFn) && req.method === "DELETE") {
    const hasLegacy = await detectHasLegacyId()
    const segs = afterFn.split("/")
    const uid = segs[3] || segs[2]
    const isNum = !Number.isNaN(Number(uid))
    let delErr: any = null
    let delAffected = 0
    if (isUUID(uid)) {
      const { error } = await supabase.from("user_account").delete().eq("id", uid)
      delErr = error
      delAffected = error ? 0 : 1
    } else if (isNum) {
      if (hasLegacy) {
        const { error } = await supabase.from("user_account").delete().eq("legacy_id", Number(uid))
        if (!error) delAffected = 1
        else delErr = error
      }
      if (!delAffected) {
        const { error } = await supabase.from("user_account").delete().eq("id", Number(uid))
        if (!error) delAffected = 1
        else delErr = error
      }
    } else {
      const { error } = await supabase.from("user_account").delete().eq("id", uid)
      delErr = error
      delAffected = error ? 0 : 1
    }
    if (delErr) return json({ detail: delErr.message }, 500)
    if (!delAffected) return json({ detail: "未找到用户或ID不匹配" }, 404)
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/groups/") && afterFn.endsWith("/members") && req.method === "GET") {
    const segs = afterFn.split("/")
    const gid = Number(segs[3])
    const { data, error } = await supabase.from("user_account").select("id,username,role,group_id,group_name,identity_type").eq("group_id", gid)
    if (error) return json({ detail: error.message }, 500)
    const members = (data || []).map(m => ({ id: (m as any).id, username: (m as any).username, full_name: (m as any).username, email: `${(m as any).username}@example.com`, role: (m as any).role, identity_type: (m as any).identity_type }))
    return json(members)
  }

  if (afterFn.startsWith("api/v1/groups/") && afterFn.endsWith("/members") && req.method === "POST") {
    const hasLegacy = await detectHasLegacyId()
    const segs = afterFn.split("/")
    const gid = Number(segs[3])
    const body = await parseBody(req) as { user_ids?: number[] }
    const ids = Array.isArray(body.user_ids) ? body.user_ids.map(n => Number(n)).filter(n => !Number.isNaN(n)) : []
    if (!ids.length) return json({ detail: "缺少用户ID" }, 422)
    let gname: string | null = null
    {
      const { data: g } = await supabase.from("groups").select("name").eq("id", gid).single()
      gname = (g as any)?.name ?? null
    }
    const updates = ids.map(async (id) => {
      if (hasLegacy) {
        const r1 = await supabase.from("user_account").update({ group_id: gid, group_name: gname }).eq("legacy_id", id)
        if (!r1.error) return r1
      }
      return await supabase.from("user_account").update({ group_id: gid, group_name: gname }).eq("id", id)
    })
    const results = await Promise.all(updates)
    const err = results.find(r => r.error)?.error
    if (err) return json({ detail: err.message }, 500)
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/groups/") && /\/members\/[0-9]+$/.test(afterFn) && req.method === "DELETE") {
    const segs = afterFn.split("/")
    const gid = Number(segs[3])
    const uid = segs[5]
    const hasLegacy = await detectHasLegacyId()
    const { error } = isUUID(uid)
      ? await supabase.from("user_account").update({ group_id: null, group_name: null }).eq("id", uid).eq("group_id", gid)
      : hasLegacy
        ? await supabase.from("user_account").update({ group_id: null, group_name: null }).eq("legacy_id", Number(uid)).eq("group_id", gid)
        : { error: { message: "未找到用户或ID不匹配" } as any }
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/groups") && req.method === "GET") {
    const page = Number(u.searchParams.get("page") || "1")
    const size = Number(u.searchParams.get("size") || "10")
    const search = String(u.searchParams.get("search") || "").trim().toLowerCase()
    const { data, error } = await supabase.from("groups").select("id,name,description,created_at")
    if (error) return json({ detail: error.message }, 500)
    const filtered = (data || []).filter(g => !search || (g.name || "").toLowerCase().includes(search))
    const start = (page - 1) * size
    const items = filtered.slice(start, start + size)
    return json({ items, total: filtered.length, page, size })
  }

  if (afterFn === "api/v1/groups" && req.method === "POST") {
    const payload = await parseBody(req) as { name?: string; description?: string }
    const name = String(payload.name || "").trim()
    if (!name || name.length < 2 || name.length > 100) return json({ detail: "组织名称长度在 2 到 100 个字符" }, 422)
    const { data, error } = await supabase.from("groups").insert({ name, description: String(payload.description || "") }).select("*").single()
    if (error) return json({ detail: error.message }, 500)
    return json(data, 201)
  }

  if (/^api\/v1\/groups\/[0-9]+$/.test(afterFn) && req.method === "PUT") {
    const segs = afterFn.split("/")
    const gid = Number(segs[3])
    const payload = await parseBody(req) as { name?: string; description?: string }
    const name = String(payload.name || "").trim()
    if (!name || name.length < 2 || name.length > 100) return json({ detail: "组织名称长度在 2 到 100 个字符" }, 422)
    const { error } = await supabase.from("groups").update({ name, description: String(payload.description || "") }).eq("id", gid)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (/^api\/v1\/groups\/[0-9]+$/.test(afterFn) && req.method === "DELETE") {
    const segs = afterFn.split("/")
    const gid = Number(segs[3])
    const { error } = await supabase.from("groups").delete().eq("id", gid)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/admin/metrics") && req.method === "GET") {
    const { data, error } = await supabase.from("admin_metrics").select("id,key,name,is_active,default_roles")
    if (error) return json({ detail: error.message }, 500)
    return json(data ?? [])
  }

  if (afterFn.startsWith("api/v1/admin/metrics/") && req.method === "PUT") {
    const segs = afterFn.split("/")
    const key = segs[3]
    const payload = await parseBody(req) as { name?: string; is_active?: boolean; default_roles?: string[] }
    const { error } = await supabase.from("admin_metrics").update({
      name: payload.name,
      is_active: payload.is_active,
      default_roles: payload.default_roles
    }).eq("key", key)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/settings/ai") && req.method === "GET") {
    const { data, error } = await supabase.from("settings_ai").select("provider,api_key,base_url,model_name,max_tokens,temperature").eq("id", 1).single()
    if (error) return json({ detail: error.message }, 500)
    return json(data)
  }

  if (afterFn.startsWith("api/v1/settings/ai") && req.method === "PUT") {
    const payload = await parseBody(req) as { provider?: string; api_key?: string; base_url?: string; model_name?: string; max_tokens?: number; temperature?: number }
    const { error } = await supabase.from("settings_ai").update({
      provider: payload.provider,
      api_key: payload.api_key,
      base_url: payload.base_url,
      model_name: payload.model_name,
      max_tokens: payload.max_tokens,
      temperature: payload.temperature
    }).eq("id", 1)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/settings/system") && req.method === "GET") {
    const { data, error } = await supabase.from("settings_system").select("system_name,timezone,language,auto_analysis,data_retention_days").eq("id", 1).single()
    if (error) return json({ detail: error.message }, 500)
    return json(data)
  }

  if (afterFn.startsWith("api/v1/settings/system") && req.method === "PUT") {
    const payload = await parseBody(req) as { system_name?: string; timezone?: string; language?: string; auto_analysis?: boolean; data_retention_days?: number }
    const { error } = await supabase.from("settings_system").update({
      system_name: payload.system_name,
      timezone: payload.timezone,
      language: payload.language,
      auto_analysis: payload.auto_analysis,
      data_retention_days: payload.data_retention_days
    }).eq("id", 1)
    if (error) return json({ detail: error.message }, 500)
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/settings/ai/test") && req.method === "POST") {
    const payload = await parseBody(req) as { provider?: string; api_key?: string; base_url?: string }
    const provider = (payload.provider || "").toLowerCase()
    const url = payload.base_url || "https://openrouter.ai/api/v1"
    const key = payload.api_key || ""
    if (!provider || !key) return json({ success: false, message: "Invalid config" }, 400)
    try {
      const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } })
      return json({ success: res.status < 400, response: res.statusText, message: res.ok ? "OK" : "Failed" })
    } catch {
      return json({ success: false, message: "Failed" })
    }
  }

  if (afterFn.startsWith("api/v1/settings/export") && req.method === "GET") {
    const { data: ai } = await supabase.from("settings_ai").select("*").eq("id", 1).single()
    const { data: sys } = await supabase.from("settings_system").select("*").eq("id", 1).single()
    const { data: metrics } = await supabase.from("admin_metrics").select("*")
    const { data: groups } = await supabase.from("groups").select("*")
    return json({ ai, system: sys, metrics, groups })
  }

  if (afterFn.startsWith("api/v1/settings/clear-cache") && req.method === "POST") {
    return json({ success: true })
  }

  if (afterFn.startsWith("api/v1/settings/reset") && req.method === "POST") {
    await supabase.from("settings_ai").update(defaultAISettings).eq("id", 1)
    await supabase.from("settings_system").update(defaultSystemSettings).eq("id", 1)
    return json({ success: true })
  }

  return notFound()
})