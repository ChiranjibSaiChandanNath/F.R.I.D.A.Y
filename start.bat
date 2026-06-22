@echo off
cd /d "%~dp0"
title F.R.I.D.A.Y. Launcher

echo.
echo  ============================================================
echo   F . R . I . D . A . Y .  --  Starting up...
echo  ============================================================
echo.

:: ----------------------------------------------------------------
:: Auto-create .env from .env.example if missing
:: ----------------------------------------------------------------
if exist ".env" goto env_exists
if not exist ".env.example" goto env_no_example

copy ".env.example" ".env" >nul
echo  [F.R.I.D.A.Y.] .env not found -- created from .env.example
echo  [F.R.I.D.A.Y.] Open .env and fill in your GROQ_API_KEY before continuing.
echo.
notepad .env
echo  Press any key after saving your API keys...
pause >nul
goto env_exists

:env_no_example
echo  [F.R.I.D.A.Y.] WARNING: No .env file found. F.R.I.D.A.Y. may not work correctly.
pause >nul

:env_exists

set FIRST_TIME=0
findstr /i "^FACE_AUTH=" .env >nul 2>&1
if errorlevel 1 set FIRST_TIME=1

:: ----------------------------------------------------------------
:: First-time Face / Voice Authentication Setup
:: ----------------------------------------------------------------
findstr /i "^FACE_AUTH=" .env >nul 2>&1
if errorlevel 1 goto prompt_face_setup
goto face_setup_done

:prompt_face_setup
echo.
echo  ============================================================
echo   F.R.I.D.A.Y.  Security Setup
echo  ============================================================
set /p choice=" Would you like to enable Face/Voice Unlock? (Y/N): "
if /i "%choice%"=="Y" goto run_face_setup
if /i "%choice%"=="Yes" goto run_face_setup

:: User denied - disable face auth in .env
echo. >> .env
echo FACE_AUTH=false >> .env
echo VOICE_PASSPHRASE= >> .env
echo  [F.R.I.D.A.Y.] Face/Voice Unlock disabled. Starting normally...
goto face_setup_done

:run_face_setup
echo.
echo  [F.R.I.D.A.Y.] Launching Face Training...
echo  Please position your face clearly in front of the webcam.
python lib/face_auth.py --train
if errorlevel 1 (
    echo.
    echo  [WARNING] Face training failed or was cancelled.
    echo  Face auth will be disabled for now.
    echo. >> .env
    echo FACE_AUTH=false >> .env
    echo VOICE_PASSPHRASE= >> .env
    pause
    goto face_setup_done
)

:: Face training succeeded, now ask for Voice Passphrase
echo.
echo  ============================================================
echo   Face training completed successfully!
echo  ============================================================
echo.
set /p passphrase=" Enter a spoken backup passphrase (e.g. 'wake up to reality'): "
if "%passphrase%"=="" (
    set passphrase=wake up to reality
)

echo. >> .env
echo FACE_AUTH=true >> .env
echo VOICE_PASSPHRASE=%passphrase% >> .env
echo.
echo  [F.R.I.D.A.Y.] Face/Voice Unlock configured successfully!
echo.
goto face_setup_done

:face_setup_done

:: ----------------------------------------------------------------
:: First-time Google Integration Setup
:: ----------------------------------------------------------------
findstr /i "^GMAIL_INTEGRATION=" .env >nul 2>&1
if errorlevel 1 goto prompt_gmail_setup
goto setup_all_done

:prompt_gmail_setup
echo.
echo  ============================================================
echo   F.R.I.D.A.Y.  Email/Calendar Integration Setup
echo  ============================================================
set /p gchoice=" Would you like to integrate your Gmail and Google Calendar? (Y/N): "
if /i "%gchoice%"=="Y" goto run_gmail_setup
if /i "%gchoice%"=="Yes" goto run_gmail_setup

:: User denied - disable Gmail integration in .env
echo. >> .env
echo GMAIL_INTEGRATION=false >> .env
echo  [F.R.I.D.A.Y.] Google integration disabled. Continuing to dashboard...
goto setup_all_done

:run_gmail_setup
echo.
echo  ============================================================
echo   [IMPORTANT NOTICE]
echo   Google integration requires you to manually download your
echo   credentials.json file and place it in the project folder.
echo   This process cannot be automated.
echo  ============================================================
echo.
set /p cred_check=" Have you already added 'credentials.json' to the project's data/ folder? (Y/N): "
if /i "%cred_check%"=="Y" goto save_gmail_enabled
if /i "%cred_check%"=="Yes" goto save_gmail_enabled

