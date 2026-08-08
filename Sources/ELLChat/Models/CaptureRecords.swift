import Foundation

struct CapturedSourceSpan: Codable, Equatable, Sendable {
  let id: UUID
  let text: String
  let start: Int
  let end: Int
}

struct CapturedSourceArtifact: Codable, Equatable, Sendable {
  let id: UUID
  let schemaVersion: Int
  let workspaceID: UUID
  let kind: String
  let connector: String
  let externalRef: String
  let contentHash: String
  let normalizedText: String
  let spans: [CapturedSourceSpan]
  let authors: [UUID]
  let observedAt: Date
  let capturedAt: Date
  let sensitivity: String
  let metadata: [String: String]
}

struct CapturedEventPayload: Codable, Equatable, Sendable {
  let text: String
  let provider: String
  let model: String
  let phase: String
}

struct CapturedExperienceEvent: Codable, Equatable, Sendable {
  let id: UUID
  let schemaVersion: Int
  let workspaceID: UUID
  let sourceID: UUID
  let sourceEventID: String
  let sessionID: String
  let parentID: UUID?
  let eventType: String
  let actorID: String
  let occurredAt: Date
  let payload: CapturedEventPayload
  let sensitivity: String
}

struct CapturedEpisode: Codable, Equatable, Sendable {
  let id: UUID
  let schemaVersion: Int
  let workspaceID: UUID
  let eventIDs: [UUID]
  let timestampStart: Date
  let timestampEnd: Date
  let actorID: String
  let participantIDs: [UUID]
  let input: String?
  let response: String?
  let actions: [String]
  let observations: [String]
  let outcomes: [String]
  let entityIDs: [UUID]
  let metadata: [String: String]
  let createdAt: Date
}

struct CapturedMessage: Sendable {
  let source: CapturedSourceArtifact
  let event: CapturedExperienceEvent
}
