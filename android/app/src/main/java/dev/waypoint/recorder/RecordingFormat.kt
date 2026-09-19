package dev.waypoint.recorder

import java.io.File

object RecordingFormat {
    const val BATCH_SIZE = 500
    fun normalizeFingerprint(value: String): String {
        val result = value.replace(":", "").replace(" ", "").lowercase()
        require(result.matches(Regex("[a-f0-9]{64}"))) { "Enter the full SHA256 certificate fingerprint" }
        return result
    }
    fun elapsedSeconds(timestampNs: Long, startNs: Long): Double {
        require(timestampNs >= startNs)
        return (timestampNs - startNs) / 1_000_000_000.0
    }
    fun completeBatches(lines: Int, finished: Boolean): Int =
        if (finished) (lines + BATCH_SIZE - 1) / BATCH_SIZE else lines / BATCH_SIZE
    fun files(folder: File): List<File> = folder.listFiles()?.filter { it.extension == "jsonl" }?.sortedByDescending { it.lastModified() } ?: emptyList()
}
