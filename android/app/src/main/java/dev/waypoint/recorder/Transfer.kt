package dev.waypoint.recorder

import android.content.Context
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest
import java.security.SecureRandom
import java.security.cert.X509Certificate
import java.util.concurrent.LinkedBlockingQueue
import java.util.concurrent.TimeUnit
import javax.net.ssl.*

class Transfer(private val context: Context) {
    private val prefs = context.getSharedPreferences("pairing", Context.MODE_PRIVATE)
    private val jsonType = "application/json; charset=utf-8".toMediaType()
    fun client(): OkHttpClient {
        val fingerprint = RecordingFormat.normalizeFingerprint(prefs.getString("fingerprint", "") ?: "")
        val expected = fingerprint.chunked(2).map { it.toInt(16).toByte() }.toByteArray()
        val trust = object : X509TrustManager {
            override fun getAcceptedIssuers(): Array<X509Certificate> = emptyArray()
            override fun checkClientTrusted(chain: Array<X509Certificate>, authType: String) { throw java.security.cert.CertificateException("Client certificates are not supported") }
            override fun checkServerTrusted(chain: Array<X509Certificate>, authType: String) {
                if (chain.isEmpty()) throw java.security.cert.CertificateException("Missing certificate")
                chain[0].checkValidity()
                val actual = MessageDigest.getInstance("SHA-256").digest(chain[0].encoded)
                if (!MessageDigest.isEqual(actual, expected)) throw java.security.cert.CertificateException("Waypoint certificate fingerprint does not match")
            }
        }
        val ssl = SSLContext.getInstance("TLS"); ssl.init(null, arrayOf(trust), SecureRandom())
        val configuredHost = java.net.URI(base()).host
        return OkHttpClient.Builder().sslSocketFactory(ssl.socketFactory, trust)
            .hostnameVerifier { hostname, session ->
                // Certificate identity is explicitly pinned; a private LAN IP need not be in its SAN.
                hostname == configuredHost && try { MessageDigest.isEqual(MessageDigest.getInstance("SHA-256").digest(session.peerCertificates[0].encoded), expected) } catch (_: Exception) { false }
            }.connectTimeout(10, TimeUnit.SECONDS).readTimeout(30, TimeUnit.SECONDS).build()
    }
    private fun base(): String {
        val value = prefs.getString("server", "")!!.trimEnd('/')
        val url = java.net.URI(value)
        require(url.scheme == "https" && !url.host.isNullOrBlank() && url.userInfo == null) { "Use https://COMPUTER-IP:8443" }
        return value
    }
    fun pair(server: String, fingerprint: String, code: String): String {
        prefs.edit().putString("server", server.trim()).putString("fingerprint", RecordingFormat.normalizeFingerprint(fingerprint)).commit()
        val body = JSONObject().put("name", android.os.Build.MODEL).put("code", code.trim())
        val result = request(client(), "/api/v1/device/pair", body, false)
        prefs.all.keys.filter { it.startsWith("ack_") }.forEach { prefs.edit().remove(it).commit() }
        prefs.edit().putString("token", result.getString("token")).putString("device_id", result.getString("device_id")).commit()
        return "Paired securely with your computer"
    }
    private fun request(client: OkHttpClient, path: String, body: JSONObject, authenticated: Boolean = true): JSONObject {
        val builder = Request.Builder().url(base() + path).post(body.toString().toRequestBody(jsonType))
        if (authenticated) builder.header("Authorization", "Bearer " + prefs.getString("token", ""))
        client.newCall(builder.build()).execute().use { response ->
            val value = JSONObject(response.body?.string() ?: "{}")
            if (!response.isSuccessful) throw IllegalStateException(value.optString("detail", "Transfer failed (${response.code})"))
            return value
        }
    }
    fun upload(file: File, live: Boolean = false): Int {
        require(!prefs.getString("token", "").isNullOrBlank()) { "Pair this phone first" }
        val ackKey = "ack_${file.nameWithoutExtension}"
        var next = prefs.getInt(ackKey, 0)
        val finished = File(file.parentFile, file.nameWithoutExtension + ".done").exists()
        // The recorder flushes complete lines before transfer. Ignore a partially written final line.
        val lines = file.readLines().filter { it.startsWith("{") && it.endsWith("}") }
        val total = RecordingFormat.completeBatches(lines.size, finished)
        val http = client()
        var socket: WebSocket? = null
        val replies = LinkedBlockingQueue<JSONObject>()
        try {
            if (live && next < total) {
                socket = http.newWebSocket(Request.Builder().url(base().replaceFirst("https://", "wss://") + "/api/v1/device/stream").build(), object : WebSocketListener() {
                    override fun onOpen(webSocket: WebSocket, response: Response) { webSocket.send(JSONObject().put("token", prefs.getString("token", "")).toString()) }
                    override fun onMessage(webSocket: WebSocket, text: String) { replies.offer(JSONObject(text)) }
                    override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) { replies.offer(JSONObject().put("error", t.message ?: "Disconnected")) }
                })
                val ready = replies.poll(15, TimeUnit.SECONDS) ?: throw IllegalStateException("Live receiver did not answer")
                check(ready.optBoolean("ready")) { ready.optString("error", "Live receiver rejected pairing") }
            }
            while (next < total) {
                val samples = JSONArray()
                lines.subList(next * RecordingFormat.BATCH_SIZE, minOf((next + 1) * RecordingFormat.BATCH_SIZE, lines.size)).forEach { samples.put(JSONObject(it)) }
                val body = JSONObject().put("version", 1).put("session_id", file.nameWithoutExtension).put("sequence", next).put("samples", samples).put("metadata", JSONObject().put("device", android.os.Build.MODEL).put("requested_imu_hz", 100))
                val response = if (socket != null) { socket.send(body.toString()); replies.poll(30, TimeUnit.SECONDS) ?: throw IllegalStateException("Acknowledgment timeout") } else request(http, "/api/v1/device/batches", body)
                check(response.optInt("ack", -1) == next) { response.optString("error", "Batch was not acknowledged") }
                next++; prefs.edit().putInt(ackKey, next).commit()
            }
        } finally { socket?.close(1000, "Transfer complete"); http.dispatcher.executorService.shutdown() }
        return next
    }
}
