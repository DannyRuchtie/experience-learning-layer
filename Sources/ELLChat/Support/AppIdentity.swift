import Foundation

enum AppIdentity {
  private static let workspaceKey = "ell.workspace-id"

  static func workspaceID(defaults: UserDefaults = .standard) -> UUID {
    if let value = defaults.string(forKey: workspaceKey), let id = UUID(uuidString: value) {
      return id
    }
    let id = UUID()
    defaults.set(id.uuidString.lowercased(), forKey: workspaceKey)
    return id
  }
}
