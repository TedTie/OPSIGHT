const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With"
}

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json", ...corsHeaders } })
}

function notFound() {
  return json({ detail: "Not Found" }, 404)
}

async function parseBody(req: Request) {
  const text = await req.text()
  try { return JSON.parse(text || "{}") } catch { return {} }
}

export default async function handler(req: Request): Promise<Response> {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders })
  const u = new URL(req.url)
  const p = u.pathname.replace(/^\/+/, "")
  const parts = p.split("/")
  const afterFn = parts.slice(1).join("/")

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

  if (afterFn.startsWith("auth/login") && req.method === "POST") {
    return json({ user: { id: 1, username: "demo", role: "super_admin" } })
  }

  if (afterFn.startsWith("auth/logout") && req.method === "POST") {
    return json({ success: true })
  }

  if (afterFn.startsWith("auth/me") && req.method === "GET") {
    return json({ id: 1, username: "demo", role: "super_admin" })
  }

  return notFound()
}