package com.precog

import android.app.Application
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.provider.Settings
import android.text.TextUtils
import com.precog.data.PrecogRepository
import com.precog.service.ScrollCaptureService

class PrecogApplication : Application() {

    val repository: PrecogRepository by lazy { PrecogRepository(this) }

    companion object {
        fun repository(context: Context): PrecogRepository =
            (context.applicationContext as PrecogApplication).repository
    }
}

/** Accessibility enablement is a system setting; the app can only check it and point at it. */
object AccessibilityStatus {

    fun isEnabled(context: Context): Boolean {
        val expected = ComponentName(context, ScrollCaptureService::class.java).flattenToString()
        val enabled = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES,
        ) ?: return false
        val splitter = TextUtils.SimpleStringSplitter(':')
        splitter.setString(enabled)
        while (splitter.hasNext()) {
            if (splitter.next().equals(expected, ignoreCase = true)) return true
        }
        return false
    }

    fun openSettings(context: Context) {
        context.startActivity(
            Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        )
    }
}
