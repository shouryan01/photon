import SwiftUI

public struct CanvasInfoBadge: View {
    let originalWidth: Int
    let originalHeight: Int
    let outputWidth: Int
    let outputHeight: Int
    let ratioName: String
    let topPadding: Int
    let bottomPadding: Int
    let leftPadding: Int

    public var body: some View {
        HStack(spacing: 8) {
            // Source dimensions
            Text("\(originalWidth) × \(originalHeight)")
                .font(.system(size: 11, design: .monospaced))
                .foregroundStyle(.secondary)

            Image(systemName: "arrow.right")
                .font(.system(size: 9, weight: .bold))
                .foregroundStyle(.tertiary)

            // Output dimensions & ratio
            Text("\(outputWidth) × \(outputHeight) (\(ratioName))")
                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                .foregroundStyle(.primary)

            Divider()
                .frame(height: 12)

            // Padding
            if topPadding == bottomPadding {
                Text("T/B: \(topPadding)px  L/R: \(leftPadding)px")
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(.secondary)
            } else {
                Text("T: \(topPadding)px  B: \(bottomPadding)px  L/R: \(leftPadding)px")
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(.ultraThinMaterial)
        .clipShape(Capsule())
        .overlay(
            Capsule()
                .stroke(Color.primary.opacity(0.1), lineWidth: 0.5)
        )
        .shadow(color: .black.opacity(0.2), radius: 4, y: 2)
    }
}
