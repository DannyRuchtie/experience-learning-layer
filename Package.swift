// swift-tools-version: 6.2

import PackageDescription

let package = Package(
  name: "ExperienceLearningLayer",
  platforms: [.macOS(.v14)],
  products: [
    .executable(name: "ELLChat", targets: ["ELLChat"])
  ],
  targets: [
    .executableTarget(
      name: "ELLChat",
      path: "Sources/ELLChat"
    ),
    .testTarget(
      name: "ELLChatTests",
      dependencies: ["ELLChat"],
      path: "Tests/ELLChatTests"
    ),
  ]
)
