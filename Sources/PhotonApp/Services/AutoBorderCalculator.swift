import Foundation

public struct CalculatedPadding: Equatable, Sendable {
    public let top: Int
    public let bottom: Int
    public let left: Int
    public let right: Int
    public let outputWidth: Int
    public let outputHeight: Int

    public var totalHorizontalPadding: Int { left + right }
    public var totalVerticalPadding: Int { top + bottom }
}

public struct AutoBorderCalculator {
    public static func calculate(
        width: Int,
        height: Int,
        targetWidthRatio: Int,
        targetHeightRatio: Int,
        thickness: Int = 0
    ) -> CalculatedPadding {
        guard width > 0, height > 0, targetWidthRatio > 0, targetHeightRatio > 0 else {
            return CalculatedPadding(top: 0, bottom: 0, left: 0, right: 0, outputWidth: width, outputHeight: height)
        }

        // Authentic Polaroid frame calculation (fixed proportions based on image size)
        if targetWidthRatio == 88 && targetHeightRatio == 107 {
            return calculatePolaroid(width: width, height: height)
        }

        let targetRatio = Double(targetWidthRatio) / Double(targetHeightRatio)
        let minW = Double(width + 2 * thickness)
        let minH = Double(height + 2 * thickness)

        let candW = (minH * targetRatio).rounded()
        let outW: Int
        let outH: Int

        if candW >= minW {
            outW = Int(candW)
            outH = Int(minH)
        } else {
            outW = Int(minW)
            outH = Int((minW / targetRatio).rounded())
        }

        let padW = max(0, outW - width)
        let padH = max(0, outH - height)

        let left = padW / 2
        let right = padW - left
        let top = padH / 2
        let bottom = padH - top

        return CalculatedPadding(
            top: top,
            bottom: bottom,
            left: left,
            right: right,
            outputWidth: outW,
            outputHeight: outH
        )
    }

    public static func calculate(
        width: Int,
        height: Int,
        settings: BorderSettings
    ) -> CalculatedPadding {
        switch settings.mode {
        case .auto:
            return calculate(
                width: width,
                height: height,
                targetWidthRatio: settings.autoRatio.widthRatio,
                targetHeightRatio: settings.autoRatio.heightRatio,
                thickness: settings.autoThickness
            )
        case .manual:
            let outW = width + settings.left + settings.right
            let outH = height + settings.top + settings.bottom
            return CalculatedPadding(
                top: settings.top,
                bottom: settings.bottom,
                left: settings.left,
                right: settings.right,
                outputWidth: outW,
                outputHeight: outH
            )
        }
    }

    private static func calculatePolaroid(
        width: Int,
        height: Int
    ) -> CalculatedPadding {
        // Authentic Polaroid proportions based on 79mm image in 88mm x 107mm frame:
        // Top & side margins: 4.5mm / 79mm ≈ 5.70%
        // Bottom chin margin: 23.5mm / 79mm ≈ 29.75% (5.22x top margin)
        let ref = Double(min(width, height))
        let sideAndTop = max(12, Int((ref * (4.5 / 79.0)).rounded()))
        let bottom = max(sideAndTop * 3, Int((ref * (23.5 / 79.0)).rounded()))

        let outW = width + sideAndTop * 2
        let outH = height + sideAndTop + bottom

        return CalculatedPadding(
            top: sideAndTop,
            bottom: bottom,
            left: sideAndTop,
            right: sideAndTop,
            outputWidth: outW,
            outputHeight: outH
        )
    }
}
