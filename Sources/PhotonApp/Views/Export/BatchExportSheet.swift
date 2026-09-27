import SwiftUI

public struct BatchExportSheet: View {
    @ObservedObject var viewModel: BorderStudioViewModel

    public init(viewModel: BorderStudioViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        VStack(spacing: 18) {
            Image(systemName: "square.and.arrow.down.on.square.fill")
                .font(.system(size: 36))
                .foregroundStyle(Color.accentColor)

            VStack(spacing: 6) {
                Text("Exporting Bordered Photos")
                    .font(.system(size: 16, weight: .bold))

                let (completed, total) = viewModel.batchProgress
                Text("Processing \(completed) of \(total) images...")
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
            }

            let (completed, total) = viewModel.batchProgress
            ProgressView(value: Double(completed), total: max(1.0, Double(total)))
                .progressViewStyle(.linear)
                .frame(width: 260)

            Button("Cancel") {
                viewModel.cancelBatchExport()
            }
            .buttonStyle(.bordered)
            .keyboardShortcut(.cancelAction)
        }
        .padding(28)
        .frame(width: 320)
    }
}
