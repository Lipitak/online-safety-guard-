package com.osg.scamshield

import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.PixelFormat
import android.os.Build
import android.os.IBinder
import android.speech.tts.TextToSpeech
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.TextView
import java.util.Locale

class CriticalAlertOverlayService : Service(), TextToSpeech.OnInitListener {

    private var windowManager: WindowManager? = null
    private var overlayView: View? = null
    private var tts: TextToSpeech? = null
    private var pendingSpeechText: String? = null
    private var pendingSpeechLang: String? = null
    private var rawTextData: String = ""
    private var categoryData: String = ""

    override fun onCreate() {
        super.onCreate()
        windowManager = getSystemService(Context.WINDOW_SERVICE) as WindowManager
        tts = TextToSpeech(this, this)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val reason = intent?.getStringExtra("reason") ?: "High Risk Phishing / Banking Fraud"
        val warningLocal = intent?.getStringExtra("warning_local") ?: "सावधान! यह एक बैंकिंग धोखाधड़ी है। तुरंत बंद करें!"
        val speechLang = intent?.getStringExtra("speech_lang") ?: "hi-IN"
        categoryData = intent?.getStringExtra("category") ?: "banking_otp"
        rawTextData = intent?.getStringExtra("raw_text") ?: ""

        pendingSpeechText = warningLocal
        pendingSpeechLang = speechLang

        showFullPageRedAlert(reason, warningLocal)
        speakRegionalWarning(warningLocal, speechLang)

        return START_NOT_STICKY
    }

    private fun showFullPageRedAlert(reason: String, warningLocal: String) {
        if (overlayView != null) {
            try { windowManager?.removeView(overlayView) } catch (e: Exception) {}
        }

        val layoutParamsType = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_PHONE
        }

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            layoutParamsType,
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or
                    WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                    WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.CENTER
        }

        val container = View(this).apply {
            setBackgroundColor(Color.parseColor("#E6B91C1C")) // Deep Emergency Red
        }

        // Programmatic Alert UI Layout
        val layout = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 64, 48, 64)
            setBackgroundColor(Color.parseColor("#1F0404"))
        }

        val iconTv = TextView(this).apply {
            text = "🚨"
            textSize = 64f
            gravity = Gravity.CENTER
        }

        val titleTv = TextView(this).apply {
            text = "CRITICAL CYBER THREAT BLOCKED"
            textSize = 22f
            setTextColor(Color.parseColor("#FF4D4D"))
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
            setPadding(0, 16, 0, 16)
        }

        val urgentTextTv = TextView(this).apply {
            text = "TURANT BAND KARO / IS APP KO BAND KARO / KISI KO OTP MAT BATAO"
            textSize = 15f
            setTextColor(Color.YELLOW)
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
            setPadding(0, 0, 0, 24)
        }

        val reasonTv = TextView(this).apply {
            text = "Reason: $reason\n\n$warningLocal"
            textSize = 14f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
            setPadding(0, 0, 0, 32)
        }

        val btnDismiss = Button(this).apply {
            text = "🛡️ GO BACK & SAFE EXIT"
            setBackgroundColor(Color.parseColor("#22C55E"))
            setTextColor(Color.BLACK)
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            setOnClickListener {
                stopSelf()
            }
        }

        val btnExplain = Button(this).apply {
            text = "🔍 VIEW AI SECURITY FIXES & SOLUTIONS"
            setBackgroundColor(Color.parseColor("#374151"))
            setTextColor(Color.WHITE)
            setOnClickListener {
                val explainIntent = Intent(applicationContext, ExplanationActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    putExtra("category", categoryData)
                    putExtra("raw_text", rawTextData)
                }
                startActivity(explainIntent)
                stopSelf()
            }
        }

        layout.addView(iconTv)
        layout.addView(titleTv)
        layout.addView(urgentTextTv)
        layout.addView(reasonTv)
        layout.addView(btnDismiss)
        layout.addView(btnExplain)

        overlayView = layout
        windowManager?.addView(overlayView, params)
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            val text = pendingSpeechText
            val lang = pendingSpeechLang ?: "hi-IN"
            if (!text.isNullOrEmpty()) {
                speakRegionalWarning(text, lang)
            }
        }
    }

    private fun speakRegionalWarning(text: String, speechLang: String) {
        try {
            val locale = Locale.forLanguageTag(speechLang)
            tts?.language = locale
            tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "ScamShieldSpeechID")
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        tts?.stop()
        tts?.shutdown()
        overlayView?.let {
            try { windowManager?.removeView(it) } catch (e: Exception) {}
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
