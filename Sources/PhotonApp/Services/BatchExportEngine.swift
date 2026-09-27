import Foundation

public struct BatchExportResult: Sendable {
    public let successfulCount: Int
    public let failedCount: Int
    public let failedItems: [String]
    public let wasCancelled: Bool
}

public actor BatchExportEngine {
    private var isCancelled: Bool = false

    public init() {}

    public func cancel() {
        self.isCancelled = true
    }

    public func export(
        items: [ImageItem],
        globalSettings: BorderSettings,
        outputDirectory: URL,
        onProgress: @Sendable @escaping (Int, Int) -> Void
    ) async -> BatchExportResult {
        self.isCancelled = false
        let total = items.count
        guard total > 0 else {
            return BatchExportResult(successfulCount: 0, failedCount: 0, failedItems: [], wasCancelled: false)
        }

        var completed = 0
        var successCount = 0
        var failedCount = 0
        var failedItems: [String] = []

        let maxConcurrent = max(2, min(ProcessInfo.processInfo.activeProcessorCount, 8))

        await withTaskGroup(of: (String, Bool).self) { group in
            var itemIterator = items.makeIterator()

            // Seed initial tasks
            for _ in 0..<maxConcurrent {
                if let nextItem = itemIterator.next() {
                    let settings = nextItem.effectiveSettings(global: globalSettings)
                    group.addTask { [isCancelled = self.isCancelled] in
                        if isCancelled || Task.isCancelled {
                            return (nextItem.displayName, false)
                        }
                        let (base, ext) = CoreGraphicsRenderer.suggestedFilename(for: nextItem)
                        let targetURL = outputDirectory.appendingPathComponent("\(base)_bordered.\(ext)")

                        do {
                            try CoreGraphicsRenderer.export(item: nextItem, settings: settings, to: targetURL)
                            return (nextItem.displayName, true)
                        } catch {
                            return (nextItem.displayName, false)
                        }
                    }
                }
            }

            // Consume results and enqueue next tasks
            for await (displayName, success) in group {
                if self.isCancelled || Task.isCancelled {
                    break
                }

                completed += 1
                if success {
                    successCount += 1
                } else {
                    failedCount += 1
                    failedItems.append(displayName)
                }

                onProgress(completed, total)

                if let nextItem = itemIterator.next() {
                    let settings = nextItem.effectiveSettings(global: globalSettings)
                    group.addTask { [isCancelled = self.isCancelled] in
                        if isCancelled || Task.isCancelled {
                            return (nextItem.displayName, false)
                        }
                        let (base, ext) = CoreGraphicsRenderer.suggestedFilename(for: nextItem)
                        let targetURL = outputDirectory.appendingPathComponent("\(base)_bordered.\(ext)")

                        do {
                            try CoreGraphicsRenderer.export(item: nextItem, settings: settings, to: targetURL)
                            return (nextItem.displayName, true)
                        } catch {
                            return (nextItem.displayName, false)
                        }
                    }
                }
            }
        }

        return BatchExportResult(
            successfulCount: successCount,
            failedCount: failedCount,
            failedItems: failedItems,
            wasCancelled: self.isCancelled
        )
    }
}
