import SwiftUI

public struct ColorPaletteView: View {
    @ObservedObject var viewModel: BorderStudioViewModel

    public init(viewModel: BorderStudioViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Border Color")
                .font(.system(size: 11, weight: .semibold))
                .foregroundStyle(.secondary)

            HStack(spacing: 8) {
                // Color Picker
                ColorPicker("", selection: Binding(
                    get: { viewModel.currentSettings.color.swiftUIColor },
                    set: { newColor in
                        var s = viewModel.currentSettings
                        s.color.swiftUIColor = newColor
                        viewModel.currentSettings = s
                    }
                ), supportsOpacity: false)
                .labelsHidden()
                .frame(width: 32, height: 26)

                // Quick preset color chips
                HStack(spacing: 6) {
                    ForEach(CodableColor.palettePresets, id: \.name) { preset in
                        let isSelected = viewModel.currentSettings.color.hexString == preset.color.hexString
                        Button {
                            var s = viewModel.currentSettings
                            s.color = preset.color
                            viewModel.currentSettings = s
                        } label: {
                            Circle()
                                .fill(preset.color.swiftUIColor)
                                .frame(width: 20, height: 20)
                                .overlay(
                                    Circle()
                                        .stroke(isSelected ? Color.blue : Color.gray.opacity(0.4), lineWidth: isSelected ? 2 : 1)
                                )
                        }
                        .buttonStyle(.plain)
                        .help(preset.name)
                    }
                }

                Spacer()

                // Hex readout
                Text(viewModel.currentSettings.color.hexString)
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(.secondary)
            }
        }
    }
}
