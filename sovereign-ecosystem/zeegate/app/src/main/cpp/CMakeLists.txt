# Sets the minimum CMake version required for this project.
cmake_minimum_required(VERSION 3.22.1)

project("zeegate")

# 1. Define paths for PJSIP
set(PJSIP_DIR ${CMAKE_CURRENT_SOURCE_DIR}/pjsip)
set(PJSIP_LIB_DIR ${PJSIP_DIR}/lib/${ANDROID_ABI})
set(PJSIP_INC_DIR ${PJSIP_DIR}/include)

# 2. Function to import PJSIP static libraries
function(import_pjsip_lib LIB_NAME)
    add_library(${LIB_NAME} STATIC IMPORTED)
    set_target_properties(${LIB_NAME} PROPERTIES
            IMPORTED_LOCATION ${PJSIP_LIB_DIR}/lib${LIB_NAME}-aarch64-unknown-linux-android.a)
endfunction()

# 3. List and import the required PJSIP libraries
# Order matters: dependent libraries must come before their dependencies
set(PJSIP_LIBS
        pjsua2 pjsua pjsip-ua pjsip-simple pjsip
        pjmedia-codec pjmedia-videodev pjmedia-audiodev pjmedia
        pjnath pjlib-util pj
        g7221codec gsmcodec ilbccodec resample speex srtp webrtc yuv)

foreach(LIB ${PJSIP_LIBS})
    import_pjsip_lib(${LIB})
endforeach()

# Find the Oboe package
find_package(oboe REQUIRED CONFIG)

# Creates and names a library, sets it as either SHARED
add_library(${CMAKE_PROJECT_NAME} SHARED
        native-lib.cpp)

# 4. Add PJSIP Include Directories and Defines
target_include_directories(${CMAKE_PROJECT_NAME} PRIVATE ${PJSIP_INC_DIR})
target_compile_definitions(${CMAKE_PROJECT_NAME} PRIVATE
        PJ_HAS_CONFIG_SITE_H=1
        PJ_CONFIG_ANDROID=1
        PJ_IS_LITTLE_ENDIAN=1
        PJ_IS_BIG_ENDIAN=0)

# 5. Link everything
target_link_libraries(${CMAKE_PROJECT_NAME}
        ${PJSIP_LIBS}
        oboe::oboe
        android
        mediandk
        log)
