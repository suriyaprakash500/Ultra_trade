# ProGuard rules for Trading Autopilot
-keepattributes Signature
-keepattributes *Annotation*

# Retrofit
-dontwarn retrofit2.**
-keep class retrofit2.** { *; }

# Gson
-keep class com.trading.autopilot.data.model.** { *; }

# Coroutines
-dontwarn kotlinx.coroutines.**
