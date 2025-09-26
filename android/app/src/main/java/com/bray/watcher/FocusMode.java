package com.bray.watcher;

import android.app.ActivityManager;
import android.app.NotificationManager;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.media.AudioManager;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;

import java.util.Arrays;
import java.util.List;

/**
 * Implements an aggressive focus mode that mirrors the Codex prompt: enable DND, silence
 * the ringer, kill background processes, and suspend distracting applications for the
 * specified duration.
 */
public class FocusMode {
    private final Context context;
    private final AudioManager audioManager;
    private final NotificationManager notificationManager;
    private final ActivityManager activityManager;
    private final DevicePolicyManager devicePolicyManager;
    private final Handler handler = new Handler(Looper.getMainLooper());

    public FocusMode(Context context) {
        this.context = context.getApplicationContext();
        this.audioManager = (AudioManager) context.getSystemService(Context.AUDIO_SERVICE);
        this.notificationManager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        this.activityManager = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
        this.devicePolicyManager = (DevicePolicyManager) context.getSystemService(Context.DEVICE_POLICY_SERVICE);
    }

    public void enableFocus(int minutes) {
        if (notificationManager != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            notificationManager.setInterruptionFilter(NotificationManager.INTERRUPTION_FILTER_NONE);
        }

        if (audioManager != null) {
            audioManager.setRingerMode(AudioManager.RINGER_MODE_SILENT);
        }

        killDistractingApps();
        suspendDistractingApps();

        handler.postDelayed(this::disableFocus, minutes * 60L * 1000L);
    }

    public void disableFocus() {
        if (notificationManager != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            notificationManager.setInterruptionFilter(NotificationManager.INTERRUPTION_FILTER_ALL);
        }

        if (audioManager != null) {
            audioManager.setRingerMode(AudioManager.RINGER_MODE_NORMAL);
        }

        unsuspendDistractingApps();
    }

    private List<String> getKillList() {
        return Arrays.asList(
                "com.instagram.android",
                "com.twitter.android",
                "com.reddit.frontpage",
                "com.slack.android",
                "com.discord",
                "com.facebook.katana"
        );
    }

    private void killDistractingApps() {
        if (activityManager == null) {
            return;
        }
        for (String packageName : getKillList()) {
            activityManager.killBackgroundProcesses(packageName);
        }
    }

    private void suspendDistractingApps() {
        if (devicePolicyManager == null || !isDeviceAdmin()) {
            return;
        }
        ComponentName admin = getAdminComponent();
        if (admin == null) {
            return;
        }
        for (String pkg : getKillList()) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                devicePolicyManager.setPackagesSuspended(admin, new String[]{pkg}, true);
            }
        }
    }

    private void unsuspendDistractingApps() {
        if (devicePolicyManager == null || !isDeviceAdmin()) {
            return;
        }
        ComponentName admin = getAdminComponent();
        if (admin == null) {
            return;
        }
        for (String pkg : getKillList()) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                devicePolicyManager.setPackagesSuspended(admin, new String[]{pkg}, false);
            }
        }
    }

    private boolean isDeviceAdmin() {
        if (devicePolicyManager == null) {
            return false;
        }
        ComponentName admin = getAdminComponent();
        return admin != null && devicePolicyManager.isAdminActive(admin);
    }

    private ComponentName getAdminComponent() {
        return new ComponentName(context, BrayDeviceAdminReceiver.class);
    }
}
