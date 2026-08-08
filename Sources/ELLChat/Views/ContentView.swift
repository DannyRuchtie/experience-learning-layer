import SwiftUI

struct ContentView: View {
  let store: ChatStore

  var body: some View {
    NavigationSplitView {
      SidebarView(store: store)
        .navigationSplitViewColumnWidth(min: 220, ideal: 260, max: 340)
    } detail: {
      if let session = store.selectedSession {
        ConversationView(store: store, session: session)
      } else {
        ContentUnavailableView(
          "Select an episode",
          systemImage: "bubble.left.and.bubble.right"
        )
      }
    }
    .alert(
      "Chat could not continue",
      isPresented: Binding(
        get: { store.errorMessage != nil },
        set: { if !$0 { store.errorMessage = nil } }
      )
    ) {
      Button("OK", role: .cancel) { store.errorMessage = nil }
    } message: {
      Text(store.errorMessage ?? "Unknown error")
    }
  }
}
