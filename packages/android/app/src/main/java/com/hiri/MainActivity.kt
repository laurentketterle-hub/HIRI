package com.hiri

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.net.HttpURLConnection
import java.net.URL

@Serializable
data class HiriDevice(
    val id: String,
    val name: String,
    val type: String,
    val state: String,
    val battery: Int? = null
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { HiriApp() }
    }
}

@Composable
fun HiriApp() {
    val scope = rememberCoroutineScope()
    var devices by remember { mutableStateOf<List<HiriDevice>>(emptyList()) }
    var token by remember { mutableStateOf("") }

    LaunchedEffect(Unit) {
        scope.launch {
            try {
                val url = URL("http://hiri.local:8080/api/devices")
                val conn = url.openConnection() as HttpURLConnection
                if (token.isNotEmpty()) conn.setRequestProperty("Authorization", "Bearer $token")
                val text = conn.inputStream.bufferedReader().readText()
                devices = Json.decodeFromString(text)
            } catch (_: Exception) {}
        }
    }

    MaterialTheme {
        Scaffold(topBar = { TopAppBar(title = { Text("HIRI Devices") }) }) { padding ->
            LazyColumn(modifier = Modifier.padding(padding)) {
                items(devices) { device ->
                    ListItem(
                        headlineContent = { Text(device.name) },
                        supportingContent = { Text("${device.type} · ${device.state}") },
                        trailingContent = {
                            if (device.type in listOf("light", "switch")) {
                                Switch(checked = device.state == "on", onCheckedChange = { /* toggle via API */ })
                            }
                        }
                    )
                    HorizontalDivider()
                }
            }
        }
    }
}
