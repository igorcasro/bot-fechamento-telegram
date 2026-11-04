<#
  Instala o bot como uma tarefa que inicia SOZINHA quando o Windows liga (sem precisar entrar
  na conta) e deixa o notebook configurado para funcionar como servidor.

  Como usar: abra o PowerShell COMO ADMINISTRADOR, entre na pasta do projeto e rode:
      powershell -ExecutionPolicy Bypass -File .\servidor\instalar-windows.ps1

  Pode rodar de novo quando quiser (ele recria a tarefa). Para remover: desinstalar-windows.ps1
#>
#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"

$NomeTarefa = "BotChecklistRestaurante"
$Raiz = Split-Path -Parent $PSScriptRoot            # pasta do projeto
$Bat = Join-Path $PSScriptRoot "iniciar-bot.bat"
$Python = Join-Path $Raiz ".venv\Scripts\python.exe"

Write-Host "Pasta do projeto: $Raiz"
if (-not (Test-Path (Join-Path $Raiz ".env")))  { throw "Falta o arquivo .env em $Raiz (copie o .env.example e preencha)." }
if (-not (Test-Path $Python))                   { throw "Falta o ambiente virtual em $Raiz\.venv (veja o guia, passo 'Instalar as dependencias')." }

# 1) Tarefa: roda ao ligar o Windows, como SYSTEM (nao depende de ninguem estar logado),
#    sem limite de tempo, mesmo na bateria, e tenta de novo se falhar.
$Acao = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$Bat`"" -WorkingDirectory $Raiz
$Gatilho = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$Config = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $NomeTarefa -Action $Acao -Trigger $Gatilho `
    -Principal $Principal -Settings $Config -Force | Out-Null
Write-Host "[ok] Tarefa '$NomeTarefa' criada (inicia ao ligar o Windows)."

# 2) Energia: na tomada, nunca suspender/hibernar e nao fazer nada ao fechar a tampa.
#    (a tela pode apagar sozinha depois de 10 min)
powercfg /change standby-timeout-ac 0     | Out-Null
powercfg /change hibernate-timeout-ac 0   | Out-Null
powercfg /change monitor-timeout-ac 10    | Out-Null
powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0 | Out-Null
powercfg /hibernate off                   | Out-Null   # tambem desliga a "Inicializacao rapida"
powercfg /setactive SCHEME_CURRENT        | Out-Null
Write-Host "[ok] Energia: nao suspende, nao hiberna, tampa fechada nao faz nada (na tomada)."

# 3) Liga agora, sem precisar reiniciar
Start-ScheduledTask -TaskName $NomeTarefa
Start-Sleep -Seconds 8
$Estado = (Get-ScheduledTask -TaskName $NomeTarefa).State
Write-Host "[ok] Tarefa iniciada. Estado: $Estado"

Write-Host ""
Write-Host "PROXIMOS PASSOS:"
Write-Host " 1. Veja se o bot responde no Telegram (/start)."
Write-Host " 2. Acompanhe o log em: $Raiz\logs\bot.log"
Write-Host " 3. Faca o teste de reinicio descrito no guia (reiniciar o notebook SEM entrar na conta)."
