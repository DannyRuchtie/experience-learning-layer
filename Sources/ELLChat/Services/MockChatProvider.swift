import Foundation

struct MockChatProvider: ChatProvider {
  func streamResponse(
    for request: ChatRequest,
    apiKey: String?
  ) -> AsyncThrowingStream<String, Error> {
    let latest = request.messages.last(where: { $0.role == .user })?.text ?? "this episode"
    let response = "Captured locally first. In provider mode, I would respond to: “\(latest)”"
    let chunks = response.split(separator: " ").map { String($0) + " " }

    return AsyncThrowingStream { continuation in
      Task {
        do {
          for chunk in chunks {
            try await Task.sleep(for: .milliseconds(18))
            continuation.yield(chunk)
          }
          continuation.finish()
        } catch {
          continuation.finish(throwing: error)
        }
      }
    }
  }
}
