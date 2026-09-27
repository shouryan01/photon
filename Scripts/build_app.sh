#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "==> Building Photon for macOS 15+ (Apple Silicon arm64)..."

BUILD_DIR="${ROOT_DIR}/build"
APP_DIR="${BUILD_DIR}/Photon.app"
MACOS_DIR="${APP_DIR}/Contents/MacOS"
RESOURCES_DIR="${APP_DIR}/Contents/Resources"
CACHE_DIR="${BUILD_DIR}/cache"
TMP_DIR="${BUILD_DIR}/tmp"

mkdir -p "${MACOS_DIR}" "${RESOURCES_DIR}" "${CACHE_DIR}" "${TMP_DIR}"

# Collect all Swift source files
SOURCES=(
    "${ROOT_DIR}/Sources/PhotonApp/PhotonApp.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Models/BorderMode.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Models/AspectRatio.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Models/BorderSettings.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Models/ImageItem.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Services/AutoBorderCalculator.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Services/CoreGraphicsRenderer.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Services/BatchExportEngine.swift"
    "${ROOT_DIR}/Sources/PhotonApp/ViewModels/BorderStudioViewModel.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Views/Sidebar/ModeSelectorView.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Views/Sidebar/AutoModeControlsView.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Views/Sidebar/ManualModeControlsView.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Views/Sidebar/ColorPaletteView.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Views/Sidebar/ManualBorderSettingsActionsView.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Views/Sidebar/ExportButtonView.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Views/Sidebar/BorderSidebarView.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Views/Canvas/CanvasInfoBadge.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Views/Canvas/CanvasView.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Views/Filmstrip/ThumbnailItemView.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Views/Filmstrip/FilmstripView.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Views/Export/BatchExportSheet.swift"
    "${ROOT_DIR}/Sources/PhotonApp/Views/MainView.swift"
)

echo "==> Compiling ${#SOURCES[@]} Swift source files..."

swiftc \
    -target arm64-apple-macosx15.0 \
    -parse-as-library \
    -O \
    -module-cache-path "${CACHE_DIR}" \
    -Xfrontend -enable-actor-data-race-checks \
    "${SOURCES[@]}" \
    -o "${MACOS_DIR}/Photon"

echo "==> Packaging macOS App Bundle..."

# Copy Info.plist
cp "${ROOT_DIR}/Info.plist" "${APP_DIR}/Contents/Info.plist"

# Copy Icon
if [ -f "${ROOT_DIR}/Resources/icon.icns" ]; then
    cp "${ROOT_DIR}/Resources/icon.icns" "${RESOURCES_DIR}/AppIcon.icns"
fi

# Write PkgInfo
echo "APPL????" > "${APP_DIR}/Contents/PkgInfo"

# Clean up temp cache
rm -rf "${TMP_DIR}"

echo "==> Build Successful!"
echo "    App Location: ${APP_DIR}"
echo "    You can run it directly with: open '${APP_DIR}'"
