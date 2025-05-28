@echo off
echo 🔧 Fixing Vue.js build errors...

:: Navigate to public directory
cd public

:: Clean existing installations
echo 🧹 Cleaning existing installations...
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del package-lock.json

:: Clear npm cache
echo 🗑️ Clearing npm cache...
npm cache clean --force

:: Install dependencies
echo 📦 Installing dependencies...
npm install

:: Install missing CSS loaders
echo 🎨 Installing CSS loaders...
npm install --save-dev css-loader vue-style-loader

:: Create vue.config.js if it doesn't exist
if not exist vue.config.js (
  echo ⚙️ Creating vue.config.js...
  (
    echo const { defineConfig } = require('@vue/cli-service'^)
    echo.
    echo module.exports = defineConfig({
    echo   transpileDependencies: true,
    echo   
    echo   css: {
    echo     extract: process.env.NODE_ENV === 'production' ? {
    echo       ignoreOrder: true,
    echo     } : false
    echo   },
    echo.
    echo   configureWebpack: {
    echo     resolve: {
    echo       alias: {
    echo         '@': require('path'^).resolve(__dirname, 'src'^)
    echo       }
    echo     }
    echo   },
    echo.
    echo   devServer: {
    echo     port: 8080,
    echo     host: '0.0.0.0'
    echo   },
    echo.
    echo   publicPath: process.env.NODE_ENV === 'production' ? '/' : '/',
    echo   outputDir: 'dist',
    echo   assetsDir: 'static'
    echo }^)
  ) > vue.config.js
)

:: Try building
echo 🏗️ Attempting build...
npm run build

if %ERRORLEVEL% equ 0 (
  echo ✅ Build successful!
) else (
  echo ❌ Build failed. Trying alternative approach...
  
  :: Remove potentially problematic MDI dependency
  npm uninstall @mdi/font
  
  :: Try building again
  npm run build
  
  if %ERRORLEVEL% equ 0 (
    echo ✅ Build successful after removing @mdi/font!
    echo 📝 Note: Icons are now loaded via CDN in index.html
  ) else (
    echo ❌ Build still failing. Manual intervention required.
    echo 📋 Check the error logs above for specific issues.
  )
)

echo 🏥 Afya Medical EHR build fix completed!
pause