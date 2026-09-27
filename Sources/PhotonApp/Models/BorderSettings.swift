import Foundation
import SwiftUI
import AppKit

public struct CodableColor: Codable, Hashable, Sendable {
    public var red: Double
    public var green: Double
    public var blue: Double
    public var alpha: Double

    public init(red: Double, green: Double, blue: Double, alpha: Double = 1.0) {
        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha
    }

    public init(hex: String) {
        var cleanHex = hex.trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
        if cleanHex.hasPrefix("#") {
            cleanHex.removeFirst()
        }
        var rgbValue: UInt64 = 0
        Scanner(string: cleanHex).scanHexInt64(&rgbValue)

        if cleanHex.count == 6 {
            self.red = Double((rgbValue & 0xFF0000) >> 16) / 255.0
            self.green = Double((rgbValue & 0x00FF00) >> 8) / 255.0
            self.blue = Double(rgbValue & 0x0000FF) / 255.0
            self.alpha = 1.0
        } else if cleanHex.count == 8 {
            self.red = Double((rgbValue & 0xFF000000) >> 24) / 255.0
            self.green = Double((rgbValue & 0x00FF0000) >> 16) / 255.0
            self.blue = Double((rgbValue & 0x0000FF00) >> 8) / 255.0
            self.alpha = Double(rgbValue & 0x000000FF) / 255.0
        } else {
            self.red = 1.0
            self.green = 1.0
            self.blue = 1.0
            self.alpha = 1.0
        }
    }

    public var swiftUIColor: Color {
        get {
            Color(.sRGB, red: red, green: green, blue: blue, opacity: alpha)
        }
        set {
            if let nsColor = NSColor(newValue).usingColorSpace(.sRGB) {
                self.red = Double(nsColor.redComponent)
                self.green = Double(nsColor.greenComponent)
                self.blue = Double(nsColor.blueComponent)
                self.alpha = Double(nsColor.alphaComponent)
            }
        }
    }

    public var nsColor: NSColor {
        NSColor(srgbRed: red, green: green, blue: blue, alpha: alpha)
    }

    public var cgColor: CGColor {
        CGColor(srgbRed: CGFloat(red), green: CGFloat(green), blue: CGFloat(blue), alpha: CGFloat(alpha))
    }

    public var hexString: String {
        let r = Int(round(red * 255))
        let g = Int(round(green * 255))
        let b = Int(round(blue * 255))
        return String(format: "#%02X%02X%02X", r, g, b)
    }

    public static let white = CodableColor(red: 1.0, green: 1.0, blue: 1.0, alpha: 1.0)
    public static let black = CodableColor(red: 0.0, green: 0.0, blue: 0.0, alpha: 1.0)
    public static let galleryOffWhite = CodableColor(hex: "#F7F6F2")
    public static let warmPaper = CodableColor(hex: "#F0EDE6")
    public static let charcoal = CodableColor(hex: "#1E1E1E")

    public static let palettePresets: [(name: String, color: CodableColor)] = [
        ("White", .white),
        ("Black", .black),
        ("Off-White", .galleryOffWhite),
        ("Warm Paper", .warmPaper),
        ("Charcoal", .charcoal)
    ]
}

public struct BorderSettings: Codable, Hashable, Sendable {
    public var mode: BorderMode
    public var autoRatio: AspectRatio
    public var autoThickness: Int
    public var top: Int
    public var bottom: Int
    public var left: Int
    public var right: Int
    public var linkVertical: Bool
    public var linkHorizontal: Bool
    public var linkAll: Bool
    public var color: CodableColor

    public var linkSides: Bool {
        get { linkAll }
        set {
            linkAll = newValue
            if newValue {
                linkVertical = true
                linkHorizontal = true
            }
        }
    }

    public init(
        mode: BorderMode = .auto,
        autoRatio: AspectRatio = .standard3x4,
        autoThickness: Int = 0,
        top: Int = 0,
        bottom: Int = 0,
        left: Int = 0,
        right: Int = 0,
        linkVertical: Bool = true,
        linkHorizontal: Bool = true,
        linkAll: Bool = true,
        color: CodableColor = .white
    ) {
        self.mode = mode
        self.autoRatio = autoRatio
        self.autoThickness = autoThickness
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right
        self.linkVertical = linkVertical
        self.linkHorizontal = linkHorizontal
        self.linkAll = linkAll
        self.color = color
    }

