// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "PriveRandomizer",
    platforms: [
        .macOS(.v12)
    ],
    products: [
        .executable(name: "PriveRandomizer", targets: ["PriveRandomizer"])
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "PriveRandomizer",
            dependencies: [],
            path: "Sources/PriveRandomizer"
        )
    ]
)
