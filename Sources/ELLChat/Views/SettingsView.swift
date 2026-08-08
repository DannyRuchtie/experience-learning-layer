import SwiftUI

struct SettingsView: View {
  @State private var apiKey = ""
  @State private var status = ""

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

      Section("Future providers") {
        LabeledContent("Codex", value: "Reserved agent adapter")
        LabeledContent("Anthropic", value: "Reserved chat adapter")
      }
    }
    .formStyle(.grouped)
    .frame(width: 480, height: 280)
    .task { loadStatus() }
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
}
