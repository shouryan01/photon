import SwiftUI
import AppKit
import UniformTypeIdentifiers

public struct ThumbnailItemView: View {
    let item: ImageItem
    let isSelected: Bool
    let onSelect: () -> Void
    let onRemove: () -> Void

    @State private var isHovering: Bool = false

    public init(item: ImageItem, isSelected: Bool, onSelect: @escaping () -> Void, onRemove: @escaping () -> Void) {
        self.item = item
        self.isSelected = isSelected
        self.onSelect = onSelect
        self.onRemove = onRemove
    }

    public var body: some View {
        Button(action: onSelect) {
            VStack(spacing: 4) {
                ZStack(alignment: .topTrailing) {
                    Image(nsImage: item.thumbnail)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(width: 68, height: 68)
                        .background(Color.black.opacity(0.3))
                        .clipShape(RoundedRectangle(cornerRadius: 6))
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(isSelected ? Color.accentColor : Color.primary.opacity(0.15), lineWidth: isSelected ? 2.5 : 1)
                        )

                    // Individual photo custom override badge
                    if item.isCustomized {
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 8, height: 8)
                            .padding(4)
                            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
                            .help("Has custom border settings")
                    }

                    // Hover Delete Button
                    if isHovering {
                        Button(action: onRemove) {
                            Image(systemName: "xmark.circle.fill")
                                .font(.system(size: 14))
                                .foregroundStyle(.white, .red)
                        }
                        .buttonStyle(.plain)
                        .offset(x: 4, y: -4)
                        .help("Remove photo from session")
                    }
                }

                Text(item.displayName)
                    .font(.system(size: 10))
                    .foregroundStyle(isSelected ? .primary : .secondary)
                    .lineLimit(1)
                    .frame(width: 72)
                    .truncationMode(.middle)
            }
            .padding(4)
            .background(isSelected ? Color.accentColor.opacity(0.1) : Color.clear)
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .buttonStyle(.plain)
        .onHover { isHovering = $0 }
    }
}

public struct AddThumbnailButton: View {
    let action: () -> Void
    var onDropFiles: (([URL]) -> Void)? = nil

    @State private var isHovering: Bool = false
    @State private var isTargeted: Bool = false

    public init(action: @escaping () -> Void, onDropFiles: (([URL]) -> Void)? = nil) {
        self.action = action
        self.onDropFiles = onDropFiles
    }

    public var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                ZStack {
                    RoundedRectangle(cornerRadius: 6)
                        .fill(isHovering || isTargeted ? Color.accentColor.opacity(0.12) : Color.primary.opacity(0.04))
                        .frame(width: 68, height: 68)

                    RoundedRectangle(cornerRadius: 6)
                        .strokeBorder(
                            isTargeted ? Color.accentColor : (isHovering ? Color.accentColor : Color.primary.opacity(0.2)),
                            style: StrokeStyle(lineWidth: isHovering || isTargeted ? 1.5 : 1, dash: [4, 3])
                        )
                        .frame(width: 68, height: 68)

                    Image(systemName: "plus")
                        .font(.system(size: 22, weight: .medium))
                        .foregroundStyle(isHovering || isTargeted ? Color.accentColor : .secondary)
                }

                Text("Add Image")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundStyle(isHovering || isTargeted ? Color.accentColor : .secondary)
                    .lineLimit(1)
                    .frame(width: 72)
            }
            .padding(4)
            .background(isHovering ? Color.accentColor.opacity(0.06) : Color.clear)
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.15)) {
                isHovering = hovering
            }
        }
        .help("Add more photos to session (⌘O)")
        .onDrop(of: [.fileURL], isTargeted: $isTargeted) { providers in
            guard let onDropFiles = onDropFiles else { return false }
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
                    onDropFiles(urlsToLoad)
                }
            }
            return true
        }
    }
}
