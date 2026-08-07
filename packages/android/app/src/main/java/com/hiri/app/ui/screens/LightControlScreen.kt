package com.hiri.app.ui.screens

import android.widget.Toast
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.hiri.app.data.Device
import com.hiri.app.network.ApiService
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LightControlScreen(
    device: Device,
    api: ApiService,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var isOn by remember {
        mutableStateOf((device.state["state"] as? String) == "on")
    }
    var brightness by remember {
        mutableStateOf((device.state["brightness"] as? Double)?.toFloat() ?: 128f)
    }
    var loading by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(device.name) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back")
                    }
                },
                actions = {
                    IconButton(onClick = {
                        scope.launch {
                            loading = true
                            try {
                                val updated = api.sendCommand(
                                    device.id, mapOf("action" to "query")
                                )
                                isOn = (updated.state["state"] as? String) == "on"
                            } catch (e: Exception) {
                                Toast.makeText(context, e.message, Toast.LENGTH_SHORT).show()
                            } finally {
                                loading = false
                            }
                        }
                    }) {
                        Icon(Icons.Default.Refresh, "Refresh state")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier.fillMaxSize().padding(padding).padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Card(modifier = Modifier.fillMaxWidth()) {
                Row(
                    modifier = Modifier.padding(16.dp).fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        if (isOn) Icons.Default.Lightbulb else Icons.Default.LightbulbOutline,
                        contentDescription = null,
                        tint = if (isOn) MaterialTheme.colorScheme.tertiary
                               else MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(48.dp)
                    )
                    Spacer(modifier = Modifier.width(16.dp))
                    Text("Power", style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.weight(1f))
                    Switch(
                        checked = isOn,
                        onCheckedChange = { newValue ->
                            scope.launch {
                                loading = true
                                try {
                                    val action = if (newValue) "turn_on" else "turn_off"
                                    api.sendCommand(device.id, mapOf("action" to action))
                                    isOn = newValue
                                } catch (e: Exception) {
                                    Toast.makeText(context, e.message, Toast.LENGTH_SHORT).show()
                                } finally { loading = false }
                            }
                        },
                        enabled = !loading && device.online
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            if (isOn) {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Brightness", style = MaterialTheme.typography.titleMedium)
                        Spacer(modifier = Modifier.height(8.dp))
                        Slider(value = brightness, onValueChange = { brightness = it },
                            valueRange = 1f..255f, steps = 253)
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(brightness.toInt().toString() + "/255",
                                style = MaterialTheme.typography.bodySmall)
                            Button(onClick = {
                                scope.launch {
                                    loading = true
                                    try {
                                        api.sendCommand(device.id, mapOf(
                                            "action" to "turn_on",
                                            "data" to mapOf("brightness" to brightness.toInt())
                                        ))
                                    } catch (e: Exception) {
                                        Toast.makeText(context, e.message,
                                            Toast.LENGTH_SHORT).show()
                                    } finally { loading = false }
                                }
                            }, enabled = !loading) {
                                Text("Apply")
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Device Info", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(8.dp))
                    InfoRow("ID", device.id)
                    InfoRow("Domain", device.domain)
                    InfoRow("Area", device.area)
                    InfoRow("Adapter", device.adapter)
                    InfoRow("Manufacturer", device.manufacturer)
                }
            }

            if (loading) {
                Spacer(modifier = Modifier.height(16.dp))
                LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
            }
        }
    }
}

@Composable
private fun InfoRow(label: String, value: String) {
    Row(modifier = Modifier.padding(vertical = 2.dp)) {
        Text(label + ": ",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(value, style = MaterialTheme.typography.bodyMedium)
    }
}
