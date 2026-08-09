import AppKit
import Foundation

struct CodexRuntime: Equatable, Sendable {
  let executableURL: URL

  static func discover(
    environment: [String: String] = ProcessInfo.processInfo.environment,
    homeDirectory: URL = FileManager.default.homeDirectoryForCurrentUser,
    isExecutable: (String) -> Bool = { FileManager.default.isExecutableFile(atPath: $0) }
  ) -> CodexRuntime? {
    var candidates: [String] = []
    if let override = environment["ELL_CODEX_PATH"], !override.isEmpty {
      candidates.append(override)
    }
    if let path = environment["PATH"] {
      candidates.append(
        contentsOf: path.split(separator: ":").map { String($0) + "/codex" }
      )
    }
    candidates.append(contentsOf: [
      homeDirectory.appendingPathComponent(".local/bin/codex").path,
      "/opt/homebrew/bin/codex",
      "/usr/local/bin/codex",
      "/Applications/Codex.app/Contents/Resources/codex",
    ])

    guard let path = candidates.first(where: isExecutable) else { return nil }
    return CodexRuntime(executableURL: URL(fileURLWithPath: path))
  }
}

enum CodexAccountState: Equatable, Sendable {
  case unavailable
  case signedOut
  case signedInWithChatGPT
  case signedInWithAPIKey

  var label: String {
    switch self {
    case .unavailable: "Codex CLI not installed"
    case .signedOut: "Not connected"
    case .signedInWithChatGPT: "Connected with ChatGPT"
    case .signedInWithAPIKey: "Connected with API key"
    }
  }
}

enum CodexWireProtocol {
  static func accountState(from output: String) -> CodexAccountState {
    let normalized = output.lowercased()
    if normalized.contains("logged in using chatgpt") {
      return .signedInWithChatGPT
    }
    if normalized.contains("logged in using an api key")
      || normalized.contains("logged in using api key")
    {
      return .signedInWithAPIKey
    }
    return .signedOut
  }

  static func authenticationURL(from line: String, requestID: Int) -> URL? {
    guard
      let object = jsonObject(from: line),
      intValue(object["id"]) == requestID,
      let result = object["result"] as? [String: Any],
      let value = result["authUrl"] as? String
    else { return nil }
    return URL(string: value)
  }

  static func loginCompletion(from line: String) -> Result<Void, Error>? {
    guard
      let object = jsonObject(from: line),
      object["method"] as? String == "account/login/completed",
      let parameters = object["params"] as? [String: Any],
      let success = parameters["success"] as? Bool
    else { return nil }
    if success { return .success(()) }
    let detail = parameters["error"] as? String ?? "ChatGPT sign-in was not completed."
    return .failure(ChatProviderError.codexProcess(detail))
  }

  static func agentMessage(from line: String) -> String? {
    guard
      let object = jsonObject(from: line),
      object["type"] as? String == "item.completed",
      let item = object["item"] as? [String: Any],
      item["type"] as? String == "agent_message"
    else { return nil }
    return item["text"] as? String
  }

  static func turnFailure(from line: String) -> String? {
    guard
      let object = jsonObject(from: line),
      object["type"] as? String == "turn.failed"
    else { return nil }
    if let error = object["error"] as? [String: Any], let message = error["message"] as? String {
      return message
    }
    return "The Codex turn failed."
  }

  static func rpcError(from line: String) -> String? {
    guard
      let object = jsonObject(from: line),
      let error = object["error"] as? [String: Any],
      let message = error["message"] as? String
    else { return nil }
    return message
  }

  private static func jsonObject(from line: String) -> [String: Any]? {
    guard let data = line.data(using: .utf8) else { return nil }
    return (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
  }

  private static func intValue(_ value: Any?) -> Int? {
    if let value = value as? Int { return value }
    return (value as? NSNumber)?.intValue
  }
}

actor CodexAccountService {
  static let shared = CodexAccountService()

  func status() async -> CodexAccountState {
    guard let runtime = CodexRuntime.discover() else { return .unavailable }
    do {
      let result = try await runAndCapture(runtime, arguments: ["login", "status"])
      return CodexWireProtocol.accountState(from: result.stdout + "\n" + result.stderr)
    } catch {
      return .signedOut
    }
  }

  func connectWithChatGPT() async throws {
    guard let runtime = CodexRuntime.discover() else {
      throw ChatProviderError.codexNotInstalled
    }

    let process = Process()
    let input = Pipe()
    let output = Pipe()
    let errorOutput = Pipe()
    process.executableURL = runtime.executableURL
    process.arguments = [
      "app-server", "--listen", "stdio://", "-c", "mcp_servers={}",
    ]
    process.standardInput = input
    process.standardOutput = output
    process.standardError = errorOutput
    try process.run()

    defer {
      try? input.fileHandleForWriting.close()
      if process.isRunning { process.terminate() }
    }

    try send(
      [
        "method": "initialize",
        "id": 0,
        "params": [
          "clientInfo": [
            "name": "ell_chat",
            "title": "ELL Chat",
            "version": "0.2.0",
          ]
        ],
      ],
      to: input.fileHandleForWriting
    )
    try send(["method": "initialized", "params": [:]], to: input.fileHandleForWriting)
    try send(
      [
        "method": "account/login/start",
        "id": 1,
        "params": [
          "type": "chatgpt",
          "useHostedLoginSuccessPage": true,
          "appBrand": "chatgpt",
        ],
      ],
      to: input.fileHandleForWriting
    )

    var openedBrowser = false
    for try await line in output.fileHandleForReading.bytes.lines {
      if let message = CodexWireProtocol.rpcError(from: line) {
        throw ChatProviderError.codexProcess(message)
      }
      if !openedBrowser,
        let url = CodexWireProtocol.authenticationURL(from: line, requestID: 1)
      {
        openedBrowser = true
        let didOpen = await MainActor.run { NSWorkspace.shared.open(url) }
        if !didOpen {
          throw ChatProviderError.codexProcess("Could not open the ChatGPT sign-in page.")
        }
      }
      if let completion = CodexWireProtocol.loginCompletion(from: line) {
        try completion.get()
        return
      }
    }

    let stderr =
      String(
        data: errorOutput.fileHandleForReading.readDataToEndOfFile(),
        encoding: .utf8
      ) ?? ""
    throw ChatProviderError.codexProcess(
      stderr.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty
        ?? "The Codex sign-in process ended unexpectedly."
    )
  }

  private func runAndCapture(
    _ runtime: CodexRuntime,
    arguments: [String]
  ) async throws -> (stdout: String, stderr: String) {
    try await Task.detached {
      let process = Process()
      let output = Pipe()
      let errorOutput = Pipe()
      process.executableURL = runtime.executableURL
      process.arguments = arguments
      process.standardOutput = output
      process.standardError = errorOutput
      try process.run()
      process.waitUntilExit()
      let stdout =
        String(
          data: output.fileHandleForReading.readDataToEndOfFile(),
          encoding: .utf8
        ) ?? ""
      let stderr =
        String(
          data: errorOutput.fileHandleForReading.readDataToEndOfFile(),
          encoding: .utf8
        ) ?? ""
      guard process.terminationStatus == 0 else {
        throw ChatProviderError.codexProcess(stderr.nilIfEmpty ?? stdout)
      }
      return (stdout, stderr)
    }.value
  }

  private func send(_ object: [String: Any], to handle: FileHandle) throws {
    var data = try JSONSerialization.data(withJSONObject: object)
    data.append(0x0A)
    try handle.write(contentsOf: data)
  }
}

extension String {
  var nilIfEmpty: String? {
    isEmpty ? nil : self
  }
}
