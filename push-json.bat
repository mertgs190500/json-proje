@echo off
cd %USERPROFILE%\Desktop\json-proje

:: Tarih ve saati al
for /f "tokens=1-4 delims=/. " %%a in ('date /t') do (
    set dow=%%a
    set mm=%%b
    set dd=%%c
    set yy=%%d
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
    set hh=%%a
    set min=%%b
)

:: Saat formatını düzelt (tek haneli saatler için başa 0 ekle)
if "%time:~0,1%"==" " set hh=0%hh%

:: Commit mesajı oluştur
set msg=Auto commit %yy%-%mm%-%dd% %hh%:%min%

git add .
git commit -m "%msg%"
git push

echo.
echo ==============================
echo JSON dosyalari GitHub'a gonderildi!
echo Commit mesaji: %msg%
echo ==============================
pause
