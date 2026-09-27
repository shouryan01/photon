import Foundation
import AppKit
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

public enum RenderError: LocalizedError {
    case contextCreationFailed
    case imageRenderingFailed
    case destinationCreationFailed
    case exportFailed

    public var errorDescription: String? {
        switch self {
        case .contextCreationFailed:
            return "Failed to create graphics context for border rendering."
        case .imageRenderingFailed:
            return "Failed to render bordered image."
        case .destinationCreationFailed:
            return "Failed to create image destination at target URL."
        case .exportFailed:
            return "Failed to finalize and write image to disk."
        }
    }
}

public struct CoreGraphicsRenderer {

    public static func renderBorderedImage(
        cgImage: CGImage,
        settings: BorderSettings
    ) throws -> (image: CGImage, padding: CalculatedPadding) {
        let width = cgImage.width
        let height = cgImage.height
        let padding = AutoBorderCalculator.calculate(width: width, height: height, settings: settings)

        let outWidth = padding.outputWidth
        let outHeight = padding.outputHeight

        let colorSpace = cgImage.colorSpace ?? CGColorSpace(name: CGColorSpace.sRGB) ?? CGColorSpaceCreateDeviceRGB()
        let bitmapInfo = CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue)

        guard let context = CGContext(
            data: nil,
            width: outWidth,
            height: outHeight,
            bitsPerComponent: 8,
            bytesPerRow: 0,
            space: colorSpace,
            bitmapInfo: bitmapInfo.rawValue
        ) else {
            throw RenderError.contextCreationFailed
        }

        context.setFillColor(settings.color.cgColor)
        context.fill(CGRect(x: 0, y: 0, width: outWidth, height: outHeight))

        let imageRect = CGRect(
            x: CGFloat(padding.left),
            y: CGFloat(padding.bottom),
            width: CGFloat(width),
            height: CGFloat(height)
        )

        context.interpolationQuality = .high
        context.draw(cgImage, in: imageRect)

        guard let outputCGImage = context.makeImage() else {
            throw RenderError.imageRenderingFailed
        }

        return (outputCGImage, padding)
    }

    public static func renderPreview(
        item: ImageItem,
        settings: BorderSettings
    ) -> (image: NSImage, padding: CalculatedPadding)? {
        let previewCG = item.previewCGImage
        let originalW = Double(item.width)
        let previewW = Double(previewCG.width)
        let scale = previewW / max(originalW, 1.0)

        var scaledSettings = settings
        if scaledSettings.mode == .auto {
            scaledSettings.autoThickness = Int(round(Double(settings.autoThickness) * scale))
        } else {
            scaledSettings.top = Int(round(Double(settings.top) * scale))
            scaledSettings.bottom = Int(round(Double(settings.bottom) * scale))
            scaledSettings.left = Int(round(Double(settings.left) * scale))
            scaledSettings.right = Int(round(Double(settings.right) * scale))
        }

        guard let rendered = try? renderBorderedImage(cgImage: previewCG, settings: scaledSettings) else {
            return nil
        }

        let fullPadding = AutoBorderCalculator.calculate(width: item.width, height: item.height, settings: settings)
        let nsImage = NSImage(cgImage: rendered.image, size: NSSize(width: rendered.image.width, height: rendered.image.height))
        return (nsImage, fullPadding)
    }

    public static func export(
        item: ImageItem,
        settings: BorderSettings,
        to destinationURL: URL
    ) throws {
        let (outputCGImage, _) = try renderBorderedImage(cgImage: item.cgImage, settings: settings)

        let ext = destinationURL.pathExtension.lowercased()
        let utType: UTType
        let properties: [CFString: Any]

        switch ext {
        case "jpg", "jpeg":
            utType = .jpeg
            properties = [kCGImageDestinationLossyCompressionQuality: 0.95]
        case "png":
            utType = .png
            properties = [:]
        case "tiff", "tif":
            utType = .tiff
            properties = [:]
        case "heic":
            utType = .heic
            properties = [kCGImageDestinationLossyCompressionQuality: 0.95]
        default:
            utType = .jpeg
            properties = [kCGImageDestinationLossyCompressionQuality: 0.95]
        }

        guard let destination = CGImageDestinationCreateWithURL(
            destinationURL as CFURL,
            utType.identifier as CFString,
            1,
            nil
        ) else {
            throw RenderError.destinationCreationFailed
        }

        CGImageDestinationAddImage(destination, outputCGImage, properties as CFDictionary)

        guard CGImageDestinationFinalize(destination) else {
            throw RenderError.exportFailed
        }
    }

    public static func suggestedFilename(for item: ImageItem) -> (baseName: String, extensionName: String) {
        if let originalURL = item.url {
            let base = originalURL.deletingPathExtension().lastPathComponent
            let rawExt = originalURL.pathExtension.lowercased()
            let rawExtensions = ["nef", "arw", "cr2", "cr3", "dng", "raw", "orf", "rw2"]
            let ext = rawExtensions.contains(rawExt) ? "jpg" : (rawExt.isEmpty ? "png" : rawExt)
            return (base, ext)
        } else {
            return (item.displayName, "png")
        }
    }
}
