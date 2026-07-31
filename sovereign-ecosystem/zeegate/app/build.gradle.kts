plugins {
    alias(libs.plugins.android.application)
}

android {
    namespace = "com.example.zeegate"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.zeegate"
        minSdk = 33
        targetSdk = 35
        versionCode = 2
        versionName = "1.1.0" // Zeegate v1 (generation 1) — see zeegate/VERSION

        buildConfigField("int", "ZEEGATE_GENERATION", "1")
        buildConfigField("String", "GREETELEMETRY_PROTOCOL_VERSION", "\"1.0.0\"")
        buildConfigField("String", "DEFAULT_NODE_ID", "\"zerocell-node-001\"")
        // Emulator → host mint worker; override via TelemetryService.configure() or product flavor.
        buildConfigField("String", "MINT_WORKER_BASE_URL", "\"http://10.0.2.2:8090\"")

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        externalNativeBuild {
            cmake {
                arguments("-DANDROID_STL=c++_shared", "-DPJ_CONFIG_ANDROID=1")
                abiFilters("arm64-v8a")
            }
        }
    }

    buildTypes {
        release {
            optimization {
                enable = false
            }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }
    buildFeatures {
        viewBinding = true
        prefab = true
        buildConfig = true
    }
}

dependencies {
    implementation(fileTree(mapOf("dir" to "libs", "include" to listOf("*.aar"))))
    // AnyFi SDK Placeholder - Replace with actual coordinate if available
    // implementation("io.anyfi:anyfi-sdk:latest.version")

    implementation(libs.libsu.core)
    implementation("com.google.oboe:oboe:1.10.0")
    implementation(libs.androidx.appcompat)
    implementation(libs.androidx.constraintlayout)
    implementation(libs.androidx.core.ktx)
    implementation(libs.material)
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.junit)
}
