import Foundation

protocol ChatProvider: Sendable {
  func streamResponse(
    for request: ChatRequest,
    apiKey: String?
  ) -> AsyncThrowingStream<String, Error>
}

enum ChatProviderError: LocalizedError {
  case missingAPIKey
  case invalidResponse
  case httpStatus(Int, String)
  case providerMessage(String)
  case unavailable(String)

  var errorDescription: String? {
    switch self {
    case .missingAPIKey:
      "Add an OpenAI API key in Settings before using OpenAI."
    case .invalidResponse:
      "The provider returned an unreadable response."
    case .httpStatus(let status, let detail):
      "Provider request failed (HTTP \(status)): \(detail)"
    case .providerMessage(let message):
      message
    case .unavailable(let provider):
      "\(provider) is reserved by the provider port but is not enabled yet."
    }
  }
}

enum ChatProviderFactory {
  static func make(_ kind: ProviderKind) -> any ChatProvider {
    switch kind {
    case .mock:
      MockChatProvider()
    case .openAI:
      OpenAIResponsesProvider()
    case .codex, .anthropic:
      UnavailableChatProvider(name: kind.title)
    }
  }
}

private struct UnavailableChatProvider: ChatProvider {
  let name: String

  func streamResponse(
    for request: ChatRequest,
    apiKey: String?
  ) -> AsyncThrowingStream<String, Error> {
    AsyncThrowingStream { continuation in
      continuation.finish(throwing: ChatProviderError.unavailable(name))
    }
  }
}
