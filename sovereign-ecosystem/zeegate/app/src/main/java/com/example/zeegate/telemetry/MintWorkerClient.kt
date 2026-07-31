package com.example.zeegate.telemetry

import android.util.Log
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

object MintWorkerClient {

    private const val TAG = "ZeeGate-MintWorker"

    fun submit(baseUrl: String, payload: JSONObject): Result<String> {
        val normalized = baseUrl.trim().removeSuffix("/")
        if (normalized.isEmpty()) {
            return Result.failure(IllegalStateException("Mint worker URL is not configured"))
        }

        return runCatching {
            val url = URL("$normalized/v1/telemetry")
            val connection = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 15_000
                readTimeout = 30_000
                doOutput = true
                setRequestProperty("Content-Type", "application/json; charset=utf-8")
            }

            try {
                OutputStreamWriter(connection.outputStream, Charsets.UTF_8).use { writer ->
                    writer.write(payload.toString())
                }

                val stream = if (connection.responseCode in 200..299) {
                    connection.inputStream
                } else {
                    connection.errorStream
                }

                val body = BufferedReader(InputStreamReader(stream, Charsets.UTF_8)).use { it.readText() }
                if (connection.responseCode !in 200..299) {
                    throw IllegalStateException("HTTP ${connection.responseCode}: $body")
                }

                Log.i(TAG, "Mint worker accepted telemetry (${connection.responseCode})")
                body
            } finally {
                connection.disconnect()
            }
        }
    }
}
