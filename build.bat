@echo off
echo ========================================================
echo   Nexus File Manager - Desktop Packaging Tool
echo ========================================================
echo.
echo Installing requirements...
pip install -r requirements.txt
echo.
echo Generating app icons...
python create_icon.py
echo.
echo Compiling Standalone Executable...
python build_app.py
echo.
echo Build process complete. Check dist\NexusFileManager\NexusFileManager.exe
pause
