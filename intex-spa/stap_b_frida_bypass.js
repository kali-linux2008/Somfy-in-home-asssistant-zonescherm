/**
 * STAP B (fallback) — Frida SSL/certificate-pinning bypass voor Android
 *
 * Gebruik alleen als mitmproxy certificate pinning detecteert (app weigert te verbinden).
 *
 * VEREISTEN:
 *   • Geroote Android-telefoon OF een rootbare emulator (bijv. Genymotion/AVD met Play Services)
 *   • Frida server op het apparaat: https://github.com/frida/frida/releases
 *     → download frida-server-<versie>-android-<arch> voor jouw CPU (arm64 voor moderne telefoons)
 *     → push naar het apparaat:
 *         adb push frida-server /data/local/tmp/
 *         adb shell "chmod 755 /data/local/tmp/frida-server"
 *         adb shell "su -c /data/local/tmp/frida-server &"
 *   • Frida CLI op je PC:
 *         pip3 install frida-tools
 *
 * PACKAGE NAAM ACHTERHALEN (doe dit eerst):
 *   adb shell pm list packages | grep -i intex
 *   → zoek iets als com.intexcorp.intexlink of com.intex.spa
 *
 * STARTEN (vervang PACKAGE_NAAM):
 *   frida -U -f PACKAGE_NAAM -l stap_b_frida_bypass.js --no-pause
 *
 * Daarna mitmproxy opstarten + telefoon-proxy instellen zoals beschreven in de README.
 * Het CA-certificaat hoeft dan NIET in Android vertrouwd te zijn (Frida bypast dat).
 */

"use strict";

// ── 1. TrustManager: accepteer elk certificaat ──────────────────────────────
Java.perform(function () {

    // ── OkHttp3 CertificatePinner ─────────────────────────────────────────
    try {
        var CertPinner = Java.use("okhttp3.CertificatePinner");
        CertPinner.check.overload("java.lang.String", "java.util.List").implementation = function () {
            console.log("[Frida] OkHttp3 CertificatePinner.check() omzeild");
        };
        // Overloaded variant (oudere versies)
        CertPinner.check.overload("java.lang.String", "[Ljava.security.cert.Certificate;").implementation = function () {
            console.log("[Frida] OkHttp3 CertificatePinner.check(certs) omzeild");
        };
    } catch (e) {
        console.log("[Frida] OkHttp3 CertificatePinner niet aanwezig (ok)");
    }

    // ── Conscrypt / standaard Android TrustManager ────────────────────────
    var TrustManager = Java.registerClass({
        name: "com.bypass.CustomTrustManager",
        implements: [Java.use("javax.net.ssl.X509TrustManager")],
        methods: {
            checkClientTrusted: function (chain, authType) {},
            checkServerTrusted: function (chain, authType) {},
            getAcceptedIssuers: function () { return []; },
        },
    });

    var SSLContext = Java.use("javax.net.ssl.SSLContext");
    var init = SSLContext.init.overload(
        "[Ljavax.net.ssl.KeyManager;",
        "[Ljavax.net.ssl.TrustManager;",
        "java.security.SecureRandom"
    );
    init.implementation = function (km, tm, sr) {
        console.log("[Frida] SSLContext.init() — eigen TrustManager injecteerd");
        init.call(this, km, [TrustManager.$new()], sr);
    };

    // ── HostnameVerifier: altijd true ─────────────────────────────────────
    var HostnameVerifier = Java.use("javax.net.ssl.HttpsURLConnection");
    HostnameVerifier.setDefaultHostnameVerifier.implementation = function () {
        console.log("[Frida] setDefaultHostnameVerifier omzeild");
    };

    // ── WebViewClient (React Native apps) ────────────────────────────────
    try {
        var WebViewClient = Java.use("android.webkit.WebViewClient");
        WebViewClient.onReceivedSslError.implementation = function (view, handler, error) {
            console.log("[Frida] WebViewClient SSL-fout genegeerd");
            handler.proceed();
        };
    } catch (e) {
        // Niet aanwezig in alle apps
    }

    // ── TrustKit (indien gebruikt) ────────────────────────────────────────
    try {
        var TrustKit = Java.use("com.datatheorem.android.trustkit.pinning.OkHostnameVerifier");
        TrustKit.verify.overload("java.lang.String", "javax.net.ssl.SSLSession").implementation = function () {
            console.log("[Frida] TrustKit verify omzeild");
            return true;
        };
    } catch (e) {
        // TrustKit niet aanwezig (ok)
    }

    console.log("\n[Frida] Certificate-pinning bypass actief.");
    console.log("[Frida] Start nu mitmproxy en stel de telefoon-proxy in.\n");
});
