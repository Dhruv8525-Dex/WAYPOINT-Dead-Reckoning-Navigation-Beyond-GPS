package dev.waypoint.recorder

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.*
import android.view.View
import android.widget.*
import java.io.File
import java.util.concurrent.Executors

class MainActivity : Activity() {
    private lateinit var layout: LinearLayout
    private lateinit var status: TextView
    private lateinit var sessions: LinearLayout
    private lateinit var live: CheckBox
    private lateinit var server: EditText
    private lateinit var fingerprint: EditText
    private lateinit var code: EditText
    private val executor = Executors.newSingleThreadExecutor()
    private val handler = Handler(Looper.getMainLooper())
    private val ink = Color.rgb(44, 71, 49)
    private val refresh = object : Runnable { override fun run() { status.text = RecordingService.message + if (RecordingService.running) "\n${RecordingService.count} samples captured" else ""; handler.postDelayed(this, 1000) } }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val scroll = ScrollView(this); layout = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(48, 65, 48, 50); setBackgroundColor(Color.rgb(245, 248, 239)) }; scroll.addView(layout); setContentView(scroll)
        text("waypoint.", 34f, true); text("YOUR MOTION, PRESERVED", 10f); spacer()
        text("Record the journey.", 28f, true); text("Use a rigid phone mount. Start while stationary. Recordings stay on your phone until transferred.", 14f)
        status = text("Ready to record", 14f); spacer()
        live = CheckBox(this).apply { text = "Live transfer when connected"; setTextColor(ink) }; layout.addView(live)
        button("Start recording") { startRecording() }
        button("Stop & save") { startService(Intent(this, RecordingService::class.java).setAction("STOP")); handler.postDelayed({ showSessions() }, 800) }
        spacer(); text("Connect your workspace", 23f, true); text("Enter the address, one-time code and certificate fingerprint displayed on the website. Use the same local network.", 13f)
        val preferences = getSharedPreferences("pairing", MODE_PRIVATE)
        server = input("https://COMPUTER-IP:8443", preferences.getString("server", "") ?: "")
        fingerprint = input("Certificate SHA256 fingerprint", preferences.getString("fingerprint", "") ?: "")
        code = input("Pairing code")
        button("Pair securely") { task { Transfer(this).pair(server.text.toString(), fingerprint.text.toString(), code.text.toString()) } }
        spacer(); text("Saved recordings", 23f, true)
        button("Refresh recordings") { showSessions() }
        sessions = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }; layout.addView(sessions); showSessions()
    }
    private fun startRecording() {
        val permissions = mutableListOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)
        if (Build.VERSION.SDK_INT >= 33) permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        val missing = permissions.filter { checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED }
        if (missing.isNotEmpty()) { requestPermissions(missing.toTypedArray(), 1); return }
        startForegroundService(Intent(this, RecordingService::class.java).putExtra("live", live.isChecked))
    }
    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 1) {
            if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED) startForegroundService(Intent(this, RecordingService::class.java).putExtra("live", live.isChecked))
            else RecordingService.message = "Precise location permission is required. You can enable it in Android settings."
        }
    }
    private fun showSessions() {
        sessions.removeAllViews()
        val files = RecordingFormat.files(File(filesDir, "recordings"))
        if (files.isEmpty()) sessions.addView(TextView(this).apply { text = "No recordings yet"; setTextColor(ink); setPadding(0, 15, 0, 15) })
        files.forEach { file ->
            sessions.addView(TextView(this).apply { text = file.nameWithoutExtension.take(18) + "…\n${file.length() / 1024} KB · " + if (File(file.parentFile, file.nameWithoutExtension + ".done").exists()) "saved" else "partial / recording"; setTextColor(ink); textSize = 13f; setPadding(0, 22, 0, 8) })
            sessions.addView(Button(this).apply { text = "Upload recording"; setOnClickListener { task { val batches = Transfer(this@MainActivity).upload(file); "$batches batches safely acknowledged. Import the session on the website." } } })
        }
    }
    private fun task(work: () -> String) { RecordingService.message = "Connecting…"; executor.execute { try { RecordingService.message = work() } catch (e: Exception) { RecordingService.message = e.message ?: "Transfer failed; recording stays on this phone" } } }
    private fun text(value: String, size: Float, bold: Boolean = false): TextView = TextView(this).apply { text = value; textSize = size; setTextColor(ink); if (bold) setTypeface(null, 1); setPadding(0, 8, 0, 12); this@MainActivity.layout.addView(this) }
    private fun input(hintText: String, value: String = ""): EditText = EditText(this).apply { hint = hintText; setText(value); textSize = 13f; setTextColor(ink); setSingleLine(false); importantForAutofill = View.IMPORTANT_FOR_AUTOFILL_NO; this@MainActivity.layout.addView(this) }
    private fun button(label: String, action: () -> Unit) { layout.addView(Button(this).apply { text = label; setOnClickListener { action() }; setTextColor(ink) }) }
    private fun spacer() { layout.addView(View(this), LinearLayout.LayoutParams(1, 28)) }
    override fun onResume() { super.onResume(); handler.post(refresh) }
    override fun onPause() { handler.removeCallbacks(refresh); super.onPause() }
    override fun onDestroy() { executor.shutdown(); super.onDestroy() }
}