    public init(
        mode: BorderMode = .auto,
        autoRatio: AspectRatio = .standard3x4,
        autoThickness: Int = 0,
        top: Int = 0,
        bottom: Int = 0,
        left: Int = 0,
        right: Int = 0,
        linkSides: Bool,
        color: CodableColor = .white
    ) {
        self.mode = mode
        self.autoRatio = autoRatio
        self.autoThickness = autoThickness
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right
        self.linkVertical = linkSides
        self.linkHorizontal = linkSides
        self.linkAll = linkSides
        self.color = color
    }

    enum CodingKeys: String, CodingKey {
        case mode
        case autoRatio
        case autoThickness
        case top
        case bottom
        case left
        case right
        case linkVertical
        case linkHorizontal
        case linkAll
        case linkSides
        case linkMode
        case linkTop
        case linkBottom
        case linkLeft
        case linkRight
        case color
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.mode = try container.decode(BorderMode.self, forKey: .mode)
        self.autoRatio = try container.decode(AspectRatio.self, forKey: .autoRatio)
        self.autoThickness = try container.decode(Int.self, forKey: .autoThickness)
        self.top = try container.decode(Int.self, forKey: .top)
        self.bottom = try container.decode(Int.self, forKey: .bottom)
        self.left = try container.decode(Int.self, forKey: .left)
        self.right = try container.decode(Int.self, forKey: .right)
        self.color = try container.decode(CodableColor.self, forKey: .color)

        if let lv = try? container.decode(Bool.self, forKey: .linkVertical),
           let lh = try? container.decode(Bool.self, forKey: .linkHorizontal),
           let la = try? container.decode(Bool.self, forKey: .linkAll) {
            self.linkVertical = lv
            self.linkHorizontal = lh
            self.linkAll = la
        } else if let linkModeStr = try? container.decode(String.self, forKey: .linkMode) {
            if linkModeStr == "opposites" {
                self.linkVertical = true
                self.linkHorizontal = true
                self.linkAll = false
            } else if linkModeStr == "none" {
                self.linkVertical = false
                self.linkHorizontal = false
                self.linkAll = false
            } else {
                self.linkVertical = true
                self.linkHorizontal = true
                self.linkAll = true
            }
        } else if let lt = try? container.decode(Bool.self, forKey: .linkTop),
                  let lb = try? container.decode(Bool.self, forKey: .linkBottom),
                  let ll = try? container.decode(Bool.self, forKey: .linkLeft),
                  let lr = try? container.decode(Bool.self, forKey: .linkRight) {
            self.linkVertical = lt && lb
            self.linkHorizontal = ll && lr
            self.linkAll = lt && lb && ll && lr
        } else if let linkSidesBool = try? container.decode(Bool.self, forKey: .linkSides) {
            self.linkVertical = linkSidesBool
            self.linkHorizontal = linkSidesBool
            self.linkAll = linkSidesBool
        } else {
            self.linkVertical = true
            self.linkHorizontal = true
            self.linkAll = true
        }
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(mode, forKey: .mode)
        try container.encode(autoRatio, forKey: .autoRatio)
        try container.encode(autoThickness, forKey: .autoThickness)
        try container.encode(top, forKey: .top)
        try container.encode(bottom, forKey: .bottom)
        try container.encode(left, forKey: .left)
        try container.encode(right, forKey: .right)
        try container.encode(linkVertical, forKey: .linkVertical)
        try container.encode(linkHorizontal, forKey: .linkHorizontal)
        try container.encode(linkAll, forKey: .linkAll)
        try container.encode(linkAll, forKey: .linkSides)
        try container.encode(color, forKey: .color)
    }

    public static let `default` = BorderSettings()

    public static let polaroid = BorderSettings(
        mode: .manual,
        autoRatio: .square1x1,
        autoThickness: 0,
        top: 60,
        bottom: 180,
        left: 60,
        right: 60,
        linkVertical: false,
        linkHorizontal: true,
        linkAll: false,
        color: .white
    )

    public static let instagramFeed = BorderSettings(
        mode: .auto,
        autoRatio: .feed4x5,
        autoThickness: 40,
        color: .white
    )

    public static let cleanSquare = BorderSettings(
        mode: .auto,
        autoRatio: .square1x1,
        autoThickness: 50,
        color: .white
    )

    public static let storyReel = BorderSettings(
        mode: .auto,
        autoRatio: .story9x16,
        autoThickness: 60,
        color: .charcoal
    )
}
