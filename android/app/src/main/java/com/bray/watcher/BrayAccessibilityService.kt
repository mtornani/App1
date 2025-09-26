package com.bray.watcher

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.graphics.PixelFormat
import android.os.Handler
import android.os.Looper
import android.view.LayoutInflater
import android.view.WindowManager
import android.view.accessibility.AccessibilityEvent
import android.widget.TextView

/**
 * Accessibility layer that force-closes distracting apps or shames the user with an overlay.
 */
class BrayAccessibilityService : AccessibilityService() {

    private val distractingApps = setOf(
        "com.instagram.android",
        "com.twitter.android",
        "com.reddit.frontpage",
        "com.facebook.katana",
        "com.zhiliaoapp.musically",
        "com.google.android.youtube"
    )

    override fun onServiceConnected() {
        super.onServiceConnected()
        serviceInfo = serviceInfo.apply {
            eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            notificationTimeout = 100
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        if (event.eventType != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return

        val packageName = event.packageName?.toString() ?: return
        if (!distractingApps.contains(packageName)) return

        performGlobalAction(GLOBAL_ACTION_BACK)
        performGlobalAction(GLOBAL_ACTION_HOME)
        showShameOverlay(packageName)
    }

    override fun onInterrupt() {
        // Nothing to clean up
    }

    private fun showShameOverlay(packageName: String) {
        val wm = getSystemService(WINDOW_SERVICE) as WindowManager
        val overlay = LayoutInflater.from(this).inflate(R.layout.shame_overlay, null)
        overlay.findViewById<TextView>(R.id.shame_text).text =
            "STOP. ${packageName}\nOB1 made €0 while you scrolled."

        val params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        )

        wm.addView(overlay, params)

        Handler(Looper.getMainLooper()).postDelayed({
            wm.removeView(overlay)
        }, 3000)
    }
}
