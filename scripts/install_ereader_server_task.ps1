param(
    [string]$Time = "08:00",
    [int]$Port = 8844,
    [switch]$Demo,
    [switch]$WithPdf,
    [string]$InputDir = "",
    [switch]$OpenFirewall
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = (Get-Command python -ErrorAction Stop).Source
}
$Main = Join-Path $Root "main.py"
$Mode = if ($Demo) { "--demo" } else { "--live" }
$Format = if ($WithPdf) { "both" } else { "epub" }
$Arguments = "`"$Main`" serve $Mode --host 0.0.0.0 --port $Port --refresh-at `"$Time`" --format $Format"
if ($InputDir) {
    $Arguments += " --input-dir `"$InputDir`""
}

$Action = New-ScheduledTaskAction -Execute $Python -Argument $Arguments -WorkingDirectory $Root
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName "Signal Matin - liseuse" -Action $Action -Trigger $Trigger `
    -Settings $Settings -Description "Publie chaque matin l'edition liseuse Signal Matin sur le reseau local" -Force | Out-Null

if ($OpenFirewall) {
    $rule = "Signal Matin - liseuse (TCP $Port)"
    if (-not (Get-NetFirewallRule -DisplayName $rule -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName $rule -Direction Inbound -Action Allow `
            -Protocol TCP -LocalPort $Port -Profile Private | Out-Null
    }
}

Start-ScheduledTask -TaskName "Signal Matin - liseuse"
Write-Host "Tache 'Signal Matin - liseuse' installee et demarree."
Write-Host "L'edition sera actualisee chaque jour a $Time et restera disponible sur le port $Port."
Write-Host "Lance la commande ci-dessous pour afficher le favori prive sans demarrer un second serveur :"
Write-Host "  signal-matin serve $Mode --host 0.0.0.0 --port $Port --refresh-at $Time --show-url-only"
if (-not $OpenFirewall) {
    Write-Host "Si la liseuse n'accede pas a la page, relance ce script en administrateur avec -OpenFirewall."
}
