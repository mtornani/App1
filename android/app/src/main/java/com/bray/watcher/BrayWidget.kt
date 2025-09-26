package com.bray.watcher

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.widget.RemoteViews

/**
 * Home screen widget projecting the ruthless telemetry: OB1 revenue and cognitive load. The
 * widget background shifts to red/orange/black depending on state and exposes a quick tap to
 * trigger Bray's focus mode.
 */
class BrayWidget : AppWidgetProvider() {

    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        for (id in appWidgetIds) {
            updateWidget(context, appWidgetManager, id)
        }
    }

    private fun updateWidget(context: Context, manager: AppWidgetManager, widgetId: Int) {
        val prefs = context.getSharedPreferences("bray_metrics", Context.MODE_PRIVATE)
        val revenue = prefs.getInt("ob1_revenue", 0)
        val load = prefs.getInt("cognitive_load", 45)

        val views = RemoteViews(context.packageName, R.layout.bray_widget).apply {
            setTextViewText(R.id.widget_text, "OB1: €$revenue | Load: $load%")

            val backgroundColor = when {
                revenue == 0 -> Color.RED
                load > 80 -> Color.parseColor("#FFA500")
                else -> Color.BLACK
            }
            setInt(R.id.widget_layout, "setBackgroundColor", backgroundColor)

            val focusIntent = Intent(context, BrayService::class.java).apply {
                action = "FOCUS_MODE"
            }
            val pendingIntent = PendingIntent.getService(
                context,
                0,
                focusIntent,
                PendingIntent.FLAG_IMMUTABLE
            )
            setOnClickPendingIntent(R.id.focus_button, pendingIntent)
        }

        manager.updateAppWidget(widgetId, views)
    }
}
