package com.hiri.app.network

import com.hiri.app.data.Device
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import java.util.concurrent.TimeUnit

interface ApiService {
    @GET("/devices")
    suspend fun getDevices(): List<Device>

    @POST("/devices/{id}/command")
    suspend fun sendCommand(
        @Path("id") deviceId: String,
        @Body body: Map<String, Any>
    ): Device

    companion object {
        private const val DEFAULT_BASE = "http://10.0.2.2:8780"

        fun create(baseUrl: String = DEFAULT_BASE): ApiService {
            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }
            val client = OkHttpClient.Builder()
                .addInterceptor(logging)
                .connectTimeout(10, TimeUnit.SECONDS)
                .readTimeout(10, TimeUnit.SECONDS)
                .build()

            return Retrofit.Builder()
                .baseUrl(baseUrl)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
                .create(ApiService::class.java)
        }
    }
}
