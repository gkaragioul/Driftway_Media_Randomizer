// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "DriftwayMediaRandomizer",
    platforms: [
        .macOS(.v12)
    ],
    products: [
        .executable(name: "DriftwayMediaRandomizer", targets: ["DriftwayMediaRandomizer"])
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "DriftwayMediaRandomizer",
            dependencies: [],
            path: "Sources/DriftwayMediaRandomizer"
        )
    ]
)
