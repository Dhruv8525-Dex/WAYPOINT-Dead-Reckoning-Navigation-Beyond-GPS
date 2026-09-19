package dev.waypoint.recorder

import android.app.*
import android.content.*
import android.hardware.*
import android.location.*
import android.os.*
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.util.UUID
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

class RecordingService : Service(), SensorEventListener, LocationListener {
    companion object { @Volatile var running = false; @Volatile var count = 0; @Volatile var message = "Ready to record" }
    private lateinit var sensors: SensorManager
    private lateinit var locations: LocationManager
    private lateinit var handlerThread: HandlerThread
    private var stream: FileOutputStream? = null
    private var file: File? = null
    private var wakeLock: PowerManager.WakeLock? = null
    private val network = Executors.newSingleThreadScheduledExecutor()
    private var gyro: FloatArray? = null
    private var gravity: FloatArray? = null
    private var fix: Location? = null
    private var startNs = 0L
    private var lastNs = 0L
    private var live = false
    override fun onBind(intent: Intent?) = null
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == "STOP") { stopSelf(); return START_NOT_STICKY }
        if (running) return START_NOT_STICKY
        sensors = getSystemService(SENSOR_SERVICE) as SensorManager
        locations = getSystemService(LOCATION_SERVICE) as LocationManager
        val acceleration = sensors.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        val gyroscope = sensors.getDefaultSensor(Sensor.TYPE_GYROSCOPE)
        if (acceleration == null || gyroscope == null) { message = "Accelerometer and gyroscope are required"; stopSelf(); return START_NOT_STICKY }
        val notifications = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        notifications.createNotificationChannel(NotificationChannel("recording", "Motion recording", NotificationManager.IMPORTANCE_LOW))
        val stop = PendingIntent.getService(this, 0, Intent(this, RecordingService::class.java).setAction("STOP"), PendingIntent.FLAG_IMMUTABLE)
        val open = PendingIntent.getActivity(this, 1, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
        val notification = Notification.Builder(this, "recording").setContentTitle("Waypoint is recording")
            .setContentText("IMU and GPS are saved on this phone").setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setContentIntent(open).setOngoing(true).addAction(Notification.Action.Builder(null, "Stop recording", stop).build()).build()
        try { startForeground(1, notification) } catch (e: Exception) { message = e.message ?: "Recording permission required"; stopSelf(); return START_NOT_STICKY }
        val folder = File(filesDir, "recordings"); folder.mkdirs()
        file = File(folder, UUID.randomUUID().toString() + ".jsonl")
        stream = FileOutputStream(file, true)
        startNs = SystemClock.elapsedRealtimeNanos(); count = 0; live = intent?.getBooleanExtra("live", false) ?: false
        handlerThread = HandlerThread("WaypointSensors"); handlerThread.start()
        val handler = Handler(handlerThread.looper)
        sensors.registerListener(this, acceleration, 10_000, handler)
        sensors.registerListener(this, gyroscope, 10_000, handler)
        sensors.getDefaultSensor(Sensor.TYPE_GRAVITY)?.let { sensors.registerListener(this, it, 10_000, handler) }
        try { locations.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000, 0f, this, handlerThread.looper) }
        catch (e: SecurityException) { message = "Grant precise location permission before recording"; stopSelf(); return START_NOT_STICKY }
        wakeLock = (getSystemService(POWER_SERVICE) as PowerManager).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "Waypoint:Recording").apply { acquire(6 * 60 * 60 * 1000L) }
        running = true; message = "Recording locally";
        network.scheduleWithFixedDelay({
            if (!live || !running) return@scheduleWithFixedDelay
            try {
                val sent = Transfer(this).upload(file!!, true)
                if (running) message = "Recording · $sent batches acknowledged"
            } catch (e: Exception) {
                if (running) message = "Recording offline · ${e.message ?: "connection unavailable"}"
            }
        }, 6, 6, TimeUnit.SECONDS)
        return START_NOT_STICKY
    }
    override fun onSensorChanged(event: SensorEvent) {
        when (event.sensor.type) {
            Sensor.TYPE_GYROSCOPE -> gyro = event.values.clone()
            Sensor.TYPE_GRAVITY -> gravity = event.values.clone()
            Sensor.TYPE_ACCELEROMETER -> {
                val g = gyro ?: return
                if (!running || event.timestamp <= lastNs || event.timestamp < startNs) return
                lastNs = event.timestamp
                val data = JSONObject().put("t", RecordingFormat.elapsedSeconds(event.timestamp, startNs))
                    .put("ax", event.values[0].toDouble()).put("ay", event.values[1].toDouble()).put("az", event.values[2].toDouble())
                    .put("gx", g[0].toDouble()).put("gy", g[1].toDouble()).put("gz", g[2].toDouble())
                gravity?.let { data.put("gravity_x", it[0].toDouble()).put("gravity_y", it[1].toDouble()).put("gravity_z", it[2].toDouble()) }
                fix?.let { location ->
                    // Never attach a future or stale GPS fix to the current IMU sample.
                    val age = (event.timestamp - location.elapsedRealtimeNanos) / 1e9
                    if (age >= 0 && age <= 2) {
                        data.put("lat", location.latitude).put("lng", location.longitude).put("accuracy", location.accuracy.toDouble())
                        if (location.hasSpeed()) data.put("speed", location.speed.toDouble())
                        if (location.hasBearing()) data.put("heading", location.bearing.toDouble())
                    }
                }
                try { synchronized(this) { stream?.write((data.toString() + "\n").toByteArray()); count++; if (count % 500 == 0) stream?.fd?.sync() } }
                catch (e: Exception) { message = "Storage error: ${e.message}"; stopSelf() }
            }
        }
    }
    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
    override fun onLocationChanged(location: Location) { fix = location }
    override fun onProviderEnabled(provider: String) {}
    override fun onProviderDisabled(provider: String) { fix = null; message = "Recording IMU · GPS provider disabled" }
    @Deprecated("Deprecated in Java") override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
    override fun onDestroy() {
        running = false
        if (::sensors.isInitialized) sensors.unregisterListener(this)
        if (::locations.isInitialized) locations.removeUpdates(this)
        network.shutdownNow()
        if (::handlerThread.isInitialized) { handlerThread.quitSafely(); handlerThread.join(1000) }
        synchronized(this) { try { stream?.fd?.sync(); stream?.close(); file?.let { File(it.parentFile, it.nameWithoutExtension + ".done").writeText(count.toString()) } } catch (_: Exception) {} }
        if (wakeLock?.isHeld == true) wakeLock?.release()
        if (!message.startsWith("Storage error")) message = "Saved $count samples on this phone"
        super.onDestroy()
    }
}
