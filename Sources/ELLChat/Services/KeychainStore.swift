import Foundation
import Security

enum KeychainStore {
  private static let service = "com.ruchtie.ell-chat"
  private static let openAIAccount = "openai-api-key"

  static func readOpenAIKey() throws -> String? {
    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword,
      kSecAttrService as String: service,
      kSecAttrAccount as String: openAIAccount,
      kSecReturnData as String: true,
      kSecMatchLimit as String: kSecMatchLimitOne,
    ]
    var result: CFTypeRef?
    let status = SecItemCopyMatching(query as CFDictionary, &result)
    if status == errSecItemNotFound { return nil }
    guard status == errSecSuccess, let data = result as? Data else {
      throw KeychainError(status: status)
    }
    return String(data: data, encoding: .utf8)
  }

  static func saveOpenAIKey(_ value: String) throws {
    let data = Data(value.utf8)
    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword,
      kSecAttrService as String: service,
      kSecAttrAccount as String: openAIAccount,
    ]
    let attributes = [kSecValueData as String: data]
    let updateStatus = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
    if updateStatus == errSecItemNotFound {
      var insertion = query
      insertion[kSecValueData as String] = data
      let status = SecItemAdd(insertion as CFDictionary, nil)
      guard status == errSecSuccess else { throw KeychainError(status: status) }
    } else if updateStatus != errSecSuccess {
      throw KeychainError(status: updateStatus)
    }
  }

  static func deleteOpenAIKey() throws {
    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword,
      kSecAttrService as String: service,
      kSecAttrAccount as String: openAIAccount,
    ]
    let status = SecItemDelete(query as CFDictionary)
    guard status == errSecSuccess || status == errSecItemNotFound else {
      throw KeychainError(status: status)
    }
  }
}

private struct KeychainError: LocalizedError {
  let status: OSStatus

  var errorDescription: String? {
    SecCopyErrorMessageString(status, nil) as String? ?? "Keychain error \(status)"
  }
}
