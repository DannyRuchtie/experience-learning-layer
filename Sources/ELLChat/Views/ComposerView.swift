import SwiftUI

struct ComposerView: View {
  let store: ChatStore

  var body: some View {
    HStack(alignment: .bottom, spacing: 12) {
      TextField("Describe what happened…", text: draft, axis: .vertical)
        .textFieldStyle(.plain)
        .lineLimit(1...8)
        .padding(10)
        .background(.quaternary.opacity(0.35), in: RoundedRectangle(cornerRadius: 10))
        .onSubmit(store.sendDraft)

      Button(action: store.sendDraft) {
        Image(systemName: "arrow.up.circle.fill")
          .font(.title2)
      }
      .buttonStyle(.plain)
      .disabled(
        store.draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || store.isSending
      )
      .keyboardShortcut(.return, modifiers: .command)
      .help("Send (⌘↩)")
    }
    .padding(16)
    .background(.bar)
  }

  private var draft: Binding<String> {
    Binding(get: { store.draft }, set: { store.draft = $0 })
  }
}
