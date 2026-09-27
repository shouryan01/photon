import SwiftUI

public struct ModeSelectorView: View {
    @ObservedObject var viewModel: BorderStudioViewModel

    public init(viewModel: BorderStudioViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        VStack(spacing: 8) {
            // Instant Segmented Mode Buttons
            HStack(spacing: 0) {
                modeButton(
                    title: "Auto",
                    systemImage: "aspectratio",
                    mode: .auto
                )

                modeButton(
                    title: "Manual",
                    systemImage: "slider.horizontal.2.square",
                    mode: .manual
                )
            }
            .background(Color(nsColor: .controlBackgroundColor))
            .clipShape(RoundedRectangle(cornerRadius: 7))
            .overlay(
                RoundedRectangle(cornerRadius: 7)
                    .stroke(Color.primary.opacity(0.12), lineWidth: 1)
            )

            if viewModel.images.count > 1 {
                Toggle(isOn: $viewModel.applyToAll) {
                    HStack(spacing: 4) {
                        Text("Apply to All Photos")
                            .font(.system(size: 12, weight: .medium))
                        if !viewModel.applyToAll, let idx = viewModel.selectedImageIndex {
                            Text("(Photo \(idx + 1) Only)")
                                .font(.system(size: 11))
                                .foregroundStyle(.blue)
                        }
                    }
                }
                .toggleStyle(.checkbox)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.top, 2)
            }
        }
    }

    @ViewBuilder
    private func modeButton(title: String, systemImage: String, mode: BorderMode) -> some View {
        let isSelected = viewModel.currentSettings.mode == mode

        Button {
            viewModel.setMode(mode)
        } label: {
            HStack(spacing: 6) {
                Image(systemName: systemImage)
                    .font(.system(size: 11, weight: isSelected ? .bold : .regular))
                Text(title)
                    .font(.system(size: 12, weight: isSelected ? .bold : .medium))
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 6)
            .background(isSelected ? Color.accentColor : Color.clear)
            .foregroundStyle(isSelected ? Color.white : Color.primary)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }
}
