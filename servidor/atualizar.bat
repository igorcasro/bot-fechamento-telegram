@echo off
rem Atualiza o bot para a versao mais nova do GitHub e reinicia. Requer o Git instalado e o
rem projeto clonado com "git clone". Rode como ADMINISTRADOR (clique direito > Executar como administrador).
rem Seus arquivos .env, arquivo\, logs\ e estado.pickle NAO sao tocados (estao fora do Git).

cd /d "%~dp0.."
git pull --ff-only
if errorlevel 1 (
    echo.
    echo FALHA no "git pull". Nada foi reiniciado. Leia a mensagem acima.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
schtasks /End /TN "BotChecklistRestaurante" >nul 2>&1
schtasks /Run /TN "BotChecklistRestaurante"
echo.
echo Pronto: bot atualizado e reiniciado. Confira com /start no Telegram.
pause
