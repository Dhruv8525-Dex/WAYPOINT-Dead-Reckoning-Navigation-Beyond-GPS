plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
    namespace = "dev.waypoint.recorder"
    compileSdk = 35
    defaultConfig { applicationId = "dev.waypoint.recorder"; minSdk = 26; targetSdk = 35; versionCode = 1; versionName = "1.0.0" }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
dependencies { implementation("com.squareup.okhttp3:okhttp:5.5.1"); testImplementation("junit:junit:4.13.2") }
