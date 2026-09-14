#!/usr/bin/env bash
set -u

OUT="${1:-13-results/raw}"
mkdir -p "$OUT"

echo "======================================"
echo " ANDROID SECURITY LAB - INVENTORY"
echo "======================================"
echo

echo "[1] Host"
echo "Kernel: $(uname -a)"
echo

echo "[2] ADB"
if command -v adb >/dev/null 2>&1; then
    adb version | head -3
else
    echo "ADB: NOT INSTALLED"
fi
echo

echo "[3] Connected Android devices"
if command -v adb >/dev/null 2>&1; then
    adb devices -l
else
    echo "ADB unavailable"
fi
echo

echo "[4] ADB shell information"
if command -v adb >/dev/null 2>&1 && adb get-state >/dev/null 2>&1; then
    echo "--- model ---"
    adb shell getprop ro.product.model 2>/dev/null
    echo "--- manufacturer ---"
    adb shell getprop ro.product.manufacturer 2>/dev/null
    echo "--- Android ---"
    adb shell getprop ro.build.version.release 2>/dev/null
    echo "--- SDK ---"
    adb shell getprop ro.build.version.sdk 2>/dev/null
    echo "--- build ---"
    adb shell getprop ro.build.display.id 2>/dev/null
else
    echo "No authorized Android device detected."
fi

echo
echo "[5] Provisioning / FRP-related properties"
if command -v adb >/dev/null 2>&1 && adb get-state >/dev/null 2>&1; then
    adb shell getprop 2>/dev/null | grep -Ei 'frp|setup|provision|oem|lock' || true
fi

echo
echo "[6] Bootloader state"
if command -v adb >/dev/null 2>&1 && adb get-state >/dev/null 2>&1; then
    adb shell getprop ro.boot.flash.locked 2>/dev/null || true
    adb shell getprop ro.boot.verifiedbootstate 2>/dev/null || true
fi

echo
echo "======================================"
echo " INVENTORY COMPLETE"
echo "======================================"
