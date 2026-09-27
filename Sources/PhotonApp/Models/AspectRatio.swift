import Foundation

public struct AspectRatio: Identifiable, Hashable, Codable, Sendable {
    public let id: String
    public let name: String
    public let widthRatio: Int
    public let heightRatio: Int
    public let tooltip: String

    public init(name: String, widthRatio: Int, heightRatio: Int, tooltip: String) {
        self.id = "\(widthRatio):\(heightRatio)"
        self.name = name
        self.widthRatio = widthRatio
        self.heightRatio = heightRatio
        self.tooltip = tooltip
    }

    public var ratioValue: Double {
        guard heightRatio > 0 else { return 1.0 }
        return Double(widthRatio) / Double(heightRatio)
    }

    public static let standard3x4 = AspectRatio(name: "3:4", widthRatio: 3, heightRatio: 4, tooltip: "3:4 Portrait (IG)")
    public static let feed4x5 = AspectRatio(name: "4:5", widthRatio: 4, heightRatio: 5, tooltip: "4:5 Feed Portrait")
    public static let square1x1 = AspectRatio(name: "1:1", widthRatio: 1, heightRatio: 1, tooltip: "1:1 Square")
    public static let story9x16 = AspectRatio(name: "9:16", widthRatio: 9, heightRatio: 16, tooltip: "9:16 Story / Reel")
    public static let polaroid = AspectRatio(name: "Polaroid", widthRatio: 88, heightRatio: 107, tooltip: "Polaroid (88:107)")
    public static let widescreen16x9 = AspectRatio(name: "16:9", widthRatio: 16, heightRatio: 9, tooltip: "16:9 Widescreen")
    public static let standard4x3 = AspectRatio(name: "4:3", widthRatio: 4, heightRatio: 3, tooltip: "4:3 Standard")

    public static let presets: [AspectRatio] = [
        .standard3x4,
        .feed4x5,
        .square1x1,
        .story9x16,
        .polaroid,
        .widescreen16x9,
        .standard4x3
    ]
}
