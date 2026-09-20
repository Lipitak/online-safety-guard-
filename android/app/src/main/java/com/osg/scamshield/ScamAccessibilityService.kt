package com.osg.scamshield

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Intent
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.widget.Toast
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

class ScamAccessibilityService : AccessibilityService() {

    private val executor = Executors.newSingleThreadExecutor()
    private val handler = Handler(Looper.getMainLooper())
    private var lastProcessedText: String = ""
    private var lastScanTime: Long = 0L

    companion object {
        private const val TAG = "ScamAccessibility"
        private const val DEBOUNCE_MS = 600L
        // Backend IP URL (e.g., http://10.0.2.2:5001/detect for Android Emulator, or server IP)
        const val BACKEND_URL = "http://10.0.2.2:5001/detect"

        val TARGET_PACKAGES = setOf(
            "com.whatsapp",
            "org.telegram.messenger",
            "com.linkedin.android",
            "com.naukri.app",
            "com.google.android.gm",
            "com.android.chrome",
            "com.google.android.apps.messaging",
            "com.samsung.android.messaging"
        )
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        Log.i(TAG, "🛡️ ScamShield Accessibility Service Connected & Monitoring 24/7.")
        val info = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED or AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS or AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
            notificationTimeout = 200
        }
        this.serviceInfo = info
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return
        val packageName = event.packageName?.toString() ?: return

        // Filter target packages
        if (!TARGET_PACKAGES.contains(packageName)) return

        val currentTime = System.currentTimeMillis()
        if (currentTime - lastScanTime < DEBOUNCE_MS) return
        lastScanTime = currentTime

        val rootNode = rootInActiveWindow ?: return
        val extractedText = StringBuilder()
        extractNodeText(rootNode, extractedText)
        val textContent = extractedText.toString().trim()

        if (textContent.isEmpty() || textContent == lastProcessedText || textContent.length < 10) {
            return
        }
        lastProcessedText = textContent

        Log.d(TAG, "Captured screen content from [$packageName]: ${textContent.take(60)}...")
        sendToBackend(textContent, packageName)
    }

    private fun extractNodeText(node: AccessibilityNodeInfo?, sb: StringBuilder) {
        if (node == null) return
        if (!node.text.isNull me.isEmpty()) {
            sb.append(node.text).append(" ")
        }
        if (!node.contentDescription.isNullOrEmpty()) {
            sb.append(node.contentDescription).append(" ")
        }
        for (i in 0 until node.childCount) {
            extractNodeText(node.getChild(i), sb)
        }
    }

    private fun sendToBackend(text: String, packageName: String) {
        executor.execute {
            try {
                val url = URL(BACKEND_URL)
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json")
                conn.doOutput = true
                conn.connectTimeout = 3000
                conn.readTimeout = 3000

                val payload = JSONObject().apply {
                    put("text", text)
                    put("package_name", packageName)
                    put("source_app", packageName)
                }

                val writer = OutputStreamWriter(conn.outputStream)
                writer.write(payload.toString())
                writer.flush()
                writer.close()

                if (conn.responseCode == 200) {
                    val responseStr = conn.inputStream.bufferedReader().use { it.readText() }
                    val json = JSONObject(responseStr)
                    val isScam = json.optBoolean("is_scam", false)
                    val severity = json.optString("severity", "none")
                    val category = json.optString("category", "generic")
                    val reason = json.optString("reason", "Scam detected")

                    if (isScam) {
                        handler.post {
                            handleScamAlert(severity, category, reason, json, packageName, text)
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Backend scan connection error: ${e.message}")
            }
        }
    }

    private fun handleScamAlert(
        severity: String,
        category: String,
        reason: String,
        json: JSONObject,
        packageName: String,
        rawText: String
    ) {
        if (severity == "critical") {
            Log.w(TAG, "🚨 CRITICAL ALERT TRIGGERED for app [$packageName]")

            val spokenObj = json.optJSONObject("spoken_warning")
            val warningLocal = spokenObj?.optString("text_local") ?: "सावधान! यह एक बैंकिंग धोखाधड़ी है। तुरंत बंद करें!"
            val speechLang = spokenObj?.optString("speech_lang") ?: "hi-IN"

            // Start Full-Screen Red Alert Overlay Service
            val overlayIntent = Intent(this, CriticalAlertOverlayService::class.java).apply {
                putExtra("reason", reason)
                putExtra("category", category)
                putExtra("warning_local", warningLocal)
                putExtra("speech_lang", speechLang)
                putExtra("raw_text", rawText)
            }
            startService(overlayIntent)

        } else {
            // MODERATE SEVERITY: Non-intrusive Toast / Badge highlight
            Log.i(TAG, "⚠️ MODERATE SCAM FLAGGED for app [$packageName]: $reason")
            Toast.makeText(
                applicationContext,
                "⚠️ ScamShield Flag: $reason",
                Toast.LENGTH_LONG
            ).show()
        }
    }

    override fun onInterrupt() {
        Log.w(TAG, "ScamShield Accessibility Service Interrupted.")
    }
}
