// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "PhotonApp",
    platforms: [
        .macOS(.v15)
    ],
    products: [
        .executable(
            name: "Photon",
            targets: ["PhotonApp"]
        )
    ],
    targets: [
        .executableTarget(
            name: "PhotonApp",
            path: "Sources/PhotonApp",
            swiftSettings: [
                .swiftLanguageMode(.v6)
            ]
        )
    ]
)
