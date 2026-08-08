import Foundation
import XCTest

@testable import ELLChat

final class ELLChatTests: XCTestCase {
  func testStableIdentifiersAreDeterministicAndOrderSensitive() {
    let messageID = UUID(uuidString: "86c7cb0b-15ae-4242-9db4-68de543dbb86")!
    let workspaceID = UUID(uuidString: "5bf98df1-2c1d-4f41-a669-dd03a87d662e")!
    let sourceA = StableIdentifiers.sourceID(messageID: messageID)
    let sourceB = StableIdentifiers.sourceID(messageID: messageID)
    let eventA = StableIdentifiers.eventID(sourceID: sourceA, messageID: messageID)
    let eventB = UUID(uuidString: "5b818098-b2f1-465c-b0f6-997d0c74d253")!

    XCTAssertEqual(sourceA, sourceB)
    XCTAssertEqual(eventA, StableIdentifiers.eventID(sourceID: sourceB, messageID: messageID))
    XCTAssertNotEqual(
      StableIdentifiers.episodeID(workspaceID: workspaceID, eventIDs: [eventA, eventB]),
      StableIdentifiers.episodeID(workspaceID: workspaceID, eventIDs: [eventB, eventA])
    )
  }

  func testCaptureWritesSourcesEventsAndOneIdempotentEpisode() async throws {
    let root = FileManager.default.temporaryDirectory
      .appendingPathComponent(UUID().uuidString, isDirectory: true)
    defer { try? FileManager.default.removeItem(at: root) }
    let workspaceID = UUID()
    let sessionID = UUID()
    let store = LocalExperienceStore(workspaceID: workspaceID, rootURL: root)
    let user = ChatMessage(
      role: .user,
      text: "Capture this exact message.",
      provider: .mock,
      model: "fixture-v1"
    )
    let assistant = ChatMessage(
      role: .assistant,
      text: "Captured.",
      provider: .mock,
      model: "fixture-v1"
    )

    let capturedUser = try await store.capture(message: user, sessionID: sessionID)
    let capturedAssistant = try await store.capture(
      message: assistant,
      sessionID: sessionID,
      parentEventID: capturedUser.event.id
    )
    let first = try await store.closeEpisode(
      user: capturedUser,
      assistant: capturedAssistant,
      sessionID: sessionID
    )
    let second = try await store.closeEpisode(
      user: capturedUser,
      assistant: capturedAssistant,
      sessionID: sessionID
    )

    XCTAssertEqual(first.id, second.id)
    XCTAssertEqual(try lineCount(root.appendingPathComponent("sources.jsonl")), 2)
    XCTAssertEqual(try lineCount(root.appendingPathComponent("events.jsonl")), 2)
    XCTAssertEqual(try lineCount(root.appendingPathComponent("episodes.jsonl")), 1)
  }

  func testMockProviderStreamsACompleteResponse() async throws {
    let request = ChatRequest(
      sessionID: UUID(),
      model: "fixture-v1",
      messages: [
        ChatMessage(
          role: .user,
          text: "An episode",
          provider: .mock,
          model: "fixture-v1"
        )
      ]
    )
    var response = ""
    for try await delta in MockChatProvider().streamResponse(for: request, apiKey: nil) {
      response += delta
    }
    XCTAssertTrue(response.contains("Captured locally first"))
    XCTAssertTrue(response.contains("An episode"))
  }

  private func lineCount(_ url: URL) throws -> Int {
    try Data(contentsOf: url).split(separator: 0x0A).count
  }
}
