package com.example.zeegate.telemetry

import org.json.JSONObject
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

/**
 * Builds greentelemetry-protocol-spec v1.0.0 payloads for Zerocell Zeegate.
 * Signing matches greentelemetry_protocol_spec/signing.py (unsigned canonical JSON + HMAC-SHA256).
 */
object GreTelemetry {

    const val SYSTEM_TYPE = "ZEEGATE_TELECOM"
    private const val HMAC_SECRET = "sovereign-ecosystem-dev-key"

    fun unsignedCanonicalJson(nodeId: String, timestampSec: Long, bandwidthBytes: Long): String {
        require(nodeId.isNotBlank()) { "node_id must be non-empty" }
        require(bandwidthBytes >= 0) { "telecom_bandwidth_bytes must be non-negative" }
        val escapedNodeId = JSONObject.quote(nodeId)
        return (
            """{"metrics":{"telecom_bandwidth_bytes":$bandwidthBytes},"node_id":$escapedNodeId,""" +
                """"system_type":"$SYSTEM_TYPE","timestamp":$timestampSec}"""
            )
    }

    fun sign(unsignedCanonical: String): String {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(HMAC_SECRET.toByteArray(Charsets.UTF_8), "HmacSHA256"))
        val digest = mac.doFinal(unsignedCanonical.toByteArray(Charsets.UTF_8))
        val hex = digest.joinToString("") { byte -> "%02x".format(byte) }
        return "hmac-sha256:$hex"
    }

    fun buildSignedPayload(nodeId: String, timestampSec: Long, bandwidthBytes: Long): JSONObject {
        val unsigned = unsignedCanonicalJson(nodeId, timestampSec, bandwidthBytes)
        val signature = sign(unsigned)
        return JSONObject(unsigned).put("signature", signature)
    }
}
