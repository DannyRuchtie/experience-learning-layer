import Foundation
import Observation

@MainActor
@Observable
final class ChatStore {
  private(set) var sessions: [ChatSession] = []
  var selectionID: UUID?
  var draft = ""
  private(set) var isSending = false
  var errorMessage: String?

  let experienceStore: LocalExperienceStore

  init(experienceStore: LocalExperienceStore? = nil) {
    self.experienceStore =
      experienceStore
      ?? LocalExperienceStore(
        workspaceID: AppIdentity.workspaceID()
      )
    Task { await load() }
  }

  var selectedSession: ChatSession? {
    guard let selectionID else { return nil }
    return sessions.first(where: { $0.id == selectionID })
  }

  func newSession() {
    let session = ChatSession()
    sessions.insert(session, at: 0)
    selectionID = session.id
    persistProjection()
  }

  func updateProvider(_ provider: ProviderKind) {
    guard provider.isAvailable, let index = selectedIndex else { return }
    sessions[index].provider = provider
    sessions[index].updatedAt = Date()
    persistProjection()
  }

  func updateModel(_ model: String) {
    guard let index = selectedIndex else { return }
    sessions[index].model = model
    sessions[index].updatedAt = Date()
    persistProjection()
  }

  func sendDraft() {
    let text = draft.trimmingCharacters(in: .whitespacesAndNewlines)
    guard !text.isEmpty, !isSending, let index = selectedIndex else { return }
    draft = ""
    errorMessage = nil

    let sessionID = sessions[index].id
    let providerKind = sessions[index].provider
    let model = sessions[index].model
    let userMessage = ChatMessage(
      role: .user,
      text: text,
      provider: providerKind,
      model: model
    )
    sessions[index].messages.append(userMessage)
    sessions[index].updatedAt = userMessage.createdAt
    if sessions[index].messages.count == 1 {
      sessions[index].title = String(text.prefix(54))
    }
    let requestMessages = sessions[index].messages
    persistProjection()
    isSending = true

    Task {
      do {
        let capturedUser = try await experienceStore.capture(
          message: userMessage,
          sessionID: sessionID
        )
        let apiKey = providerKind == .openAI ? try KeychainStore.readOpenAIKey() : nil
        let provider = ChatProviderFactory.make(providerKind)
        let assistantID = UUID()
        let assistantCreatedAt = Date()
        var assistantText = ""
        appendAssistantPlaceholder(
          id: assistantID,
          createdAt: assistantCreatedAt,
          provider: providerKind,
          model: model,
          sessionID: sessionID
        )

        let request = ChatRequest(
          sessionID: sessionID,
          model: model,
          messages: requestMessages
        )
        for try await delta in provider.streamResponse(for: request, apiKey: apiKey) {
          assistantText += delta
          updateAssistant(id: assistantID, text: assistantText, sessionID: sessionID)
        }
        let finalText = assistantText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !finalText.isEmpty else { throw ChatProviderError.invalidResponse }

        let assistant = ChatMessage(
          id: assistantID,
          role: .assistant,
          text: finalText,
          createdAt: assistantCreatedAt,
          provider: providerKind,
          model: model
        )
        updateAssistant(id: assistantID, text: finalText, sessionID: sessionID)
        let capturedAssistant = try await experienceStore.capture(
          message: assistant,
          sessionID: sessionID,
          parentEventID: capturedUser.event.id
        )
        _ = try await experienceStore.closeEpisode(
          user: capturedUser,
          assistant: capturedAssistant,
          sessionID: sessionID
        )
        persistProjection()
      } catch {
        removeEmptyAssistant(in: sessionID)
        errorMessage = error.localizedDescription
      }
      isSending = false
    }
  }

  private var selectedIndex: Int? {
    guard let selectionID else { return nil }
    return sessions.firstIndex(where: { $0.id == selectionID })
  }

  private func load() async {
    do {
      sessions = try await experienceStore.loadSessions()
    } catch {
      errorMessage = "Could not load local chat history: \(error.localizedDescription)"
    }
    if sessions.isEmpty {
      newSession()
    } else if selectionID == nil {
      selectionID = sessions[0].id
    }
  }

  private func appendAssistantPlaceholder(
    id: UUID,
    createdAt: Date,
    provider: ProviderKind,
    model: String,
    sessionID: UUID
  ) {
    guard let index = sessions.firstIndex(where: { $0.id == sessionID }) else { return }
    sessions[index].messages.append(
      ChatMessage(
        id: id,
        role: .assistant,
        text: "",
        createdAt: createdAt,
        provider: provider,
        model: model
      )
    )
  }

  private func updateAssistant(id: UUID, text: String, sessionID: UUID) {
    guard
      let sessionIndex = sessions.firstIndex(where: { $0.id == sessionID }),
      let messageIndex = sessions[sessionIndex].messages.firstIndex(where: { $0.id == id })
    else { return }
    sessions[sessionIndex].messages[messageIndex].text = text
    sessions[sessionIndex].updatedAt = Date()
  }

  private func removeEmptyAssistant(in sessionID: UUID) {
    guard let index = sessions.firstIndex(where: { $0.id == sessionID }) else { return }
    sessions[index].messages.removeAll { $0.role == .assistant && $0.text.isEmpty }
  }

  private func persistProjection() {
    let snapshot = sessions
    Task {
      do {
        try await experienceStore.saveSessions(snapshot)
      } catch {
        errorMessage = "Could not save local chat history: \(error.localizedDescription)"
      }
    }
  }
}
