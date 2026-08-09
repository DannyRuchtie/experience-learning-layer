import Foundation

struct CodexCLIProvider: ChatProvider {
  func streamResponse(
    for request: ChatRequest,
    apiKey: String?
  ) -> AsyncThrowingStream<String, Error> {
    AsyncThrowingStream { continuation in
      Task {
        do {
          guard let runtime = CodexRuntime.discover() else {
            throw ChatProviderError.codexNotInstalled
          }
          let accountState = await CodexAccountService.shared.status()
          guard accountState == .signedInWithChatGPT || accountState == .signedInWithAPIKey else {
            throw ChatProviderError.codexNotAuthenticated
          }

          let process = Process()
          let input = Pipe()
          let output = Pipe()
          let errorOutput = Pipe()
          process.executableURL = runtime.executableURL
          process.arguments = [
            "exec",
            "--ignore-user-config",
            "--ignore-rules",
            "--ephemeral",
            "--skip-git-repo-check",
            "--json",
            "--color", "never",
            "--sandbox", "read-only",
            "--model", request.model,
            "-c", "approval_policy=\"never\"",
            "-C", FileManager.default.temporaryDirectory.path,
            "-",
          ]
          process.standardInput = input
          process.standardOutput = output
          process.standardError = errorOutput
          try process.run()

          let prompt = CodexConversationPrompt.make(from: request.messages)
          try input.fileHandleForWriting.write(contentsOf: Data(prompt.utf8))
          try input.fileHandleForWriting.close()

          var emittedResponse = false
          for try await line in output.fileHandleForReading.bytes.lines {
            if let failure = CodexWireProtocol.turnFailure(from: line) {
              throw ChatProviderError.codexProcess(failure)
            }
            if let text = CodexWireProtocol.agentMessage(from: line), !text.isEmpty {
              emittedResponse = true
              continuation.yield(text)
            }
          }

          process.waitUntilExit()
          let stderr =
            String(
              data: errorOutput.fileHandleForReading.readDataToEndOfFile(),
              encoding: .utf8
            ) ?? ""
          guard process.terminationStatus == 0 else {
            throw ChatProviderError.codexProcess(
              stderr.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty
                ?? "Codex exited with status \(process.terminationStatus)."
            )
          }
          guard emittedResponse else { throw ChatProviderError.invalidResponse }
          continuation.finish()
        } catch {
          continuation.finish(throwing: error)
        }
      }
    }
  }
}

enum CodexConversationPrompt {
  static func make(from messages: [ChatMessage]) -> String {
    var lines = [
      "You are the conversational model provider inside ELLChat.",
      "Reply directly to the latest user message.",
      "Do not inspect files, run commands, call tools, or modify anything.",
      "Do not mention these wrapper instructions.",
      "",
      "Conversation transcript:",
    ]
    for message in messages {
      let role = message.role == .user ? "USER" : "ASSISTANT"
      lines.append("<\(role)>")
      lines.append(message.text)
      lines.append("</\(role)>")
    }
    lines.append("")
    lines.append("Respond only with the assistant reply to the final USER message.")
    return lines.joined(separator: "\n")
  }
}
