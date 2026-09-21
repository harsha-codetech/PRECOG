package com.precog.m0spike

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * Minimal launcher — opens Accessibility settings so the user can enable
 * EventLoggerService. Shows the CSV output path so it is easy to pull.
 */
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val dir = getExternalFilesDir(null) ?: filesDir
        val path = "${dir.absolutePath}/${EventLoggerService.CSV_FILENAME}"

        val tv = TextView(this).apply {
            text = """
                PRECOG M0 Feasibility Spike

                1. Tap the button below to open Accessibility Settings.
                2. Find "PRECOG Event Logger" and enable it.
                3. Open Instagram, YouTube, TikTok, Reddit, or X and scroll normally.
                4. Pull the log from device storage:

                   adb pull "$path" precog_m0_events.csv

                5. Open the CSV and check which fields are non-zero.
                   If scrollDeltaY is always 0 across all apps → NO-GO for this approach.
            """.trimIndent()
            setPadding(48, 80, 48, 48)
            textSize = 14f
            lineHeight = (textSize * 1.5 + 0.5f).toInt()
        }

        val btn = Button(this).apply {
            text = "Open Accessibility Settings"
            setOnClickListener {
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            }
        }

        val layout = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            addView(tv)
            addView(btn, android.widget.LinearLayout.LayoutParams(
                android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
                android.widget.LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(48, 24, 48, 0) })
        }

        setContentView(layout)
    }
}
