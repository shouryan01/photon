import SwiftUI

public struct BorderSidebarView: View {
    @ObservedObject var viewModel: BorderStudioViewModel

    public init(viewModel: BorderStudioViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        VStack(spacing: 0) {
            // Scrollable Settings
            ScrollView(.vertical, showsIndicators: true) {
                VStack(spacing: 16) {
                    // Mode Selector & Apply to all
                    ModeSelectorView(viewModel: viewModel)

                    Divider()

                    // Controls based on mode
                    Group {
                        if viewModel.currentSettings.mode == .auto {
                            AutoModeControlsView(viewModel: viewModel)
                        } else {
                            ManualModeControlsView(viewModel: viewModel)
                        }
                    }
                    .animation(nil, value: viewModel.currentSettings.mode)

                    Divider()

                    // Color palette
                    ColorPaletteView(viewModel: viewModel)

                    // Manual Mode Actions (Save/Load Border Settings)
                    if viewModel.currentSettings.mode == .manual {
                        Divider()
                        ManualBorderSettingsActionsView(viewModel: viewModel)
                    }
                }
                .padding(16)
            }
            .frame(maxHeight: .infinity)

            // Pinned Bottom Download / Export Button
            ExportButtonView(viewModel: viewModel)
        }
        .frame(width: 360)
        .background(.ultraThinMaterial)
    }
}
