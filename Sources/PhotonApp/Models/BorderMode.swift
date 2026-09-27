import Foundation

public enum BorderMode: String, CaseIterable, Identifiable, Codable, Sendable {
    case auto = "auto"
    case manual = "manual"

    public var id: String { rawValue }

    public var title: String {
        switch self {
        case .auto:
            return "Auto"
        case .manual:
            return "Manual"
        }
    }

    public var iconName: String {
        switch self {
        case .auto:
            return "aspectratio"
        case .manual:
            return "slider.horizontal.2.square"
        }
    }
}
