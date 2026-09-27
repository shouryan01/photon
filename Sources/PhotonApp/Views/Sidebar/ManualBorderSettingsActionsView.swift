import SwiftUI

public struct ManualBorderSettingsActionsView: View {
    @ObservedObject var viewModel: BorderStudioViewModel

    public init(viewModel: BorderStudioViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Save / Load Border Settings")
                .font(.system(size: 11, weight: .semibold))
                .foregroundStyle(.secondary)

            // Save / Load Border Settings
            HStack(spacing: 8) {
                Button {
                    viewModel.savePreset()
                } label: {
                    Label("Save Settings", systemImage: "square.and.arrow.down")
                        .font(.system(size: 11))
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)

                Button {
                    viewModel.loadPreset()
                } label: {
                    Label("Load Settings", systemImage: "square.and.arrow.up")
                        .font(.system(size: 11))
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
            }
        }
    }
}

public typealias ManualJsonActionsView = ManualBorderSettingsActionsView
