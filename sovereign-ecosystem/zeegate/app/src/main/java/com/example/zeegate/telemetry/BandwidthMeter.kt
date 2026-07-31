package com.example.zeegate.telemetry

import android.net.TrafficStats
import android.os.Process

/**
 * Accumulates UID network rx+tx bytes for telecom_bandwidth_bytes reporting.
 * AnyFi relay and SIP/media traffic share the app UID on the gateway device.
 */
class BandwidthMeter {

    private var lastRx: Long = -1L
    private var lastTx: Long = -1L
    private var sessionBytes: Long = 0L

    fun sampleAndGetTotalBytes(): Long {
        val uid = Process.myUid()
        val rx = TrafficStats.getUidRxBytes(uid)
        val tx = TrafficStats.getUidTxBytes(uid)

        if (rx >= 0 && tx >= 0) {
            if (lastRx >= 0 && lastTx >= 0) {
                val deltaRx = (rx - lastRx).coerceAtLeast(0)
                val deltaTx = (tx - lastTx).coerceAtLeast(0)
                sessionBytes += deltaRx + deltaTx
            }
            lastRx = rx
            lastTx = tx
        }

        return sessionBytes
    }
}
