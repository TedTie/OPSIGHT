param(
  [string]$ProjectRef = "hmzwgteftyiwfhepkvco"
)

if (-not (Get-Command supabase -ErrorAction SilentlyContinue)) {
  Write-Error 'Supabase CLI not found. Install via Scoop: iwr -useb get.scoop.sh | iex; scoop bucket add supabase https://github.com/supabase/scoop-bucket.git; scoop install supabase'
  exit 1
}

Write-Host 'Enter SUPABASE_ACCESS_TOKEN (input is hidden):' -ForegroundColor Green
$secure = Read-Host -AsSecureString
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$token = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

if ([string]::IsNullOrWhiteSpace($token)) { Write-Error 'Access Token is empty'; exit 1 }

$env:SUPABASE_ACCESS_TOKEN = $token

try {
  supabase login --token $token --no-browser | Out-Null
  supabase link --project-ref $ProjectRef | Out-Null
  supabase functions deploy killerapp | Out-Null
  Write-Host 'Supabase function deployed: killerapp' -ForegroundColor Green
}
finally {
  $env:SUPABASE_ACCESS_TOKEN = $null
}