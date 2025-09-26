package com.bray.watcher;

import android.app.ActivityManager;
import android.app.AlertDialog;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.app.usage.UsageStats;
import android.app.usage.UsageStatsManager;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.view.WindowManager;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * BrayService is the always-on watchdog that keeps the user's Android device on task.
 * <p>
 * It aggressively monitors usage stats, keeps a non-dismissable foreground notification,
 * and intervenes when distracting applications take over the foreground. The implementation
 * mirrors the requested Codex prompt: persistent notification with quick actions, periodic
 * focus telemetry, and an intervention dialog that can outright terminate the offending app.
 */
public class BrayService extends Service {
    private static final int NOTIFICATION_ID = 666;
    private static final String CHANNEL_ID = "BRAY_CHANNEL";
    private static final long MONITOR_INTERVAL_MS = 60_000L;

    private UsageStatsManager usageManager;
    private NotificationManager notificationManager;
    private ActivityManager activityManager;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Map<String, Long> shameLog = new ConcurrentHashMap<>();
    private Thread monitorThread;
    private FocusMode focusMode;
    private long lastRevenueCheck = 0L;

    @Override
    public void onCreate() {
        super.onCreate();
        usageManager = (UsageStatsManager) getSystemService(USAGE_STATS_SERVICE);
        notificationManager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        activityManager = (ActivityManager) getSystemService(ACTIVITY_SERVICE);
        focusMode = new FocusMode(this);

        createPersistentNotification();
        startMonitoring();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && intent.getAction() != null) {
            switch (intent.getAction()) {
                case "FOCUS":
                case "FOCUS_MODE":
                    focusMode.enableFocus(90);
                    break;
                case "KILL":
                    killDistractingApps();
                    break;
                default:
                    break;
            }
        }
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (monitorThread != null) {
            monitorThread.interrupt();
        }
        handler.removeCallbacksAndMessages(null);
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private void createPersistentNotification() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "Bray Watcher",
                    NotificationManager.IMPORTANCE_HIGH
            );
            channel.setDescription("Always watching");
            notificationManager.createNotificationChannel(channel);
        }

        Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);

        PendingIntent focusIntent = PendingIntent.getService(
                this,
                0,
                new Intent(this, BrayService.class).setAction("FOCUS"),
                PendingIntent.FLAG_IMMUTABLE
        );

        PendingIntent killIntent = PendingIntent.getService(
                this,
                1,
                new Intent(this, BrayService.class).setAction("KILL"),
                PendingIntent.FLAG_IMMUTABLE
        );

        builder.setContentTitle("Bray Active")
                .setContentText(buildStatusText())
                .setSmallIcon(R.drawable.eye)
                .setOngoing(true)
                .addAction(new Notification.Action.Builder(
                        R.drawable.focus,
                        "FOCUS",
                        focusIntent
                ).build())
                .addAction(new Notification.Action.Builder(
                        R.drawable.kill,
                        "KILL APPS",
                        killIntent
                ).build());

        startForeground(NOTIFICATION_ID, builder.build());
    }

    private void startMonitoring() {
        monitorThread = new Thread(() -> {
            while (!Thread.currentThread().isInterrupted()) {
                checkDistractingApps();
                checkOB1Revenue();
                updateNotification();
                try {
                    Thread.sleep(MONITOR_INTERVAL_MS);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }
        }, "Bray-Monitor");
        monitorThread.start();
    }

    private void checkDistractingApps() {
        UsageStats current = getCurrentApp();
        if (current == null) {
            return;
        }

        String packageName = current.getPackageName();
        if (getDistractingApps().contains(packageName)) {
            showInterventionDialog(packageName);
        }
    }

    private void showInterventionDialog(String packageName) {
        handler.post(() -> {
            AlertDialog alert = new AlertDialog.Builder(BrayService.this)
                    .setTitle("STOP")
                    .setMessage("You're wasting time on " + packageName + "\n\nOB1 made €" + getOB1Revenue() + " while you scrolled.")
                    .setPositiveButton("Kill App", (dialog, which) -> killApp(packageName))
                    .setNegativeButton("5 More Minutes", (dialog, which) -> logShame(packageName))
                    .create();

            if (alert.getWindow() != null) {
                alert.getWindow().setType(WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY);
            }
            alert.show();
        });
    }

    private void updateNotification() {
        Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);

        PendingIntent focusIntent = PendingIntent.getService(
                this,
                0,
                new Intent(this, BrayService.class).setAction("FOCUS"),
                PendingIntent.FLAG_IMMUTABLE
        );

        PendingIntent killIntent = PendingIntent.getService(
                this,
                1,
                new Intent(this, BrayService.class).setAction("KILL"),
                PendingIntent.FLAG_IMMUTABLE
        );

        builder.setContentTitle("Bray Active")
                .setContentText(buildStatusText())
                .setSmallIcon(R.drawable.eye)
                .setOngoing(true)
                .addAction(new Notification.Action.Builder(
                        R.drawable.focus,
                        "FOCUS",
                        focusIntent
                ).build())
                .addAction(new Notification.Action.Builder(
                        R.drawable.kill,
                        "KILL APPS",
                        killIntent
                ).build());

        notificationManager.notify(NOTIFICATION_ID, builder.build());
    }

    private String buildStatusText() {
        return "OB1: €" + getOB1Revenue() + " | Load: " + getCognitiveLoad() + "%";
    }

    private UsageStats getCurrentApp() {
        if (usageManager == null) {
            return null;
        }
        long end = System.currentTimeMillis();
        long start = end - 5_000;
        List<UsageStats> stats = usageManager.queryUsageStats(UsageStatsManager.INTERVAL_DAILY, start, end);
        if (stats == null || stats.isEmpty()) {
            return null;
        }
        UsageStats latest = null;
        for (UsageStats usageStats : stats) {
            if (latest == null || usageStats.getLastTimeUsed() > latest.getLastTimeUsed()) {
                latest = usageStats;
            }
        }
        return latest;
    }

    private void killDistractingApps() {
        for (String packageName : getDistractingApps()) {
            killApp(packageName);
        }
    }

    private void killApp(String packageName) {
        if (activityManager != null) {
            activityManager.killBackgroundProcesses(packageName);
        }
    }

    private void logShame(String packageName) {
        shameLog.put(packageName, System.currentTimeMillis());
        SharedPreferences prefs = getSharedPreferences("bray_shame", MODE_PRIVATE);
        prefs.edit().putLong(packageName, System.currentTimeMillis()).apply();
    }

    private List<String> getDistractingApps() {
        return Arrays.asList(
                "com.instagram.android",
                "com.twitter.android",
                "com.reddit.frontpage",
                "com.facebook.katana",
                "com.zhiliaoapp.musically",
                "com.google.android.youtube",
                "com.slack.android",
                "com.discord"
        );
    }

    private int getOB1Revenue() {
        SharedPreferences prefs = getSharedPreferences("bray_metrics", MODE_PRIVATE);
        return prefs.getInt("ob1_revenue", 0);
    }

    private int getCognitiveLoad() {
        SharedPreferences prefs = getSharedPreferences("bray_metrics", MODE_PRIVATE);
        return prefs.getInt("cognitive_load", 45);
    }

    private void checkOB1Revenue() {
        long now = System.currentTimeMillis();
        if (now - lastRevenueCheck < 300_000L) {
            return;
        }
        lastRevenueCheck = now;

        SharedPreferences prefs = getSharedPreferences("bray_metrics", MODE_PRIVATE);
        int currentRevenue = prefs.getInt("ob1_revenue", 0);
        int shamePenalty = Math.min(shameLog.size() * 5, 50);
        int adjustedRevenue = Math.max(0, currentRevenue - shamePenalty);
        int cognitiveLoad = Math.min(100, prefs.getInt("cognitive_load", 45) + shameLog.size() * 3);

        prefs.edit()
                .putInt("ob1_revenue", adjustedRevenue)
                .putInt("cognitive_load", cognitiveLoad)
                .apply();
    }
}
