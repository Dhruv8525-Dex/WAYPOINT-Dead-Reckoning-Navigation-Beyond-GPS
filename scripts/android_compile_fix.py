from pathlib import Path
p=Path('android/app/src/main/java/dev/waypoint/recorder/MainActivity.kt');s=p.read_text().replace('layout.addView(this)','this@MainActivity.layout.addView(this)');p.write_text(s)
p=Path('android/app/src/main/java/dev/waypoint/recorder/Transfer.kt');s=p.read_text().replace('        prefs.edit().putString("token", result.getString("token"))','        prefs.all.keys.filter { it.startsWith("ack_") }.forEach { prefs.edit().remove(it).commit() }\n        prefs.edit().putString("token", result.getString("token"))');p.write_text(s)
