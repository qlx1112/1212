[app]

package.name = mykivyapp
package.domain = org.mykivyapp
title = MyKivyApp
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.api = 33
android.ndk = 25b

android.private_api = False
android.ndk_path =
android.ant_path =
android.accept_sdk_license = True

android.enable_androidx = True
android.permissions = INTERNET,ACCESS_NETWORK_STATE

[buildozer]
log_level = 2
warn_on_root = 1
