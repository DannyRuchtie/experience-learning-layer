import SwiftUI

struct SettingsView: View {
  @State private var apiKey = ""
  @State private var status = ""
  @State private var codexStatus = "Checking…"
  @State private var isConnectingCodex = false

  var body: some View {
    Form {
      Section("OpenAI") {
        SecureField("API key", text: $apiKey)
        Text("Stored in your macOS Keychain. It is never written to episode files.")
          .font(.caption)
          .foregroundStyle(.secondary)
        HStack {
          Button("Save") { save() }
            .disabled(apiKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
          Button("Remove", role: .destructive) { remove() }
          if !status.isEmpty {
            Text(status)
              .font(.caption)
              .foregroundStyle(.secondary)
          }
        }
      }

      Section("Codex with ChatGPT") {
        LabeledContent("Account", value: codexStatus)
        Text("Codex owns the ChatGPT credential. ELLChat never reads or stores its tokens.")
          .font(.caption)
          .foregroundStyle(.secondary)
        HStack {
          Button("Connect ChatGPT") { connectCodex() }
            .disabled(
              isConnectingCodex || codexStatus == CodexAccountState.unavailable.label
                || codexStatus == CodexAccountState.signedInWithChatGPT.label)
          Button("Check Again") { refreshCodexStatus() }
            .disabled(isConnectingCodex)
          if isConnectingCodex {
            ProgressView()
              .controlSize(.small)
          }
        }
      }

      Section("Future providers") {
        LabeledContent("Anthropic", value: "Reserved chat adapter")
      }
    }
    .formStyle(.grouped)
    .frame(width: 500, height: 430)
    .task {
      loadStatus()
      await updateCodexStatus()
    }
  }

  private func loadStatus() {
    do {
      status = try KeychainStore.readOpenAIKey() == nil ? "Not configured" : "Configured"
    } catch {
      status = error.localizedDescription
    }
  }

  private func save() {
    do {
      try KeychainStore.saveOpenAIKey(apiKey.trimmingCharacters(in: .whitespacesAndNewlines))
      apiKey = ""
      status = "Saved"
    } catch {
      status = error.localizedDescription
    }
  }

  private func remove() {
    do {
      try KeychainStore.deleteOpenAIKey()
      apiKey = ""
      status = "Removed"
    } catch {
      status = error.localizedDescription
    }
  }

  private func refreshCodexStatus() {
    Task { await updateCodexStatus() }
  }

  private func updateCodexStatus() async {
    codexStatus = (await CodexAccountService.shared.status()).label
  }

  private func connectCodex() {
    isConnectingCodex = true
    codexStatus = "Waiting for browser sign-in…"
    Task {
      do {
        try await CodexAccountService.shared.connectWithChatGPT()
        await updateCodexStatus()
      } catch {
        codexStatus = error.localizedDescription
      }
      isConnectingCodex = false
    }
  }
}
