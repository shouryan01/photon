import Foundation
import SwiftUI
import AppKit
import UniformTypeIdentifiers

@MainActor
public final class BorderStudioViewModel: ObservableObject {
    @Published public var images: [ImageItem] = []
    @Published public var selectedImageIndex: Int? = nil

    @Published public var globalSettings: BorderSettings = .default
    @Published public var applyToAll: Bool = true
    @Published public var outputDirectory: URL? = nil

    @Published public var activePreview: NSImage? = nil
    @Published public var activePadding: CalculatedPadding? = nil

    @Published public var isExportingBatch: Bool = false
    @Published public var batchProgress: (completed: Int, total: Int) = (0, 0)
    @Published public var batchAlertMessage: String? = nil
    @Published public var showBatchAlert: Bool = false

    private var batchEngine = BatchExportEngine()

    public init() {}

    public var activeImage: ImageItem? {
        guard let index = selectedImageIndex, images.indices.contains(index) else {
            return nil
        }
        return images[index]
    }

    public var currentSettings: BorderSettings {
        get {
            if let active = activeImage, let custom = active.customSettings {
                return custom
            }
            return globalSettings
        }
        set {
            if applyToAll {
                globalSettings = newValue
            } else if let active = activeImage {
                active.customSettings = newValue
            }
            updateActivePreview()
        }
    }

    public func updateActivePreview() {
        guard let active = activeImage else {
            activePadding = nil
            return
        }

        self.activePadding = AutoBorderCalculator.calculate(
            width: active.width,
            height: active.height,
            settings: currentSettings
        )
    }

    public func setMode(_ mode: BorderMode) {
        guard currentSettings.mode != mode else { return }
        if applyToAll {
            globalSettings.mode = mode
        } else if let active = activeImage {
            if active.customSettings == nil {
                active.customSettings = globalSettings
            }
            active.customSettings?.mode = mode
        }
        updateActivePreview()
    }

    // MARK: - Image Management

    public func pickImages() {
        let panel = NSOpenPanel()
        panel.title = "Select Photos"
        panel.message = "Choose one or multiple images to add borders"
        panel.allowsMultipleSelection = true
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowedContentTypes = [
            .image,
            .jpeg,
            .png,
            .tiff,
            .heic,
            .bmp,
            .webP,
            .rawImage
        ]

        if panel.runModal() == .OK {
            addImages(from: panel.urls)
        }
    }

    public func addImages(from urls: [URL]) {
        let previousCount = images.count
        var loadedItems: [ImageItem] = []
        collectImages(from: urls, into: &loadedItems)

        guard !loadedItems.isEmpty else { return }

        images.append(contentsOf: loadedItems)

        if selectedImageIndex == nil || previousCount < images.count {
            selectedImageIndex = previousCount
        }
        updateActivePreview()
    }

    private func collectImages(from urls: [URL], into results: inout [ImageItem]) {
        for url in urls {
            var isDir: ObjCBool = false
            if FileManager.default.fileExists(atPath: url.path, isDirectory: &isDir), isDir.boolValue {
                if let files = try? FileManager.default.contentsOfDirectory(at: url, includingPropertiesForKeys: nil) {
                    collectImages(from: files, into: &results)
                }
                continue
            }

            if let item = ImageItem.load(from: url) {
                results.append(item)
            }
        }
    }

    public func addPastedImage(_ nsImage: NSImage) {
        if let item = ImageItem.from(nsImage: nsImage, displayName: "Pasted Image \(images.count + 1)") {
            images.append(item)
            selectedImageIndex = images.count - 1
            updateActivePreview()
        }
    }

    public func selectImage(at index: Int) {
        guard images.indices.contains(index) else { return }
        selectedImageIndex = index
        updateActivePreview()
    }

    public func selectNextImage() {
        guard !images.isEmpty else { return }
        let current = selectedImageIndex ?? -1
        let next = (current + 1) % images.count
        selectImage(at: next)
    }

    public func selectPreviousImage() {
        guard !images.isEmpty else { return }
        let current = selectedImageIndex ?? 0
        let prev = (current - 1 + images.count) % images.count
        selectImage(at: prev)
    }

    public func removeActiveImage() {
        guard let index = selectedImageIndex, images.indices.contains(index) else { return }
        removeImage(at: index)
    }

