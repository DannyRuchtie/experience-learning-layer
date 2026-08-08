import SwiftUI

struct ConversationView: View {
  let store: ChatStore
  let session: ChatSession

  var body: some View {
    VStack(spacing: 0) {
      ScrollViewReader { proxy in
        ScrollView {
          LazyVStack(spacing: 16) {
            if session.messages.isEmpty {
              EmptyConversationView()
            }
            ForEach(session.messages) { message in
              MessageRow(message: message)
                .id(message.id)
            }
          }
          .padding(24)
          .frame(maxWidth: 820)
          .frame(maxWidth: .infinity)
        }
        .onChange(of: session.messages.count) {
          if let last = session.messages.last {
            withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
          }
        }
      }

      Divider()
      ComposerView(store: store)
    }
    .navigationTitle(session.title)
    .toolbar {
      ToolbarItemGroup {
        Picker("Provider", selection: providerSelection) {
          ForEach(ProviderKind.allCases) { provider in
            Text(provider.title)
              .tag(provider)
              .disabled(!provider.isAvailable)
          }
        }
        .frame(width: 145)

        TextField("Model", text: modelSelection)
          .textFieldStyle(.roundedBorder)
          .frame(width: 150)
      }
    }
  }

  private var providerSelection: Binding<ProviderKind> {
    Binding(get: { session.provider }, set: store.updateProvider)
  }

  private var modelSelection: Binding<String> {
    Binding(get: { session.model }, set: store.updateModel)
  }
}

private struct EmptyConversationView: View {
  var body: some View {
    ContentUnavailableView {
      Label("Start an episode", systemImage: "sparkles")
    } description: {
      Text("Your message is written to local evidence before it is sent to a provider.")
    }
    .padding(.top, 100)
  }
}
