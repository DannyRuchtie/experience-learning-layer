import Foundation

struct OpenAIResponsesProvider: ChatProvider {
  private let endpoint = URL(string: "https://api.openai.com/v1/responses")!

  func streamResponse(
    for request: ChatRequest,
    apiKey: String?
  ) -> AsyncThrowingStream<String, Error> {
    AsyncThrowingStream { continuation in
      Task {
        do {
          guard let apiKey, !apiKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
          else {
            throw ChatProviderError.missingAPIKey
          }

          var urlRequest = URLRequest(url: endpoint)
          urlRequest.httpMethod = "POST"
          urlRequest.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
          urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
          urlRequest.httpBody = try JSONEncoder().encode(
            RequestBody(
              model: request.model,
              input: request.messages.map {
                InputMessage(role: $0.role.rawValue, content: $0.text)
              },
              stream: true,
              store: false
            )
          )

          let (bytes, response) = try await URLSession.shared.bytes(for: urlRequest)
          guard let http = response as? HTTPURLResponse else {
            throw ChatProviderError.invalidResponse
          }
          guard (200..<300).contains(http.statusCode) else {
            var body = ""
            for try await line in bytes.lines {
              body += line
            }
            throw ChatProviderError.httpStatus(http.statusCode, body)
          }

          for try await line in bytes.lines where line.hasPrefix("data: ") {
            let value = String(line.dropFirst(6))
            guard value != "[DONE]", let data = value.data(using: .utf8) else {
              continue
            }
            let event = try JSONDecoder().decode(StreamEvent.self, from: data)
            if event.type == "response.output_text.delta", let delta = event.delta {
              continuation.yield(delta)
            } else if event.type == "error" {
              throw ChatProviderError.providerMessage(
                event.error?.message ?? "OpenAI streaming request failed."
              )
            }
          }
          continuation.finish()
        } catch {
          continuation.finish(throwing: error)
        }
      }
    }
  }
}

extension OpenAIResponsesProvider {
  fileprivate struct RequestBody: Encodable {
    let model: String
    let input: [InputMessage]
    let stream: Bool
    let store: Bool
  }

  fileprivate struct InputMessage: Encodable {
    let role: String
    let content: String
  }

  fileprivate struct StreamEvent: Decodable {
    let type: String
    let delta: String?
    let error: ProviderError?
  }

  fileprivate struct ProviderError: Decodable {
    let message: String
  }
}
