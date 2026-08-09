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

  func testCodexRuntimeDiscoveryPrefersExplicitOverride() {
    let runtime = CodexRuntime.discover(
      environment: [
        "ELL_CODEX_PATH": "/fixture/codex",
        "PATH": "/other/bin",
      ],
      homeDirectory: URL(fileURLWithPath: "/home/fixture"),
      isExecutable: { $0 == "/fixture/codex" }
    )

    XCTAssertEqual(runtime?.executableURL.path, "/fixture/codex")
  }

  func testCodexWireProtocolParsesAccountAndStreamingEvents() throws {
    XCTAssertEqual(
      CodexWireProtocol.accountState(from: "Logged in using ChatGPT"),
      .signedInWithChatGPT
    )
    XCTAssertEqual(
      CodexWireProtocol.agentMessage(
        from: #"{"type":"item.completed","item":{"type":"agent_message","text":"Ready."}}"#
      ),
      "Ready."
    )
    XCTAssertNil(
      CodexWireProtocol.agentMessage(from: #"{"type":"turn.started"}"#)
    )

    let authURL = try XCTUnwrap(
      CodexWireProtocol.authenticationURL(
        from: #"{"id":1,"result":{"type":"chatgpt","authUrl":"https://chatgpt.com/auth"}}"#,
        requestID: 1
      )
    )
    XCTAssertEqual(authURL.host(), "chatgpt.com")
  }

  func testCodexConversationPromptPreservesOrderedRoles() {
    let messages = [
      ChatMessage(
        role: .user,
        text: "First",
        provider: .codex,
        model: "fixture"
      ),
      ChatMessage(
        role: .assistant,
        text: "Second",
        provider: .codex,
        model: "fixture"
      ),
      ChatMessage(
        role: .user,
        text: "Third",
        provider: .codex,
        model: "fixture"
      ),
    ]

    let prompt = CodexConversationPrompt.make(from: messages)
    let first = prompt.range(of: "<USER>\nFirst\n</USER>")
    let second = prompt.range(of: "<ASSISTANT>\nSecond\n</ASSISTANT>")
    let third = prompt.range(of: "<USER>\nThird\n</USER>")
    XCTAssertNotNil(first)
    XCTAssertNotNil(second)
    XCTAssertNotNil(third)
    XCTAssertLessThan(first!.lowerBound, second!.lowerBound)
    XCTAssertLessThan(second!.lowerBound, third!.lowerBound)
    XCTAssertTrue(prompt.contains("Do not inspect files, run commands, call tools"))
  }

  func testLiveCodexProviderWhenExplicitlyEnabled() async throws {
    guard ProcessInfo.processInfo.environment["ELL_LIVE_CODEX_TEST"] == "1" else {
      throw XCTSkip("Set ELL_LIVE_CODEX_TEST=1 to consume a real authenticated Codex turn.")
    }
    let request = ChatRequest(
      sessionID: UUID(),
      model: "gpt-5.6-terra",
      messages: [
        ChatMessage(
          role: .user,
          text: "Reply with exactly: ELL Codex provider connected.",
          provider: .codex,
          model: "gpt-5.6-terra"
        )
      ]
    )
    var response = ""
    for try await chunk in CodexCLIProvider().streamResponse(for: request, apiKey: nil) {
      response += chunk
    }
    XCTAssertEqual(
      response.trimmingCharacters(in: .whitespacesAndNewlines),
      "ELL Codex provider connected."
    )
  }

  private func lineCount(_ url: URL) throws -> Int {
    try Data(contentsOf: url).split(separator: 0x0A).count
  }
}
