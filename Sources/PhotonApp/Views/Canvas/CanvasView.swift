import SwiftUI
import AppKit
import UniformTypeIdentifiers

public struct CanvasView: View {
    @ObservedObject var viewModel: BorderStudioViewModel
    @State private var isTargeted: Bool = false
    @State private var isAddHovered: Bool = false

    public init(viewModel: BorderStudioViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        ZStack {
            // Minimal Studio Canvas Backdrop
            Color(nsColor: .underPageBackgroundColor)
                .ignoresSafeArea()

            if let active = viewModel.activeImage, let padding = viewModel.activePadding {
                // Active Bordered Image Display
                VStack(spacing: 0) {
                    GeometryReader { geo in
                        let availableW = max(10, geo.size.width - 48)
                        let availableH = max(10, geo.size.height - 48)

                        let outW = CGFloat(padding.outputWidth)
                        let outH = CGFloat(padding.outputHeight)
                        let scale = min(availableW / outW, availableH / outH)

                        let frameW = outW * scale
                        let frameH = outH * scale

                        let imgW = CGFloat(active.width) * scale
                        let imgH = CGFloat(active.height) * scale
                        let padLeft = CGFloat(padding.left) * scale
                        let padTop = CGFloat(padding.top) * scale

                        ZStack(alignment: .topLeading) {
                            // Outer Border
                            Rectangle()
                                .fill(viewModel.currentSettings.color.swiftUIColor)
                                .frame(width: frameW, height: frameH)

                            // Inner Photo
                            Image(nsImage: active.displayImage)
                                .resizable()
                                // This is already a 1600 px preview image. Medium
                                // interpolation keeps interactive layout changes
                                // responsive without affecting export quality.
                                .interpolation(.medium)
                                .frame(width: imgW, height: imgH)
                                .offset(x: padLeft, y: padTop)

                            // Floating Delete Button (Top-Right of border box)
                            Button {
                                viewModel.removeActiveImage()
                            } label: {
                                Image(systemName: "xmark")
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundStyle(.white)
                                    .frame(width: 24, height: 24)
                                    .background(Color.black.opacity(0.65))
                                    .clipShape(Circle())
                                    .overlay(
                                        Circle()
                                            .stroke(Color.white.opacity(0.2), lineWidth: 1)
                                    )
                            }
                            .buttonStyle(.plain)
                            .offset(x: frameW - 32, y: 8)
                            .help("Remove photo from session (⌫)")
                        }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                    }
                    .padding(.top, 16)

                    // Bottom Floating Info HUD
                    CanvasInfoBadge(
                        originalWidth: active.width,
                        originalHeight: active.height,
                        outputWidth: padding.outputWidth,
                        outputHeight: padding.outputHeight,
                        ratioName: viewModel.currentSettings.mode == .auto ? viewModel.currentSettings.autoRatio.name : "Manual",
                        topPadding: padding.top,
                        bottomPadding: padding.bottom,
                        leftPadding: padding.left
                    )
                    .padding(.bottom, 16)
                }

                // Floating "Add Image" Button when only 1 image is in session
                if viewModel.images.count == 1 {
                    Button {
                        viewModel.pickImages()
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "plus")
                                .font(.system(size: 11, weight: .bold))
                            Text("Add Image")
                                .font(.system(size: 12, weight: .medium))
                        }
                        .foregroundStyle(isAddHovered ? Color.accentColor : Color.primary)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 7)
                        .background(.ultraThinMaterial)
                        .clipShape(Capsule())
                        .overlay(
                            Capsule()
                                .stroke(isAddHovered ? Color.accentColor : Color.primary.opacity(0.15), lineWidth: 1)
                        )
                        .shadow(color: Color.black.opacity(0.1), radius: 4, x: 0, y: 2)
                    }
                    .buttonStyle(.plain)
                    .onHover { hovering in
                        withAnimation(.easeInOut(duration: 0.15)) {
                            isAddHovered = hovering
                        }
                    }
                    .padding(16)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing)
                    .help("Add more images to session (⌘O)")
                    .onDrop(of: [.fileURL], isTargeted: $isAddHovered) { providers in
                        handleDrop(providers: providers)
                    }
                }
            } else {
                // Empty state dropzone
                VStack(spacing: 16) {
                    Image(systemName: "photo.on.rectangle.angled")
                        .font(.system(size: 48))
                        .foregroundStyle(.tertiary)

                    VStack(spacing: 6) {
                        Text("Drop Photos Here")
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundStyle(.primary)

                        Text("Drag & drop one or multiple images, or select from disk")
                            .font(.system(size: 12))
                            .foregroundStyle(.secondary)
                    }

                    Button {
                        viewModel.pickImages()
                    } label: {
                        Label("Pick Image(s)", systemImage: "plus")
                            .font(.system(size: 13, weight: .medium))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                    }
                    .buttonStyle(.borderedProminent)
                }
                .frame(maxWidth: 380, maxHeight: 240)
                .padding(32)
                .background(Color(nsColor: .controlBackgroundColor).opacity(0.4))
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .strokeBorder(
                            isTargeted ? Color.accentColor : Color.primary.opacity(0.15),
                            style: StrokeStyle(lineWidth: 2, dash: [8, 4])
                        )
                )
            }
        }
        .onDrop(of: [.fileURL], isTargeted: $isTargeted) { providers in
            handleDrop(providers: providers)
        }
    }

    private func handleDrop(providers: [NSItemProvider]) -> Bool {
        var urlsToLoad: [URL] = []
        let group = DispatchGroup()

        for provider in providers {
            group.enter()
            _ = provider.loadObject(ofClass: URL.self) { url, _ in
                if let u = url {
                    urlsToLoad.append(u)
                }
                group.leave()
            }
        }

        group.notify(queue: .main) {
            if !urlsToLoad.isEmpty {
                viewModel.addImages(from: urlsToLoad)
            }
        }
        return true
    }
}

