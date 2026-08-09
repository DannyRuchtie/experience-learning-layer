import Foundation

enum ProviderKind: String, Codable, CaseIterable, Identifiable, Sendable {
  case mock
  case openAI = "openai"
  case codex
  case anthropic

  var id: String { rawValue }

  var title: String {
    switch self {
    case .mock: "Local Preview"
    case .openAI: "OpenAI"
    case .codex: "Codex"
    case .anthropic: "Anthropic"
    }
  }

  var isAvailable: Bool {
    self == .mock || self == .openAI || self == .codex
  }
}

enum ChatRole: String, Codable, Sendable {
  case user
  case assistant
}

struct ChatMessage: Identifiable, Codable, Equatable, Sendable {
  let id: UUID
  let role: ChatRole
  var text: String
  let createdAt: Date
  let provider: ProviderKind
  let model: String

  init(
    id: UUID = UUID(),
    role: ChatRole,
    text: String,
    createdAt: Date = Date(),
    provider: ProviderKind,
    model: String
  ) {
    self.id = id
    self.role = role
    self.text = text
    self.createdAt = createdAt
    self.provider = provider
    self.model = model
  }
}

struct ChatSession: Identifiable, Codable, Equatable, Sendable {
  let id: UUID
  var title: String
  var provider: ProviderKind
  var model: String
  var messages: [ChatMessage]
  let createdAt: Date
  var updatedAt: Date

  init(
    id: UUID = UUID(),
    title: String = "New episode",
    provider: ProviderKind = .mock,
    model: String = "gpt-5.6-terra",
    messages: [ChatMessage] = [],
    createdAt: Date = Date(),
    updatedAt: Date = Date()
  ) {
    self.id = id
    self.title = title
    self.provider = provider
    self.model = model
    self.messages = messages
    self.createdAt = createdAt
    self.updatedAt = updatedAt
  }
}

struct ChatRequest: Sendable {
  let sessionID: UUID
  let model: String
  let messages: [ChatMessage]
}
