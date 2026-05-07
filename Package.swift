// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "GKMediaRandomizer",
    platforms: [
        .macOS(.v12)
    ],
    products: [
        .executable(name: "GKMediaRandomizer", targets: ["GKMediaRandomizer"])
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "GKMediaRandomizer",
            dependencies: [],
            path: "Sources/GKMediaRandomizer"
        )
    ]
)
