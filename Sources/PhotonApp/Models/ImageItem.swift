import Foundation
import AppKit
import CoreGraphics
import ImageIO

public final class ImageItem: Identifiable, @unchecked Sendable {
    public let id: UUID
    public let url: URL?
    public let displayName: String
    public let cgImage: CGImage
    public let previewCGImage: CGImage
    public let displayImage: NSImage
    public let width: Int
    public let height: Int
    public let thumbnail: NSImage
    public var customSettings: BorderSettings?

    public init(
        id: UUID = UUID(),
        url: URL? = nil,
        displayName: String,
        cgImage: CGImage,
        previewCGImage: CGImage? = nil,
        thumbnail: NSImage? = nil,
        customSettings: BorderSettings? = nil
    ) {
        self.id = id
        self.url = url
        self.displayName = displayName
        self.cgImage = cgImage
        self.width = cgImage.width
        self.height = cgImage.height
        self.customSettings = customSettings

        let prev = previewCGImage ?? ImageItem.generateCGThumbnail(from: cgImage, maxPixelDimension: 1600)
        self.previewCGImage = prev
        self.displayImage = NSImage(cgImage: prev, size: NSSize(width: prev.width, height: prev.height))

        if let thumb = thumbnail {
            self.thumbnail = thumb
        } else {
            self.thumbnail = ImageItem.generateThumbnail(from: self.previewCGImage, maxPixelDimension: 240)
        }
    }

    public var isCustomized: Bool {
        customSettings != nil
    }

    public func effectiveSettings(global: BorderSettings) -> BorderSettings {
        customSettings ?? global
    }

    public static func load(from url: URL) -> ImageItem? {
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil) else {
            return nil
        }

        let fullOptions: [CFString: Any] = [
            kCGImageSourceShouldCache: true
        ]

        guard let cgImage = CGImageSourceCreateImageAtIndex(source, 0, fullOptions as CFDictionary) else {
            return nil
        }

        // Fast hardware-assisted preview generation (1600px max)
        let previewOptions: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceThumbnailMaxPixelSize: 1600
        ]

        let previewCG: CGImage
        if let p = CGImageSourceCreateThumbnailAtIndex(source, 0, previewOptions as CFDictionary) {
            previewCG = p
        } else {
            previewCG = generateCGThumbnail(from: cgImage, maxPixelDimension: 1600)
        }

        // Fast thumbnail generation (240px max)
        let thumbOptions: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceThumbnailMaxPixelSize: 240
        ]

        let thumbImage: NSImage
        if let thumbCG = CGImageSourceCreateThumbnailAtIndex(source, 0, thumbOptions as CFDictionary) {
            thumbImage = NSImage(cgImage: thumbCG, size: NSSize(width: thumbCG.width, height: thumbCG.height))
        } else {
            thumbImage = generateThumbnail(from: previewCG, maxPixelDimension: 240)
        }

        return ImageItem(
            url: url,
            displayName: url.lastPathComponent,
            cgImage: cgImage,
            previewCGImage: previewCG,
            thumbnail: thumbImage
        )
    }

    public static func from(nsImage: NSImage, displayName: String = "Pasted Image") -> ImageItem? {
        guard let cgImage = nsImage.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
            return nil
        }
        let previewCG = generateCGThumbnail(from: cgImage, maxPixelDimension: 1600)
        return ImageItem(
            url: nil,
            displayName: displayName,
            cgImage: cgImage,
            previewCGImage: previewCG
        )
    }

    public static func generateCGThumbnail(from cgImage: CGImage, maxPixelDimension: CGFloat) -> CGImage {
        let width = CGFloat(cgImage.width)
        let height = CGFloat(cgImage.height)
        guard width > 0, height > 0 else { return cgImage }

        let scale = min(maxPixelDimension / width, maxPixelDimension / height, 1.0)
        if scale >= 1.0 { return cgImage }

        let targetSize = CGSize(width: max(1, round(width * scale)), height: max(1, round(height * scale)))
        let colorSpace = cgImage.colorSpace ?? CGColorSpaceCreateDeviceRGB()

        guard let context = CGContext(
            data: nil,
            width: Int(targetSize.width),
            height: Int(targetSize.height),
            bitsPerComponent: 8,
            bytesPerRow: 0,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            return cgImage
        }

        context.interpolationQuality = .medium
        context.draw(cgImage, in: CGRect(origin: .zero, size: targetSize))

        return context.makeImage() ?? cgImage
    }

    private static func generateThumbnail(from cgImage: CGImage, maxPixelDimension: CGFloat) -> NSImage {
        let width = CGFloat(cgImage.width)
        let height = CGFloat(cgImage.height)
        guard width > 0, height > 0 else {
            return NSImage()
        }

        let scale = min(maxPixelDimension / width, maxPixelDimension / height, 1.0)
        let targetSize = CGSize(width: max(1, round(width * scale)), height: max(1, round(height * scale)))

        let colorSpace = cgImage.colorSpace ?? CGColorSpaceCreateDeviceRGB()
        guard let context = CGContext(
            data: nil,
            width: Int(targetSize.width),
            height: Int(targetSize.height),
            bitsPerComponent: 8,
            bytesPerRow: 0,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            return NSImage(cgImage: cgImage, size: targetSize)
        }

        context.interpolationQuality = .medium
        context.draw(cgImage, in: CGRect(origin: .zero, size: targetSize))

        if let thumbnailCG = context.makeImage() {
            return NSImage(cgImage: thumbnailCG, size: targetSize)
        }
        return NSImage(cgImage: cgImage, size: targetSize)
    }
}
