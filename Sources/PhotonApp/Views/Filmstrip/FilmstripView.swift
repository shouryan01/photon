import SwiftUI
import AppKit
import UniformTypeIdentifiers

public struct FilmstripView: View {
    @ObservedObject var viewModel: BorderStudioViewModel

    public init(viewModel: BorderStudioViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        VStack(spacing: 0) {
            Divider()

            HStack(spacing: 8) {
                // Navigation Prev Button
                Button {
                    viewModel.selectPreviousImage()
                } label: {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundStyle(.secondary)
                        .frame(width: 24, height: 60)
                        .background(Color.primary.opacity(0.04))
                        .clipShape(RoundedRectangle(cornerRadius: 4))
                }
                .buttonStyle(.plain)
                .disabled(viewModel.images.count <= 1)
                .opacity(viewModel.images.count <= 1 ? 0.3 : 1.0)
                .help("Previous photo (←)")

                // Thumbnails Scroll Area
                ScrollViewReader { proxy in
                    ScrollView(.horizontal, showsIndicators: false) {
                        LazyHStack(spacing: 8) {
                            ForEach(Array(viewModel.images.enumerated()), id: \.element.id) { index, item in
                                ThumbnailItemView(
                                    item: item,
                                    isSelected: viewModel.selectedImageIndex == index,
                                    onSelect: {
                                        viewModel.selectImage(at: index)
                                    },
                                    onRemove: {
                                        viewModel.removeImage(at: index)
                                    }
                                )
                                .id(item.id)
                            }

                            // Add More Photos Button at the end of the filmstrip
                            AddThumbnailButton(
                                action: {
                                    viewModel.pickImages()
                                },
                                onDropFiles: { urls in
                                    viewModel.addImages(from: urls)
                                }
                            )
                            .id("filmstrip_add_button")
                        }
                        .padding(.horizontal, 4)
                        .padding(.vertical, 8)
                    }
                    .onChange(of: viewModel.selectedImageIndex) { _, newIndex in
                        if let idx = newIndex, viewModel.images.indices.contains(idx) {
                            withAnimation(.easeInOut(duration: 0.2)) {
                                proxy.scrollTo(viewModel.images[idx].id, anchor: .center)
                            }
                        }
                    }
                }

                // Navigation Next Button
                Button {
                    viewModel.selectNextImage()
                } label: {
                    Image(systemName: "chevron.right")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundStyle(.secondary)
                        .frame(width: 24, height: 60)
                        .background(Color.primary.opacity(0.04))
                        .clipShape(RoundedRectangle(cornerRadius: 4))
                }
                .buttonStyle(.plain)
                .disabled(viewModel.images.count <= 1)
                .opacity(viewModel.images.count <= 1 ? 0.3 : 1.0)
                .help("Next photo (→)")
            }
            .padding(.horizontal, 12)
            .frame(height: 105)
            .background(.ultraThinMaterial)
            .onDrop(of: [.fileURL], isTargeted: nil) { providers in
                handleDrop(providers: providers)
            }
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
