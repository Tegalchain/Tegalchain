package com.example.zeegate

import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.util.Log
import com.example.zeegate.telemetry.BandwidthMeter
import com.example.zeegate.telemetry.GreTelemetry
import com.example.zeegate.telemetry.MintWorkerClient
import java.util.Timer
import kotlin.concurrent.timerTask

class TelemetryService : Service() {

    private var timer: Timer? = null
    private val tag = "ZeeGate-Telemetry"
    private val bandwidthMeter = BandwidthMeter()

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.i(tag, "Telemetry Service Started (greentelemetry ${BuildConfig.GREETELEMETRY_PROTOCOL_VERSION})")
        startReporting()
        return START_STICKY
    }

    private fun startReporting() {
        timer?.cancel()
        timer = Timer()
        timer?.schedule(
            timerTask { gatherAndReport() },
            5_000L,
            30_000L,
        )
    }

    private fun gatherAndReport() {
        try {
            val nodeId = resolveNodeId()
            val timestampSec = System.currentTimeMillis() / 1000L
            val bandwidthBytes = bandwidthMeter.sampleAndGetTotalBytes()

            val payload = GreTelemetry.buildSignedPayload(
                nodeId = nodeId,
                timestampSec = timestampSec,
                bandwidthBytes = bandwidthBytes,
            )

            val mintUrl = resolveMintWorkerUrl()
            if (mintUrl.isNullOrBlank()) {
                Log.w(tag, "MINT_WORKER_URL not set; payload ready: $payload")
                return
            }

            MintWorkerClient.submit(mintUrl, payload)
                .onSuccess { response ->
                    Log.i(tag, "Greentelemetry mint response: $response")
                }
                .onFailure { error ->
                    Log.e(tag, "Mint worker submission failed", error)
                }
        } catch (error: Exception) {
            Log.e(tag, "Telemetry cycle failed", error)
        }
    }

    private fun resolveNodeId(): String {
        val fromIntent = pendingNodeId
        if (!fromIntent.isNullOrBlank()) {
            return fromIntent
        }
        return BuildConfig.DEFAULT_NODE_ID
    }

    private fun resolveMintWorkerUrl(): String? {
        val fromIntent = pendingMintWorkerUrl
        if (!fromIntent.isNullOrBlank()) {
            return fromIntent
        }
        val configured = BuildConfig.MINT_WORKER_BASE_URL.trim()
        return configured.ifBlank { null }
    }

    override fun onDestroy() {
        timer?.cancel()
        super.onDestroy()
    }

    companion object {
        private var pendingNodeId: String? = null
        private var pendingMintWorkerUrl: String? = null

        fun configure(nodeId: String?, mintWorkerUrl: String?) {
            pendingNodeId = nodeId
            pendingMintWorkerUrl = mintWorkerUrl
        }
    }
}
