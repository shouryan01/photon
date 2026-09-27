import SwiftUI

public struct AutoModeControlsView: View {
    @ObservedObject var viewModel: BorderStudioViewModel

    public init(viewModel: BorderStudioViewModel) {
        self.viewModel = viewModel
    }


    public var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            // Aspect Ratio section
            VStack(alignment: .leading, spacing: 6) {
                Text("Target Aspect Ratio")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(.secondary)

                VStack(spacing: 6) {
                    HStack(spacing: 6) {
                        aspectRatioButton(.standard3x4)
                        aspectRatioButton(.feed4x5)
                        aspectRatioButton(.square1x1)
                        aspectRatioButton(.story9x16)
                    }
                    HStack(spacing: 6) {
                        aspectRatioButton(.polaroid)
                        aspectRatioButton(.widescreen16x9)
                        aspectRatioButton(.standard4x3)
                    }
                }
            }

            // Thickness slider section (hidden when Polaroid is selected since it uses fixed proportions)
            if viewModel.currentSettings.autoRatio.name != "Polaroid" {
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text("Base Thickness")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundStyle(.secondary)
                        Spacer()
                        TextField("0", text: Binding(
                            get: { String(viewModel.currentSettings.autoThickness) },
                            set: { if let v = Int($0) {
                                var s = viewModel.currentSettings
                                s.autoThickness = max(0, min(10000, v))
                                viewModel.currentSettings = s
                            }}
                        ))
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 60)
                        .multilineTextAlignment(.trailing)
                        Text("px")
                            .font(.system(size: 11))
                            .foregroundStyle(.secondary)
                    }

                    Slider(value: Binding(
                        get: { Double(viewModel.currentSettings.autoThickness) },
                        set: { newThickness in
                            var s = viewModel.currentSettings
                            s.autoThickness = Int(round(newThickness))
                            viewModel.currentSettings = s
                        }
                    ), in: 0...500)
                }
            }

            // Real-time info summary
            if let padding = viewModel.activePadding, let active = viewModel.activeImage {
                VStack(alignment: .leading, spacing: 4) {
                    let isLandscape = active.width > active.height
                    let isPortrait = active.height > active.width
                    let orientation = isPortrait ? "Portrait" : (isLandscape ? "Landscape" : "Square")

                    HStack {
                        Text("Source:")
                            .foregroundStyle(.secondary)
                        Text("\(active.width) × \(active.height) px (\(orientation))")
                            .foregroundStyle(.primary)
                    }

                    HStack {
                        Text("Output:")
                            .foregroundStyle(.secondary)
                        Text("\(padding.outputWidth) × \(padding.outputHeight) px (\(viewModel.currentSettings.autoRatio.name))")
                            .foregroundStyle(.primary)
                            .bold()
                    }

                    HStack {
                        Text("Padding:")
                            .foregroundStyle(.secondary)
                        if padding.top == padding.bottom {
                            Text("T/B: \(padding.top)px | L/R: \(padding.left)px")
                                .foregroundStyle(.primary)
                        } else {
                            Text("T: \(padding.top)px | B: \(padding.bottom)px | L/R: \(padding.left)px")
                                .foregroundStyle(.primary)
                        }
                    }
                }
                .font(.system(size: 11))
                .padding(8)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color(nsColor: .controlBackgroundColor).opacity(0.5))
                .clipShape(RoundedRectangle(cornerRadius: 6))
            }
        }
    }

    @ViewBuilder
    private func aspectRatioButton(_ preset: AspectRatio) -> some View {
        let isSelected = viewModel.currentSettings.autoRatio.id == preset.id
        if isSelected {
            Button {
                var s = viewModel.currentSettings
                s.autoRatio = preset
                viewModel.currentSettings = s
            } label: {
                Text(preset.name)
                    .font(.system(size: 11, weight: .bold))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 6)
            }
            .buttonStyle(.borderedProminent)
            .tint(.accentColor)
            .help(preset.tooltip)
        } else {
            Button {
                var s = viewModel.currentSettings
                s.autoRatio = preset
                viewModel.currentSettings = s
            } label: {
                Text(preset.name)
                    .font(.system(size: 11, weight: .regular))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 6)
            }
            .buttonStyle(.bordered)
            .help(preset.tooltip)
        }
    }
}
