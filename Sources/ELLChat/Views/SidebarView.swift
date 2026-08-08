import SwiftUI

struct SidebarView: View {
  let store: ChatStore

  var body: some View {
    List(selection: selection) {
      Section("Episodes") {
        ForEach(store.sessions) { session in
          HStack(spacing: 10) {
            Image(systemName: "bubble.left")
              .foregroundStyle(.secondary)
              .frame(width: 16)
            VStack(alignment: .leading, spacing: 2) {
              Text(session.title)
                .lineLimit(1)
              Text(session.provider.title)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(1)
            }
          }
          .tag(session.id)
        }
      }
    }
    .listStyle(.sidebar)
    .navigationTitle("ELL Chat")
    .toolbar {
      ToolbarItem {
        Button(action: store.newSession) {
          Label("New Episode", systemImage: "square.and.pencil")
        }
        .help("New Episode (⌘N)")
      }
    }
  }

  private var selection: Binding<UUID?> {
    Binding(get: { store.selectionID }, set: { store.selectionID = $0 })
  }
}