    public func removeImage(at index: Int) {
        guard images.indices.contains(index) else { return }
        images.remove(at: index)

        if images.isEmpty {
            selectedImageIndex = nil
        } else if let current = selectedImageIndex {
            if current >= images.count {
                selectedImageIndex = images.count - 1
            }
        }
        updateActivePreview()
    }

    public func clearAll() {
        images.removeAll()
        selectedImageIndex = nil
        activePreview = nil
        activePadding = nil
    }

    // MARK: - Output Directory

    public func selectOutputDirectory() {
        let panel = NSOpenPanel()
        panel.title = "Select Output Directory"
        panel.message = "Choose a destination folder for exported bordered images"
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.canCreateDirectories = true
        panel.allowsMultipleSelection = false

        if panel.runModal() == .OK {
            self.outputDirectory = panel.url
        }
    }

    // MARK: - Preset Management

    public func savePreset() {
        let panel = NSSavePanel()
        panel.title = "Save Border Settings Preset"
        panel.nameFieldStringValue = "BorderPreset.json"
        panel.allowedContentTypes = [UTType.json]

        if panel.runModal() == .OK, let targetURL = panel.url {
            do {
                let encoder = JSONEncoder()
                encoder.outputFormatting = .prettyPrinted
                let data = try encoder.encode(currentSettings)
                try data.write(to: targetURL)
            } catch {
                NSSound.beep()
            }
        }
    }

    public func loadPreset() {
        let panel = NSOpenPanel()
        panel.title = "Load Border Settings Preset"
        panel.allowsMultipleSelection = false
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowedContentTypes = [UTType.json]

        if panel.runModal() == .OK, let sourceURL = panel.url {
            do {
                let data = try Data(contentsOf: sourceURL)
                let decoder = JSONDecoder()
                let loadedSettings = try decoder.decode(BorderSettings.self, from: data)
                self.currentSettings = loadedSettings
            } catch {
                NSSound.beep()
            }
        }
    }

    // MARK: - Export

    public func export() {
        if images.count <= 1 {
            exportActiveImage()
        } else {
            exportAllImages()
        }
    }

    public func exportActiveImage() {
        guard let active = activeImage else { return }
        let settings = currentSettings

        if let outDir = outputDirectory {
            let (base, ext) = CoreGraphicsRenderer.suggestedFilename(for: active)
            let destURL = outDir.appendingPathComponent("\(base)_bordered.\(ext)")
            do {
                try CoreGraphicsRenderer.export(item: active, settings: settings, to: destURL)
                NSWorkspace.shared.activateFileViewerSelecting([destURL])
            } catch {
                NSSound.beep()
            }
        } else {
            let panel = NSSavePanel()
            panel.title = "Save Bordered Image"
            let (base, ext) = CoreGraphicsRenderer.suggestedFilename(for: active)
            panel.nameFieldStringValue = "\(base)_bordered.\(ext)"

            if let utType = UTType(filenameExtension: ext) {
                panel.allowedContentTypes = [utType]
            }

            if panel.runModal() == .OK, let destURL = panel.url {
                do {
                    try CoreGraphicsRenderer.export(item: active, settings: settings, to: destURL)
                    self.outputDirectory = destURL.deletingLastPathComponent()
                } catch {
                    NSSound.beep()
                }
            }
        }
    }

    public func exportAllImages() {
        guard !images.isEmpty else { return }

        guard let outDir = outputDirectory else {
            selectOutputDirectory()
            if outputDirectory != nil {
                exportAllImages()
            }
            return
        }

        isExportingBatch = true
        batchProgress = (0, images.count)

        Task {
            let engine = self.batchEngine
            let result = await engine.export(
                items: self.images,
                globalSettings: self.globalSettings,
                outputDirectory: outDir
            ) { completed, total in
                Task { @MainActor in
                    self.batchProgress = (completed, total)
                }
            }

            self.isExportingBatch = false

            if !result.wasCancelled {
                self.batchAlertMessage = "Successfully exported \(result.successfulCount) of \(self.images.count) images to:\n\(outDir.path)"
                self.showBatchAlert = true
            }
        }
    }

    public func cancelBatchExport() {
        Task {
            await batchEngine.cancel()
            self.isExportingBatch = false
        }
    }
}