:: User has not added credentials.json yet
echo.
echo  Opening Google Cloud Console instructions page...
start https://console.cloud.google.com/
echo.
echo  Please follow these steps:
echo  1. Create a Desktop app OAuth credential on Google Cloud Console.
echo  2. Download the JSON file.
echo  3. Rename it to "credentials.json".
echo  4. Paste it inside the project's "data/" directory.
echo.
echo  ============================================================
echo   Once you have pasted 'credentials.json' inside 'data/' folder,
echo   return here and confirm.
echo  ============================================================
echo.
:loop_cred_confirm
set /p cred_confirm=" Did you add the 'credentials.json' file to the project's data/ folder now? (Y/N): "
if /i "%cred_confirm%"=="Y" goto save_gmail_enabled
if /i "%cred_confirm%"=="Yes" goto save_gmail_enabled
echo  [F.R.I.D.A.Y.] credentials.json file is required to enable integration.
set /p retry_choice=" Try again (T) or Skip / Disable (S)?: "
if /i "%retry_choice%"=="S" goto skip_gmail_setup
if /i "%retry_choice%"=="Skip" goto skip_gmail_setup
goto loop_cred_confirm

:skip_gmail_setup
echo. >> .env
echo GMAIL_INTEGRATION=false >> .env
echo  [F.R.I.D.A.Y.] Google integration skipped. Starting normally...
goto setup_all_done

:save_gmail_enabled
echo. >> .env
echo GMAIL_INTEGRATION=true >> .env
echo  [F.R.I.D.A.Y.] Google integration enabled successfully!
goto setup_all_done

:setup_all_done
if "%FIRST_TIME%"=="1" goto prompt_name_setup
goto actual_start

:prompt_name_setup
echo.
echo  ============================================================
echo   F.R.I.D.A.Y.  Identity Configuration
echo  ============================================================
echo.
set /p input_name=" Please enter your name (e.g. John, Tony, Alex): "
if "%input_name%"=="" (
    set input_name=sir
)
set /p input_honorific=" What should I call you? (sir / ma'am / boss / chief / etc.): "
if "%input_honorific%"=="" (
    set input_honorific=sir
)

:: Update USER_NAME and HONORIFIC in .env
powershell -Command "(Get-Content .env) -replace '^USER_NAME=.*', 'USER_NAME=%input_name%' -replace '^HONORIFIC=.*', 'HONORIFIC=%input_honorific%' | Set-Content .env"

echo.
echo  [F.R.I.D.A.Y.] Identity configured! Welcome, %input_honorific% %input_name%.
echo.
goto actual_start

:actual_start




:: ----------------------------------------------------------------
:: Check face model -- warn if FACE_AUTH=true but no model trained
:: ----------------------------------------------------------------
findstr /i "FACE_AUTH=true" .env >nul 2>&1
if errorlevel 1 goto skip_face_check
if exist "data\face_auth\face_model.yml" goto model_ok

echo  [FACE AUTH] FACE_AUTH=true but no face model found!
echo  [FACE AUTH] Run this first:  python lib/face_auth.py --train
echo.
echo  Press any key to start anyway (auth will be skipped)...
pause >nul
goto skip_face_check

:model_ok
echo  [FACE AUTH] Face model found. Lock screen will activate in browser.

:skip_face_check
echo.

:: ----------------------------------------------------------------
:: Kill any leftover F.R.I.D.A.Y. processes
:: ----------------------------------------------------------------
echo  [F.R.I.D.A.Y.] Cleaning up old processes...
powershell -Command "$p = (Get-NetTCPConnection -LocalPort 8340 -ErrorAction SilentlyContinue).OwningProcess; if ($p) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue }" >nul 2>&1
powershell -Command "$p = (Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue).OwningProcess; if ($p) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue }" >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq F.R.I.D.A.Y. Backend*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq F.R.I.D.A.Y. Frontend*" >nul 2>&1

:: ----------------------------------------------------------------
:: Start backend in a new terminal window
:: ----------------------------------------------------------------
echo  [F.R.I.D.A.Y.] Starting backend (port 8340)...
start "F.R.I.D.A.Y. Backend" cmd /k "cd /d %~dp0 && python -u server.py"

:: ----------------------------------------------------------------
:: Start frontend in a new terminal window
:: ----------------------------------------------------------------
echo  [F.R.I.D.A.Y.] Starting frontend (port 5173)...
start "F.R.I.D.A.Y. Frontend" cmd /k "cd /d %~dp0frontend && call npm.cmd run dev"

:: Wait for servers to boot
echo  [F.R.I.D.A.Y.] Waiting for servers to initialize...
timeout /t 4 /nobreak >nul

:: ----------------------------------------------------------------
:: Open browser
:: ----------------------------------------------------------------
echo  [F.R.I.D.A.Y.] Launching browser...
start http://localhost:5173

echo.
echo  ============================================================
echo   F.R.I.D.A.Y. is now running.
echo   If the browser didn't open, go to: http://localhost:5173
echo  ============================================================
echo.
timeout /t 5 >nul
