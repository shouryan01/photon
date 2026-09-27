import SwiftUI

public struct ManualModeControlsView: View {
    @ObservedObject var viewModel: BorderStudioViewModel

    public init(viewModel: BorderStudioViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header with Master "Link All" button
            HStack {
                Text("Manual Borders")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(.secondary)

                Spacer()

                Button {
                    var s = viewModel.currentSettings
                    s.linkAll.toggle()
                    if s.linkAll {
                        s.linkVertical = true
                        s.linkHorizontal = true
                        s.bottom = s.top
                        s.left = s.top
                        s.right = s.top
                    }
                    viewModel.currentSettings = s
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: viewModel.currentSettings.linkAll ? "link" : "link.badge.plus")
                            .font(.system(size: 10))
                        Text("Link All")
                            .font(.system(size: 11, weight: viewModel.currentSettings.linkAll ? .semibold : .regular))
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(viewModel.currentSettings.linkAll ? Color.accentColor : Color(nsColor: .controlBackgroundColor))
                    .foregroundStyle(viewModel.currentSettings.linkAll ? Color.white : Color.primary)
                    .clipShape(RoundedRectangle(cornerRadius: 5))
                    .overlay(
                        RoundedRectangle(cornerRadius: 5)
                            .stroke(viewModel.currentSettings.linkAll ? Color.accentColor : Color.primary.opacity(0.12), lineWidth: 1)
                    )
                }
                .buttonStyle(.plain)
                .help(viewModel.currentSettings.linkAll ? "All 4 borders linked (Click to unlink)" : "Link all 4 borders together")
            }

            // Vertical Pair (Top & Bottom)
            borderPairView(
                firstLabel: "Top",
                firstValue: Binding(
                    get: { viewModel.currentSettings.top },
                    set: { val in
                        var s = viewModel.currentSettings
                        s.top = val
                        if s.linkAll {
                            s.bottom = val
                            s.left = val
                            s.right = val
                        } else if s.linkVertical {
                            s.bottom = val
                        }
                        viewModel.currentSettings = s
                    }
                ),
                secondLabel: "Bottom",
                secondValue: Binding(
                    get: { viewModel.currentSettings.bottom },
                    set: { val in
                        var s = viewModel.currentSettings
                        s.bottom = val
                        if s.linkAll {
                            s.top = val
                            s.left = val
                            s.right = val
                        } else if s.linkVertical {
                            s.top = val
                        }
                        viewModel.currentSettings = s
                    }
                ),
                isLinked: Binding(
                    get: { viewModel.currentSettings.linkVertical },
                    set: { active in
                        var s = viewModel.currentSettings
                        s.linkVertical = active
                        if active {
                            s.bottom = s.top
                        } else {
                            s.linkAll = false
                        }
                        viewModel.currentSettings = s
                    }
                ),
                tooltip: "Top & Bottom"
            )

            // Horizontal Pair (Left & Right)
            borderPairView(
                firstLabel: "Left",
                firstValue: Binding(
                    get: { viewModel.currentSettings.left },
                    set: { val in
                        var s = viewModel.currentSettings
                        s.left = val
                        if s.linkAll {
                            s.top = val
                            s.bottom = val
                            s.right = val
                        } else if s.linkHorizontal {
                            s.right = val
                        }
                        viewModel.currentSettings = s
                    }
                ),
                secondLabel: "Right",
                secondValue: Binding(
                    get: { viewModel.currentSettings.right },
                    set: { val in
                        var s = viewModel.currentSettings
                        s.right = val
                        if s.linkAll {
                            s.top = val
                            s.bottom = val
                            s.left = val
                        } else if s.linkHorizontal {
                            s.left = val
                        }
                        viewModel.currentSettings = s
                    }
                ),
                isLinked: Binding(
                    get: { viewModel.currentSettings.linkHorizontal },
                    set: { active in
                        var s = viewModel.currentSettings
                        s.linkHorizontal = active
                        if active {
                            s.right = s.left
                        } else {
                            s.linkAll = false
                        }
                        viewModel.currentSettings = s
                    }
                ),
                tooltip: "Left & Right"
            )
        }
    }

    @ViewBuilder
    private func borderPairView(
        firstLabel: String,
        firstValue: Binding<Int>,
        secondLabel: String,
        secondValue: Binding<Int>,
        isLinked: Binding<Bool>,
        tooltip: String
    ) -> some View {
        HStack(spacing: 6) {
            // Sliders on the left
            VStack(spacing: 6) {
                singleSliderRow(label: firstLabel, valueBinding: firstValue)
                singleSliderRow(label: secondLabel, valueBinding: secondValue)
            }

            // Visual link bracket + button
            HStack(spacing: 3) {
                LinkBracket(isLinked: isLinked.wrappedValue)

                Button {
                    isLinked.wrappedValue.toggle()
                } label: {
                    Image(systemName: isLinked.wrappedValue ? "link" : "link.slash")
                        .font(.system(size: 11, weight: isLinked.wrappedValue ? .semibold : .regular))
                        .foregroundStyle(isLinked.wrappedValue ? Color.white : Color.secondary)
                        .frame(width: 26, height: 44)
                        .background(isLinked.wrappedValue ? Color.accentColor : Color(nsColor: .controlBackgroundColor))
                        .clipShape(RoundedRectangle(cornerRadius: 5))
                        .overlay(
                            RoundedRectangle(cornerRadius: 5)
                                .stroke(isLinked.wrappedValue ? Color.accentColor : Color.primary.opacity(0.12), lineWidth: 1)
                        )
                }
                .buttonStyle(.plain)
                .help(isLinked.wrappedValue ? "\(tooltip) linked (Click to unlink)" : "Click to link \(tooltip)")
            }
        }
    }

    @ViewBuilder
    private func singleSliderRow(label: String, valueBinding: Binding<Int>) -> some View {
        HStack(spacing: 6) {
            Text(label)
                .font(.system(size: 11))
                .foregroundStyle(.secondary)
                .frame(width: 44, alignment: .leading)

            Slider(value: Binding(
                get: { Double(valueBinding.wrappedValue) },
                set: { valueBinding.wrappedValue = Int(round($0)) }
            ), in: 0...500)

            TextField("0", text: Binding(
                get: { String(valueBinding.wrappedValue) },
                set: { if let v = Int($0) { valueBinding.wrappedValue = max(0, min(10000, v)) } }
            ))
            .textFieldStyle(.roundedBorder)
            .frame(width: 48)
            .multilineTextAlignment(.trailing)

            Text("px")
                .font(.system(size: 11))
                .foregroundStyle(.secondary)
                .frame(width: 16, alignment: .leading)
        }
    }
}

private struct LinkBracket: View {
    let isLinked: Bool

    var body: some View {
        GeometryReader { geo in
            Path { path in
                let w = geo.size.width
                let h = geo.size.height
                path.move(to: CGPoint(x: w, y: 3))
                path.addLine(to: CGPoint(x: 1, y: 3))
                path.addLine(to: CGPoint(x: 1, y: h - 3))
                path.addLine(to: CGPoint(x: w, y: h - 3))
            }
            .stroke(isLinked ? Color.accentColor : Color.secondary.opacity(0.35), lineWidth: 1.5)
        }
        .frame(width: 5, height: 44)
    }
}
