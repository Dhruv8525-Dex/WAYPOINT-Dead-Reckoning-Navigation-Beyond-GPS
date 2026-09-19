package dev.waypoint.recorder
import org.junit.Assert.*
import org.junit.Test
class RecordingFormatTest {
 @Test fun monotonicClock() { assertEquals(1.5, RecordingFormat.elapsedSeconds(2500000000,1000000000), 0.000001) }
 @Test fun partialBatchNeverTransfersEarly() { assertEquals(1,RecordingFormat.completeBatches(501,false)); assertEquals(2,RecordingFormat.completeBatches(501,true)) }
 @Test(expected=IllegalArgumentException::class) fun rejectShortFingerprint() { RecordingFormat.normalizeFingerprint("abc") }
 @Test fun normalizePin() { assertEquals("aa".repeat(32),RecordingFormat.normalizeFingerprint("AA:".repeat(31)+"AA")) }
}
