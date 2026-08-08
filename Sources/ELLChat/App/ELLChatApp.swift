import AppKit
import SwiftUI

@main
struct ELLChatApp: App {
  @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
  @State private var store = ChatStore()

  var body: some Scene {
    WindowGroup("ELL Chat", id: "main") {
      ContentView(store: store)
        .frame(minWidth: 760, minHeight: 540)
    }
    .defaultSize(width: 1040, height: 720)
    .commands {
      CommandGroup(after: .newItem) {
        Button("New Episode") { store.newSession() }
          .keyboardShortcut("n", modifiers: .command)
      }
    }

    Settings {
      SettingsView()
    }
  }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
  func applicationDidFinishLaunching(_ notification: Notification) {
    NSApp.setActivationPolicy(.regular)
    NSApp.activate(ignoringOtherApps: true)
  }
}
