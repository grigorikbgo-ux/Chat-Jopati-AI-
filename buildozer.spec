[app]
title = Jopati AI
package.name = jopati_pro
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

# ВАЖНО: Список библиотек для работы кода #33
requirements = python3,kivy==2.2.1,requests,urllib3,certifi,idna,charset-normalizer

orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
fullscreen = 0

# Разрешения
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = armeabi-v7a, arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
