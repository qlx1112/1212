[app]

title = FlashCard
package.name = flashcard
package.domain = org.flashcard

source.dir = .
source.include_exts = py,ttc

requirements = python3,kivy

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.ndk = 25b
android.sdk = 24
android.accept_sdk_license = True
