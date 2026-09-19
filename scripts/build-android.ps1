param([string]$JavaPath='C:\Program Files\Java\jdk-23')
$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:JAVA_HOME=$JavaPath
$env:ANDROID_HOME=(Resolve-Path .tools/android-sdk).Path
$sdkPath = $env:ANDROID_HOME.Replace('\','/')
Set-Content -LiteralPath android/local.properties -Value "sdk.dir=$sdkPath" -Encoding ascii
& .tools/gradle-8.11.1/bin/gradle.bat -p android assembleDebug testDebugUnitTest --no-daemon --console=plain
if ($LASTEXITCODE) { throw 'Android build or tests failed' }
Copy-Item -LiteralPath android/app/build/outputs/apk/debug/app-debug.apk -Destination artifacts/waypoint-recorder.apk -Force
