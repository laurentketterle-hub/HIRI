package com.hiri.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.*
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.hiri.app.data.Device
import com.hiri.app.network.ApiService
import com.hiri.app.ui.screens.DeviceListScreen
import com.hiri.app.ui.screens.LightControlScreen
import com.hiri.app.ui.theme.HiriTheme
import com.google.gson.Gson
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val api = ApiService.create()
        setContent {
            HiriTheme {
                val navController = rememberNavController()
                NavHost(navController = navController, startDestination = "devices") {
                    composable("devices") {
                        DeviceListHost(api = api, onDeviceClick = { device ->
                            val json = Gson().toJson(device)
                            navController.navigate("device/$json")
                        })
                    }
                    composable("device/{deviceJson}") { backStackEntry ->
                        val json = backStackEntry.arguments?.getString("deviceJson") ?: ""
                        val device = Gson().fromJson(json, Device::class.java)
                        LightControlScreen(
                            device = device,
                            api = api,
                            onBack = { navController.popBackStack() }
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun DeviceListHost(api: ApiService, onDeviceClick: (Device) -> Unit) {
    var devices by remember { mutableStateOf<List<Device>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    fun load() {
        scope.launch {
            loading = true
            error = null
            try {
                devices = api.getDevices()
            } catch (e: Exception) {
                error = e.message ?: "Unknown error"
            } finally {
                loading = false
            }
        }
    }

    LaunchedEffect(Unit) { load() }

    DeviceListScreen(
        devices = devices,
        loading = loading,
        error = error,
        onRefresh = { load() },
        onDeviceClick = onDeviceClick
    )
}
