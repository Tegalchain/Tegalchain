package com.example.zeegate

import com.example.zeegate.telemetry.GreTelemetry
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class GreTelemetryTest {

    @Test
    fun unsignedCanonical_matchesPythonSortOrder() {
        val canonical = GreTelemetry.unsignedCanonicalJson(
            nodeId = "zerocell-node-001",
            timestampSec = 1_700_000_000L,
            bandwidthBytes = 4096L,
        )
        assertEquals(
            """{"metrics":{"telecom_bandwidth_bytes":4096},"node_id":"zerocell-node-001","system_type":"ZEEGATE_TELECOM","timestamp":1700000000}""",
            canonical,
        )
    }

    @Test
    fun signature_matchesPythonInteropVector() {
        val unsigned = GreTelemetry.unsignedCanonicalJson(
            nodeId = "zerocell-node-001",
            timestampSec = 1_700_000_000L,
            bandwidthBytes = 4096L,
        )
        assertEquals(
            "hmac-sha256:29a7cf5a7d8fc93017c0b5071063de44db10622a3b0a8b9439944b31e7e26d2c",
            GreTelemetry.sign(unsigned),
        )
    }

    @Test
    fun buildSignedPayload_includesAllRequiredFields() {
        val payload = GreTelemetry.buildSignedPayload(
            nodeId = "zerocell-node-001",
            timestampSec = 1_700_000_000L,
            bandwidthBytes = 1024L,
        )
        assertEquals("zerocell-node-001", payload.getString("node_id"))
        assertEquals("ZEEGATE_TELECOM", payload.getString("system_type"))
        assertEquals(1024L, payload.getJSONObject("metrics").getLong("telecom_bandwidth_bytes"))
        assertTrue(payload.getString("signature").startsWith("hmac-sha256:"))
    }
}
