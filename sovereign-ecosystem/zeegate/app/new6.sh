#!/bin/bash

# --- ZeeGate PJSIP Verification & Build Script ---

echo "Starting Pre-build checks..."

# 1. Check NDK
if [ -z "$ANDROID_NDK_ROOT" ]; then
    export ANDROID_NDK_ROOT="/c/Users/it/AppData/Local/Android/Sdk/ndk/30.0.14904198"
    echo "Defaulting ANDROID_NDK_ROOT to $ANDROID_NDK_ROOT"
fi

# Robust path normalization for MSYS2/Cygwin
# Converts C:\... to /c/... and ensures forward slashes
ANDROID_NDK_ROOT=$(echo "$ANDROID_NDK_ROOT" | sed 's/\\/\//g' | sed 's/\([a-zA-Z]\):/\/\L\1/g')
export ANDROID_NDK_ROOT

# Ensure ANDROID_NDK_HOME is also set
export ANDROID_NDK_HOME="$ANDROID_NDK_ROOT"
export ANDROID_HOME="/c/Users/it/AppData/Local/Android/Sdk"

echo "Using NDK at: $ANDROID_NDK_ROOT"

# Verify the directory exists
if [ ! -d "$ANDROID_NDK_ROOT" ]; then
    echo "ERROR: NDK directory NOT FOUND at $ANDROID_NDK_ROOT"
    echo "Available NDKs in /c/Users/it/AppData/Local/Android/Sdk/ndk/:"
    ls -1 /c/Users/it/AppData/Local/Android/Sdk/ndk/
    exit 1
fi

# Check for ndk-build or ndk-build.cmd
if [ ! -f "$ANDROID_NDK_ROOT/ndk-build" ] && [ ! -f "$ANDROID_NDK_ROOT/ndk-build.cmd" ]; then
    echo "ERROR: ndk-build not found inside $ANDROID_NDK_ROOT"
    exit 1
fi

echo "NDK verified at $ANDROID_NDK_ROOT"

# 2. Navigate to Source
cd /c/Users/it/AndroidStudioProjects/ZeeGate/pjsip_source/pjproject-2.14 || exit 1
echo "Current directory: $(pwd)"

# 3. Verify config_site.h
if [ ! -f "pjlib/include/pj/config_site.h" ]; then
    echo "Creating config_site.h..."
    echo "#define PJ_CONFIG_ANDROID 1" > pjlib/include/pj/config_site.h
    echo "#include <pj/config_site_sample.h>" >> pjlib/include/pj/config_site.h
fi

# 4. Configure
echo "Configuring PJSIP for Android (arm64-v8a) with API 33..."
# Use APP_PLATFORM instead of an unrecognized command line flag
export TARGET_ABI=arm64-v8a
export APP_PLATFORM=android-33

# Run configuration. Note: --with-oboe is supported but may require
# Oboe source/binaries if not found in NDK.
./configure-android --with-oboe

if [ $? -eq 0 ]; then
    echo "Configuration SUCCESS. Starting build..."
    make dep && make clean && make

    echo "Gathering and renaming binaries..."
    TARGET_DIR="/c/Users/it/AndroidStudioProjects/ZeeGate/app/src/main/cpp/pjsip/lib/arm64-v8a"
    mkdir -p "$TARGET_DIR"

    # Find all .a files, copy them, and remove the architecture suffix
    find . -name "*.a" | while read -r lib; do
        filename=$(basename "$lib")
        # Rename libname-arm64-v8a-unknown-linux-android.a to libname.a
        shortname=$(echo "$filename" | sed 's/-arm64-v8a-unknown-linux-android//')
        cp "$lib" "$TARGET_DIR/$shortname"
        echo "Installed: $shortname"
    done

    echo "ZeeGate PJSIP binaries are now ready in the project."
else
    echo "Configuration FAILED."
    exit 1
fi
