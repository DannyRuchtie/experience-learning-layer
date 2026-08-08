import Foundation

actor LocalExperienceStore {
  let workspaceID: UUID
  let rootURL: URL

  private let fileManager: FileManager
  private var loadedFiles: Set<URL> = []
  private var identifiersByFile: [URL: Set<UUID>] = [:]

  init(
    workspaceID: UUID,
    rootURL: URL? = nil,
    fileManager: FileManager = .default
  ) {
    self.workspaceID = workspaceID
    self.fileManager = fileManager
    if let rootURL {
      self.rootURL = rootURL
    } else {
      let applicationSupport = fileManager.urls(
        for: .applicationSupportDirectory,
        in: .userDomainMask
      ).first!
      self.rootURL = applicationSupport.appendingPathComponent(
        "ExperienceLearningLayer/Chat",
        isDirectory: true
      )
    }
  }

  func loadSessions() throws -> [ChatSession] {
    try ensureDirectory()
    let url = rootURL.appendingPathComponent("chat_state.json")
    guard fileManager.fileExists(atPath: url.path) else { return [] }
    return try Self.decoder().decode([ChatSession].self, from: Data(contentsOf: url))
  }

  func saveSessions(_ sessions: [ChatSession]) throws {
    try ensureDirectory()
    let data = try Self.encoder(pretty: true).encode(sessions)
    try data.write(
      to: rootURL.appendingPathComponent("chat_state.json"),
      options: .atomic
    )
  }

  func capture(
    message: ChatMessage,
    sessionID: UUID,
    parentEventID: UUID? = nil,
    phase: String = "final"
  ) throws -> CapturedMessage {
    try ensureDirectory()
    let sourceID = StableIdentifiers.sourceID(messageID: message.id)
    let span = CapturedSourceSpan(
      id: StableIdentifiers.spanID(sourceID: sourceID),
      text: message.text,
      start: 0,
      end: message.text.unicodeScalars.count
    )
    let source = CapturedSourceArtifact(
      id: sourceID,
      schemaVersion: 1,
      workspaceID: workspaceID,
      kind: "conversation",
      connector: "ell_chat",
      externalRef: message.id.uuidString.lowercased(),
      contentHash: StableIdentifiers.sha256(message.text),
      normalizedText: message.text,
      spans: [span],
      authors: [],
      observedAt: message.createdAt,
      capturedAt: Date(),
      sensitivity: "private",
      metadata: ["provider": message.provider.rawValue, "model": message.model]
    )
    let event = CapturedExperienceEvent(
      id: StableIdentifiers.eventID(sourceID: sourceID, messageID: message.id),
      schemaVersion: 1,
      workspaceID: workspaceID,
      sourceID: sourceID,
      sourceEventID: message.id.uuidString.lowercased(),
      sessionID: sessionID.uuidString.lowercased(),
      parentID: parentEventID,
      eventType: message.role == .user ? "user_message" : "assistant_message",
      actorID: message.role == .user
        ? "local-user"
        : "provider:\(message.provider.rawValue)",
      occurredAt: message.createdAt,
      payload: CapturedEventPayload(
        text: message.text,
        provider: message.provider.rawValue,
        model: message.model,
        phase: phase
      ),
      sensitivity: "private"
    )

    try appendOnce(
      source,
      id: source.id,
      to: rootURL.appendingPathComponent("sources.jsonl")
    )
    try appendOnce(
      event,
      id: event.id,
      to: rootURL.appendingPathComponent("events.jsonl")
    )
    return CapturedMessage(source: source, event: event)
  }

  func closeEpisode(
    user: CapturedMessage,
    assistant: CapturedMessage,
    sessionID: UUID
  ) throws -> CapturedEpisode {
    try ensureDirectory()
    let eventIDs = [user.event.id, assistant.event.id]
    let episode = CapturedEpisode(
      id: StableIdentifiers.episodeID(workspaceID: workspaceID, eventIDs: eventIDs),
      schemaVersion: 1,
      workspaceID: workspaceID,
      eventIDs: eventIDs,
      timestampStart: user.event.occurredAt,
      timestampEnd: assistant.event.occurredAt,
      actorID: "local-user",
      participantIDs: [],
      input: user.event.payload.text,
      response: assistant.event.payload.text,
      actions: [],
      observations: [],
      outcomes: [],
      entityIDs: [],
      metadata: [
        "session_id": sessionID.uuidString.lowercased(),
        "boundary": "completed_turn",
      ],
      createdAt: Date()
    )
    try appendOnce(
      episode,
      id: episode.id,
      to: rootURL.appendingPathComponent("episodes.jsonl")
    )
    return episode
  }

  private func ensureDirectory() throws {
    try fileManager.createDirectory(at: rootURL, withIntermediateDirectories: true)
  }

  private func appendOnce<T: Encodable>(_ record: T, id: UUID, to url: URL) throws {
    try loadIdentifiersIfNeeded(from: url)
    if identifiersByFile[url, default: []].contains(id) { return }

    var line = try Self.encoder().encode(record)
    line.append(0x0A)
    if !fileManager.fileExists(atPath: url.path) {
      guard fileManager.createFile(atPath: url.path, contents: nil) else {
        throw CocoaError(.fileWriteUnknown)
      }
    }
    let handle = try FileHandle(forWritingTo: url)
    defer { try? handle.close() }
    try handle.seekToEnd()
    try handle.write(contentsOf: line)
    identifiersByFile[url, default: []].insert(id)
  }

  private func loadIdentifiersIfNeeded(from url: URL) throws {
    guard !loadedFiles.contains(url) else { return }
    loadedFiles.insert(url)
    guard fileManager.fileExists(atPath: url.path) else {
      identifiersByFile[url] = []
      return
    }

    let data = try Data(contentsOf: url)
    let identifiers = data.split(separator: 0x0A).compactMap { line -> UUID? in
      guard
        let object = try? JSONSerialization.jsonObject(with: Data(line)),
        let dictionary = object as? [String: Any],
        let value = dictionary["id"] as? String
      else { return nil }
      return UUID(uuidString: value)
    }
    identifiersByFile[url] = Set(identifiers)
  }

  private static func encoder(pretty: Bool = false) -> JSONEncoder {
    let encoder = JSONEncoder()
    encoder.keyEncodingStrategy = .convertToSnakeCase
    encoder.dateEncodingStrategy = .iso8601
    encoder.outputFormatting = pretty ? [.prettyPrinted, .sortedKeys] : [.sortedKeys]
    return encoder
  }

  private static func decoder() -> JSONDecoder {
    let decoder = JSONDecoder()
    decoder.keyDecodingStrategy = .convertFromSnakeCase
    decoder.dateDecodingStrategy = .iso8601
    return decoder
  }
}
