package com.hiri.app.data

data class Device(
    val id: String,
    val name: String,
    val domain: String,
    val manufacturer: String = "HIRI",
    val model: String = "generic",
    val area: String = "home",
    val online: Boolean = true,
    val state: Map<String, Any> = emptyMap(),
    val attributes: Map<String, Any> = emptyMap(),
    val adapter: String = "local"
)
