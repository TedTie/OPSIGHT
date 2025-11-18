param(
  [string]$ProjectRef = "hmzwgteftyiwfhepkvco"
)

function Require-Command($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    Write-Error "命令 '$name' 未安装。请先安装 Supabase CLI 后重试：winget install Supabase.SupabaseCLI 或参考官方文档。"
    exit 1
  }
}

Require-Command "supabase"

Write-Host "请输入 SUPABASE_ACCESS_TOKEN（不会回显）：" -ForegroundColor Green
$secure = Read-Host -AsSecureString
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$token = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

if ([string]::IsNullOrWhiteSpace($token)) { Write-Error "未提供 Access Token"; exit 1 }

$env:SUPABASE_ACCESS_TOKEN = $token

try {
  supabase login | Out-Null
  supabase link --project-ref $ProjectRef | Out-Null
  supabase functions deploy killerapp | Out-Null
  Write-Host "Supabase 函数部署完成：killerapp" -ForegroundColor Green
}
finally {
  $env:SUPABASE_ACCESS_TOKEN = $null
}