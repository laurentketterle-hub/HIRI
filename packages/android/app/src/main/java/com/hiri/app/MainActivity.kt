package com.hiri.app

import kotlinx.coroutines.*
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * HIRI Android client — device control with offline cache.
 *
 * Talks to HIRI-bridge REST at http://10.0.2.2:8780 from emulator,
 * or a configurable LAN address for physical devices.
 */
class MainActivity {
    // ------------------------------------------------------------------
    // Configuration
    // ------------------------------------------------------------------
    private var apiBase: String = "http://10.0.2.2:8780"

    fun apiBase(): String = apiBase
    fun setApiBase(base: String) { apiBase = base.trimEnd('/') }

    // ------------------------------------------------------------------
    // Data classes
    // ------------------------------------------------------------------
    data class HiriDevice(
        val id: String,
        val name: String,
        val domain: String,
        val area: String = "",
        val state: Map<String, Any?> = emptyMap(),
        val adapter: String = "local",
        val online: Boolean = true,
    )

    data class HiriStats(
        val total: Int = 0,
        val online: Int = 0,
        val byDomain: Map<String, Int> = emptyMap(),
    )

    // ------------------------------------------------------------------
    // Offline cache
    // ------------------------------------------------------------------
    private var cachedDevices: List<HiriDevice> = emptyList()
    private var cachedStats: HiriStats = HiriStats()
    private var isOffline: Boolean = false

    fun isCached(): Boolean = cachedDevices.isNotEmpty()
    fun offlineMode(): Boolean = isOffline

    // ------------------------------------------------------------------
    // API
    // ------------------------------------------------------------------
    suspend fun fetchHealth(): Boolean = withContext(Dispatchers.IO) {
        try {
            val conn = URL("$apiBase/health").openConnection() as HttpURLConnection
            conn.connectTimeout = 3000
            conn.readTimeout = 3000
            isOffline = conn.responseCode != 200
            !isOffline
        } catch (e: Exception) {
            isOffline = true
            false
        }
    }

    suspend fun fetchDevices(domain: String? = null, area: String? = null): List<HiriDevice> =
        withContext(Dispatchers.IO) {
            try {
                val params = mutableListOf<String>()
                domain?.let { params.add("domain=$it") }
                area?.let { params.add("area=$it") }
                val qs = if (params.isNotEmpty()) "?" + params.joinToString("&") else ""
                val conn = URL("$apiBase/devices$qs").openConnection() as HttpURLConnection
                conn.connectTimeout = 5000
                conn.readTimeout = 5000
                val text = conn.inputStream.bufferedReader().readText()
                val arr = JSONArray(text)
                val devices = (0 until arr.length()).map { i ->
                    val obj = arr.getJSONObject(i)
                    val stateObj = obj.optJSONObject("state")
                    val state = if (stateObj != null) {
                        stateObj.keys().asSequence().associateWith { k -> stateObj.get(k) }
                    } else emptyMap()
                    HiriDevice(
                        id = obj.getString("id"),
                        name = obj.optString("name", ""),
                        domain = obj.optString("domain", ""),
                        area = obj.optString("area", ""),
                        state = state,
                        adapter = obj.optString("adapter", "local"),
                        online = obj.optBoolean("online", true),
                    )
                }
                cachedDevices = devices
                isOffline = false
                devices
            } catch (e: Exception) {
                isOffline = true
                cachedDevices
            }
        }

    suspend fun fetchStats(): HiriStats = withContext(Dispatchers.IO) {
        try {
            val conn = URL("$apiBase/stats").openConnection() as HttpURLConnection
            conn.connectTimeout = 5000
            conn.readTimeout = 5000
            val text = conn.inputStream.bufferedReader().readText()
            val obj = JSONObject(text)
            val byDomain = obj.optJSONObject("by_domain")
            val domains = if (byDomain != null) {
                byDomain.keys().asSequence().associateWith { k -> byDomain.getInt(k) }
            } else emptyMap()
            cachedStats = HiriStats(
                total = obj.optInt("total", 0),
                online = obj.optInt("online", 0),
                byDomain = domains,
            )
            cachedStats
        } catch (e: Exception) {
            cachedStats
        }
    }

    suspend fun sendCommand(deviceId: String, action: String, data: Map<String, Any?> = emptyMap()): Boolean =
        withContext(Dispatchers.IO) {
            try {
                val payload = JSONObject()
                payload.put("action", action)
                data.forEach { (k, v) -> payload.put(k, v) }
                val conn = URL("$apiBase/devices/${java.net.URLEncoder.encode(deviceId, "UTF-8")}/command")
                    .openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.doOutput = true
                conn.setRequestProperty("Content-Type", "application/json")
                conn.connectTimeout = 5000
                conn.readTimeout = 5000
                conn.outputStream.write(payload.toString().toByteArray())
                conn.responseCode == 200
            } catch (e: Exception) {
                false
            }
        }

    suspend fun turnOn(deviceId: String, extra: Map<String, Any?> = emptyMap()): Boolean =
        sendCommand(deviceId, "turn_on", extra)

    suspend fun turnOff(deviceId: String): Boolean =
        sendCommand(deviceId, "turn_off")

    // ------------------------------------------------------------------
    // Helpers
    // ------------------------------------------------------------------
    fun devicesByRoom(): Map<String, List<HiriDevice>> {
        return cachedDevices.groupBy { it.area.ifEmpty { "home" } }
    }

    fun devicesByDomain(): Map<String, List<HiriDevice>> {
        return cachedDevices.groupBy { it.domain }
    }
}
