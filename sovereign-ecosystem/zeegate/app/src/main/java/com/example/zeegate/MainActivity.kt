package com.example.zeegate

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.view.View
import androidx.core.content.ContextCompat
import com.example.zeegate.databinding.ActivityMainBinding
import com.topjohnwu.superuser.Shell
import java.io.File

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Initialize libsu with context
        Shell.setDefaultBuilder(
            Shell.Builder.create()
                .setContext(this),
        )

        performDiagnostic()

        // Start Telemetry Service (greentelemetry → mint worker)
        TelemetryService.configure(
            nodeId = null,
            mintWorkerUrl = null,
        )
        startService(Intent(this, TelemetryService::class.java))

        // Initialize AnyFi Software-Defined Networking
        initializeAnyFi()
    }

    private fun performDiagnostic() {
        val myUid = android.os.Process.myUid()
        val isRooted = Shell.getShell().isRoot
        val ksuPresent = checkIfKernelSUPresent()
        
        val permissions = arrayOf(
            Manifest.permission.CAPTURE_AUDIO_OUTPUT,
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.MODIFY_PHONE_STATE,
        )
        val allPermsGranted = permissions.all { 
            ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED 
        }

        // 1. UID Check
        if (myUid == 1000) {
            binding.statusUid.text = getString(R.string.uid_ok)
            binding.statusUid.setTextColor(ContextCompat.getColor(this, android.R.color.holo_green_dark))
        } else {
            binding.statusUid.text = getString(R.string.uid_fail, myUid)
            binding.statusUid.setTextColor(ContextCompat.getColor(this, android.R.color.holo_red_dark))
            showOnboarding(getString(R.string.onboarding_uid_text))
        }

        // 2. KernelSU Check
        if (ksuPresent) {
            binding.statusKsu.text = getString(R.string.ksu_ok)
            binding.statusKsu.setTextColor(ContextCompat.getColor(this, android.R.color.holo_green_dark))
        } else {
            binding.statusKsu.text = getString(R.string.ksu_fail)
            binding.statusKsu.setTextColor(ContextCompat.getColor(this, android.R.color.holo_red_dark))
            showOnboarding(getString(R.string.onboarding_ksu_text))
        }

        // 3. Root Check
        if (isRooted) {
            binding.statusRoot.text = getString(R.string.root_ok)
            binding.statusRoot.setTextColor(ContextCompat.getColor(this, android.R.color.holo_green_dark))
            
            // If rooted, perform system patches
            applyAudioConcurrencyPatches()
            installKernelSUModule()
        } else {
            binding.statusRoot.text = getString(R.string.root_fail)
            binding.statusRoot.setTextColor(ContextCompat.getColor(this, android.R.color.holo_red_dark))
            if (ksuPresent) {
                showOnboarding(getString(R.string.onboarding_root_text))
            }
        }

        // 4. Permissions Check
        if (allPermsGranted) {
            binding.statusPermissions.text = getString(R.string.perm_ok)
            binding.statusPermissions.setTextColor(ContextCompat.getColor(this, android.R.color.holo_green_dark))
        } else {
            binding.statusPermissions.text = getString(R.string.perm_fail)
            binding.statusPermissions.setTextColor(ContextCompat.getColor(this, android.R.color.holo_red_dark))
        }

        // 5. Component Check
        val oboeStatus = stringFromJNI()
        binding.statusOboe.text = getString(R.string.oboe_format, oboeStatus)
        
        val blockchainStatus = try {
            bridge.Bridge.getStatus()
        } catch (_: Exception) {
            "Disconnected"
        }
        binding.statusBlockchain.text = getString(R.string.blockchain_format, blockchainStatus)
    }

    private fun showOnboarding(message: String) {
        binding.onboardingCard.visibility = View.VISIBLE
        binding.onboardingText.text = message
    }

    private fun initializeAnyFi() {
        try {
            // AnyFi SDK initialization placeholder
            android.util.Log.d("ZeeGate-AnyFi", "AnyFi Mesh Networking Initialized")
        } catch (e: Exception) {
            android.util.Log.e("ZeeGate-AnyFi", "AnyFi Init Failed", e)
        }
    }

    private fun checkIfKernelSUPresent(): Boolean {
        return try {
            File("/proc/devices").readText().contains("kernelsu")
        } catch (_: Exception) {
            false
        }
    }

    private fun applyAudioConcurrencyPatches() {
        Shell.cmd(
            "setprop voice.voip.conc.disabled false",
            "setprop voice.record.conc.disabled false",
            "setprop voice.playback.conc.disabled false",
            "setprop persist.vendor.audio.voip.concurrency true",
            "setprop persist.vendor.audio.record.concurrency true",
        ).submit()
    }

    private fun installKernelSUModule(): Boolean {
        val moduleId = "zeegate_audio"
        val moduleDir = "/data/adb/modules/$moduleId"
        val vendorEtc = "$moduleDir/system/vendor/etc"
        
        val commands = mutableListOf(
            "mkdir -p $vendorEtc",
            "echo \"id=$moduleId\" > $moduleDir/module.prop",
            "echo \"name=ZeeGate Audio Gateway\" >> $moduleDir/module.prop",
            "echo \"version=v1.0\" >> $moduleDir/module.prop",
            "echo \"versionCode=1\" >> $moduleDir/module.prop",
            "echo \"author=ZeeGate\" >> $moduleDir/module.prop",
            "echo \"description=Enables Audio Concurrency and In-Call Music flags.\" >> $moduleDir/module.prop",
            "cp /vendor/etc/audio_policy_configuration.xml $vendorEtc/audio_policy_configuration.xml",
            "sed -i '/mixPort name=\"primary output\"/,/\\/mixPort/ s/flags=\"[^\"]*\"/&|AUDIO_OUTPUT_FLAG_INCALL_MUSIC/' $vendorEtc/audio_policy_configuration.xml",
            "touch $moduleDir/update"
        )
        return Shell.cmd(*commands.toTypedArray()).exec().isSuccess
    }

    external fun stringFromJNI(): String
    external fun initPjsip(server: String, user: String, pass: String): Boolean
    external fun getEngineTelemetry(): String

    companion object {
        init {
            System.loadLibrary("zeegate")
        }
    }
}
