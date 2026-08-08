import CryptoKit
import Foundation

enum StableIdentifiers {
  static let ellNamespace = UUID(uuidString: "57d81e68-b0d4-5031-9dbf-cd69aa4edfd2")!

  static func sourceID(messageID: UUID) -> UUID {
    uuid5(namespace: ellNamespace, name: "source:ell_chat:\(canonical(messageID)):1")
  }

  static func eventID(sourceID: UUID, messageID: UUID) -> UUID {
    uuid5(namespace: sourceID, name: "event:\(canonical(messageID))")
  }

  static func episodeID(workspaceID: UUID, eventIDs: [UUID]) -> UUID {
    let joined = eventIDs.map(canonical).joined(separator: ":")
    return uuid5(namespace: workspaceID, name: "episode:\(joined)")
  }

  static func spanID(sourceID: UUID) -> UUID {
    uuid5(namespace: sourceID, name: "span:0")
  }

  static func sha256(_ text: String) -> String {
    let digest = SHA256.hash(data: Data(text.utf8))
    return "sha256:" + digest.map { String(format: "%02x", $0) }.joined()
  }

  private static func uuid5(namespace: UUID, name: String) -> UUID {
    var namespaceBytes = withUnsafeBytes(of: namespace.uuid) { Array($0) }
    namespaceBytes.append(contentsOf: name.utf8)
    var bytes = Array(Insecure.SHA1.hash(data: Data(namespaceBytes)).prefix(16))
    bytes[6] = (bytes[6] & 0x0F) | 0x50
    bytes[8] = (bytes[8] & 0x3F) | 0x80
    let hex = bytes.map { String(format: "%02x", $0) }.joined()
    let value =
      "\(hex.prefix(8))-\(hex.dropFirst(8).prefix(4))-\(hex.dropFirst(12).prefix(4))-\(hex.dropFirst(16).prefix(4))-\(hex.dropFirst(20))"
    return UUID(uuidString: value)!
  }

  private static func canonical(_ id: UUID) -> String {
    id.uuidString.lowercased()
  }
}
