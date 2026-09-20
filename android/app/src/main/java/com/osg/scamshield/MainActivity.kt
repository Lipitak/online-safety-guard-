package com.osg.scamshield

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {

    private lateinit var statusTv: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate()

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            padding = 48
            setBackgroundColor(android.graphics.Color.parseColor("#0B0F19"))
        }

        val title = TextView(this).apply {
            text = "🛡️ ScamShield 24/7 Protection"
            textSize = 22f
            setTextColor(android.graphics.Color.WHITE)
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            setPadding(0, 0, 0, 16)
        }

        val sub = TextView(this).apply {
            text = "Trinetra_ai SIH Cyber Security Suite\nAutomated threat detection across WhatsApp, Telegram, LinkedIn, Naukri, Gmail, Chrome, and SMS."
            textSize = 13.5f
            setTextColor(android.graphics.Color.LTGRAY)
            setPadding(0, 0, 0, 32)
        }

        statusTv = TextView(this).apply {
            textSize = 15f
            setPadding(0, 0, 0, 24)
        }

        val btnAccessibility = Button(this).apply {
            text = "1. Enable Accessibility Service (One-Time)"
            setBackgroundColor(android.graphics.Color.parseColor("#E8641C"))
            setTextColor(android.graphics.Color.WHITE)
            setOnClickListener {
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            }
        }

        val btnOverlay = Button(this).apply {
            text = "2. Enable Red Alert Overlay (One-Time)"
            setBackgroundColor(android.graphics.Color.parseColor("#2563EB"))
            setTextColor(android.graphics.Color.WHITE)
            setOnClickListener {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    val intent = Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse("package:$packageName")
                    )
                    startActivity(intent)
                }
            }
        }

        layout.addView(title)
        layout.addView(sub)
        layout.addView(statusTv)
        layout.addView(btnAccessibility)
        layout.addView(btnOverlay)

        setContentView(layout)
    }

    override fun onResume() {
        super.onResume()
        updateStatus()
    }

    private fun updateStatus() {
        val hasOverlay = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            Settings.canDrawOverlays(this)
        } else true

        if (hasOverlay) {
            statusTv.text = "🟢 24/7 ACTIVE PROTECTION ACTIVE\nAll Accessibility & Overlay Permissions Granted."
            statusTv.setTextColor(android.graphics.Color.parseColor("#22C55E"))
        } else {
            statusTv.text = "🟠 Setup Required: Please grant Accessibility & Overlay permissions."
            statusTv.setTextColor(android.graphics.Color.parseColor("#F59E0B"))
        }
    }
}
