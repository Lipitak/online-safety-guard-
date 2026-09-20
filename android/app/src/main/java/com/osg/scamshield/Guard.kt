package com.osg.scamshield

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.telephony.SmsMessage
import android.util.Log

object Guard {
    const val TAG = "ScamShieldGuard"
    var isEnabled: Boolean = true
}

class ScamListenerService : BroadcastReceiver() {
    override fun onReceive(context: Context?, intent: Intent?) {
        if (intent == null || context == null) return

        if (intent.action == "android.provider.Telephony.SMS_RECEIVED") {
            val bundle = intent.extras ?: return
            val pdus = bundle.get("pdus") as? Array<*> ?: return
            for (pdu in pdus) {
                val sms = SmsMessage.createFromPdu(pdu as ByteArray)
                val body = sms.messageBody
                val sender = sms.originatingAddress
                Log.d(Guard.TAG, "SMS Received from $sender: ${body.take(50)}")
            }
        }
    }
}
