<#
  Remove a tarefa que inicia o bot com o Windows e para o bot.
  Rode no PowerShell COMO ADMINISTRADOR:
      powershell -ExecutionPolicy Bypass -File .\servidor\desinstalar-windows.ps1
  (As configuracoes de energia nao sao revertidas; para isso use Painel de Controle > Opcoes de Energia.)
#>
#Requires -RunAsAdministrator
$NomeTarefa = "BotChecklistRestaurante"
if (Get-ScheduledTask -TaskName $NomeTarefa -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName $NomeTarefa -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $NomeTarefa -Confirm:$false
    Write-Host "[ok] Tarefa removida."
} else {
    Write-Host "A tarefa '$NomeTarefa' nao existe."
}
# garante que nenhum bot.py ficou rodando
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -like "*bot.py*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host "[ok] Processo $($_.ProcessId) encerrado." }
