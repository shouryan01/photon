import SwiftUI

public struct ExportButtonView: View {
    @ObservedObject var viewModel: BorderStudioViewModel

    public init(viewModel: BorderStudioViewModel) {
        self.viewModel = viewModel
    }

    private var isEnabled: Bool {
        !viewModel.images.isEmpty && !viewModel.isExportingBatch
    }

    public var body: some View {
        VStack(spacing: 0) {
            Divider()

            Button {
                viewModel.export()
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: iconName)
                        .font(.system(size: 14, weight: .semibold))

                    Text(buttonTitle)
                        .font(.system(size: 13.5, weight: .semibold))
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
            }
            .buttonStyle(ExportButtonStyle(isEnabled: isEnabled))
            .disabled(!isEnabled)
            .help(tooltipText)
            .padding(.horizontal, 16)
            .padding(.top, 10)
            .padding(.bottom, 12)
        }
        .background(.ultraThinMaterial)
        .background(Color(nsColor: .windowBackgroundColor).opacity(0.75))
    }

    private var iconName: String {
        let count = viewModel.images.count
        if count == 0 {
            return "square.and.arrow.down"
        } else if count == 1 {
            return "square.and.arrow.down.fill"
        } else {
            return "square.and.arrow.down.on.square.fill"
        }
    }

    private var buttonTitle: String {
        let count = viewModel.images.count
        if count == 0 {
            return "Download Photo"
        } else if count == 1 {
            return "Download Photo"
        } else {
            return "Download All (\(count) Photos)"
        }
    }

    private var tooltipText: String {
        let count = viewModel.images.count
        if count == 0 {
            return "Add photos to export with borders (⌘S)"
        } else if count == 1 {
            return "Download bordered photo to disk (⌘S)"
        } else {
            return "Download all \(count) photos with borders (⌘S)"
        }
    }
}

// MARK: - Custom Export Button Style

private struct ExportButtonStyle: ButtonStyle {
    let isEnabled: Bool
    @State private var isHovered = false

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .foregroundStyle(isEnabled ? Color.white : Color.secondary.opacity(0.6))
            .background {
                if isEnabled {
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .fill(
                            LinearGradient(
                                colors: [
                                    Color.accentColor.opacity(0.96),
                                    Color.accentColor
                                ],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )
                        .overlay(
                            RoundedRectangle(cornerRadius: 8, style: .continuous)
                                .strokeBorder(
                                    LinearGradient(
                                        colors: [Color.white.opacity(0.28), Color.white.opacity(0.06)],
                                        startPoint: .top,
                                        endPoint: .bottom
                                    ),
                                    lineWidth: 0.75
                                )
                        )
                        .shadow(
                            color: Color.accentColor.opacity(isHovered ? 0.38 : 0.22),
                            radius: isHovered ? 6 : 4,
                            x: 0,
                            y: isHovered ? 3 : 2
                        )
                        .brightness(isHovered ? (configuration.isPressed ? -0.05 : 0.04) : (configuration.isPressed ? -0.08 : 0))
                } else {
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .fill(Color(nsColor: .controlBackgroundColor).opacity(0.65))
                        .overlay(
                            RoundedRectangle(cornerRadius: 8, style: .continuous)
                                .strokeBorder(Color.primary.opacity(0.08), lineWidth: 0.75)
                        )
                }
            }
            .scaleEffect(isEnabled && configuration.isPressed ? 0.985 : 1.0)
            .animation(.easeInOut(duration: 0.15), value: isHovered)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
            .onHover { hovering in
                isHovered = hovering
            }
    }
}
