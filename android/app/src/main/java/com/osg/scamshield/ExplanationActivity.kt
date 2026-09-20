package com.osg.scamshield

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.util.Log
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

class ExplanationActivity : Activity() {

    private val executor = Executors.newSingleThreadExecutor()
    private lateinit var mainLayout: LinearLayout

    companion object {
        private const val TAG = "ExplanationActivity"
        const val EXPLAIN_URL = "http://10.0.2.2:5001/explain"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate()

        val category = intent.getStringExtra("category") ?: "generic"
        val rawText = intent.getStringExtra("raw_text") ?: ""

        val scrollView = ScrollView(this)
        mainLayout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            padding = 48
            setBackgroundColor(Color.parseColor("#0B0F19"))
        }
        scrollView.addView(mainLayout)
        setContentView(scrollView)

        renderLoadingUI()
        fetchExplanation(category, rawText)
    }

    private fun renderLoadingUI() {
        mainLayout.removeAllViews()
        val title = TextView(this).apply {
            text = "🛡️ ScamShield AI Post-Mortem Analysis"
            textSize = 20f
            setTextColor(Color.WHITE)
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            setPadding(0, 0, 0, 24)
        }
        val loading = TextView(this).apply {
            text = "🔍 Analyzing threat triggers, user vulnerabilities, and remediation steps..."
            textSize = 14f
            setTextColor(Color.LTGRAY)
        }
        mainLayout.addView(title)
        mainLayout.addView(loading)
    }

    private fun fetchExplanation(category: String, rawText: String) {
        executor.execute {
            try {
                val url = URL(EXPLAIN_URL)
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json")
                conn.doOutput = true
                conn.connectTimeout = 3000
                conn.readTimeout = 3000

                val payload = JSONObject().apply {
                    put("text", rawText)
                    put("category", category)
                }

                val writer = OutputStreamWriter(conn.outputStream)
                writer.write(payload.toString())
                writer.flush()
                writer.close()

                if (conn.responseCode == 200) {
                    val responseStr = conn.inputStream.bufferedReader().use { it.readText() }
                    val json = JSONObject(responseStr)
                    runOnUiThread { renderExplanationUI(json) }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error fetching explanation: ${e.message}")
                runOnUiThread { renderErrorUI(e.message ?: "Failed to reach server") }
            }
        }
    }

    private fun renderExplanationUI(json: JSONObject) {
        mainLayout.removeAllViews()

        val titleTv = TextView(this).apply {
            text = json.optString("threat_title", "Security Post-Mortem Report")
            textSize = 22f
            setTextColor(Color.parseColor("#E8641C"))
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            setPadding(0, 0, 0, 16)
        }

        val summaryTv = TextView(this).apply {
            text = json.optString("threat_summary", "Threat detected.")
            textSize = 14f
            setTextColor(Color.WHITE)
            setPadding(0, 0, 0, 24)
        }

        // Section 1: User Security Mistakes
        val userMistakesTitle = createSectionTitle("1. User Security Mistakes Identified")
        val userMistakesBox = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#1F180F"))
            setPadding(24, 24, 24, 24)
        }
        val userMistakesArr = json.optJSONArray("user_mistakes")
        if (userMistakesArr != null) {
            for (i in 0 until userMistakesArr.length()) {
                val item = TextView(this).apply {
                    text = "⚠️ ${userMistakesArr.getString(i)}"
                    setTextColor(Color.parseColor("#FCA5A5"))
                    textSize = 13.5f
                    setPadding(0, 4, 0, 4)
                }
                userMistakesBox.addView(item)
            }
        }

        // Section 2: System / Security Gaps
        val systemGapsTitle = createSectionTitle("2. System & Network Security Gaps")
        val systemGapsBox = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#111827"))
            setPadding(24, 24, 24, 24)
        }
        val systemGapsArr = json.optJSONArray("system_gaps")
        if (systemGapsArr != null) {
            for (i in 0 until systemGapsArr.length()) {
                val item = TextView(this).apply {
                    text = "🌐 ${systemGapsArr.getString(i)}"
                    setTextColor(Color.parseColor("#93C5FD"))
                    textSize = 13.5f
                    setPadding(0, 4, 0, 4)
                }
                systemGapsBox.addView(item)
            }
        }

        // Section 3: Actionable Step-by-Step Remediation Plan
        val remediationTitle = createSectionTitle("3. Step-by-Step Fixes & Solutions")
        val remediationBox = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#062312"))
            setPadding(24, 24, 24, 24)
        }
        val stepsArr = json.optJSONArray("remediation_steps")
        if (stepsArr != null) {
            for (i in 0 until stepsArr.length()) {
                val item = TextView(this).apply {
                    text = "✅ ${stepsArr.getString(i)}"
                    setTextColor(Color.parseColor("#86EFAC"))
                    textSize = 13.5f
                    setPadding(0, 6, 0, 6)
                }
                remediationBox.addView(item)
            }
        }

        val btnClose = Button(this).apply {
            text = "🛡️ ACKNOWLEDGE & RETURN"
            setBackgroundColor(Color.parseColor("#22C55E"))
            setTextColor(Color.BLACK)
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            setOnClickListener { finish() }
        }

        mainLayout.addView(titleTv)
        mainLayout.addView(summaryTv)
        mainLayout.addView(userMistakesTitle)
        mainLayout.addView(userMistakesBox)
        mainLayout.addView(createSpacer())
        mainLayout.addView(systemGapsTitle)
        mainLayout.addView(systemGapsBox)
        mainLayout.addView(createSpacer())
        mainLayout.addView(remediationTitle)
        mainLayout.addView(remediationBox)
        mainLayout.addView(createSpacer())
        mainLayout.addView(btnClose)
    }

    private fun createSectionTitle(title: String): TextView {
        return TextView(this).apply {
            text = title
            textSize = 15f
            setTextColor(Color.parseColor("#60A5FA"))
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            setPadding(0, 12, 0, 8)
        }
    }

    private fun createSpacer(): LinearLayout {
        return LinearLayout(this).apply {
            layoutParams = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 24)
        }
    }

    private fun renderErrorUI(errorMsg: String) {
        mainLayout.removeAllViews()
        val errorTv = TextView(this).apply {
            text = "⚠️ Could not load explanation report: $errorMsg"
            setTextColor(Color.RED)
            textSize = 14f
        }
        val btnClose = Button(this).apply {
            text = "Close"
            setOnClickListener { finish() }
        }
        mainLayout.addView(errorTv)
        mainLayout.addView(btnClose)
    }
}
