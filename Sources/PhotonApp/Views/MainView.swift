import SwiftUI
import AppKit

public struct MainView: View {
    @StateObject private var viewModel = BorderStudioViewModel()

    public init() {}

    public var body: some View {
        HStack(spacing: 0) {
            // Sidebar Controls (Fixed 360pt)
            BorderSidebarView(viewModel: viewModel)

            Divider()

            // Central Canvas Area
            VStack(spacing: 0) {
                CanvasView(viewModel: viewModel)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                // Bottom Filmstrip Carousel (Auto-displays when 2+ photos)
                if viewModel.images.count >= 2 {
                    FilmstripView(viewModel: viewModel)
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                }
            }
            .animation(.easeInOut(duration: 0.25), value: viewModel.images.count >= 2)
        }
        .frame(minWidth: 900, minHeight: 650)
        .sheet(isPresented: $viewModel.isExportingBatch) {
            BatchExportSheet(viewModel: viewModel)
        }
        .alert("Export Finished", isPresented: $viewModel.showBatchAlert) {
            if let outDir = viewModel.outputDirectory {
                Button("Show in Finder") {
                    NSWorkspace.shared.activateFileViewerSelecting([outDir])
                }
            }
            Button("Done", role: .cancel) {}
        } message: {
            if let msg = viewModel.batchAlertMessage {
                Text(msg)
            }
        }
        // Keyboard Shortcuts
        .focusable()
        .onKeyPress(.delete) {
            viewModel.removeActiveImage()
            return .handled
        }
        .onKeyPress(.leftArrow) {
            viewModel.selectPreviousImage()
            return .handled
        }
        .onKeyPress(.rightArrow) {
            viewModel.selectNextImage()
            return .handled
        }
        .onAppear {
            // Support global shortcuts (⌘V paste, ⌘O open, ⌘S export)
            NSEvent.addLocalMonitorForEvents(matching: .keyDown) { event in
                let flags = event.modifierFlags.intersection(.deviceIndependentFlagsMask)
                if flags == .command {
                    switch event.charactersIgnoringModifiers {
                    case "v":
                        handlePaste()
                        return nil
                    case "o":
                        viewModel.pickImages()
                        return nil
                    case "s":
                        viewModel.export()
                        return nil
                    default:
                        break
                    }
                }
                return event
            }
        }
    }

    private func handlePaste() {
        let pasteboard = NSPasteboard.general
        if let image = NSImage(pasteboard: pasteboard) {
            viewModel.addPastedImage(image)
        }
    }
}
