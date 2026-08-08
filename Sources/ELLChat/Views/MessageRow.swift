import SwiftUI

struct MessageRow: View {
  let message: ChatMessage

  var body: some View {
    HStack {
      if message.role == .assistant { bubble }
      Spacer(minLength: 80)
      if message.role == .user { bubble }
    }
  }

  private var bubble: some View {
    VStack(alignment: .leading, spacing: 8) {
      if message.text.isEmpty {
        ProgressView()
          .controlSize(.small)
      } else {
        Text(message.text)
          .textSelection(.enabled)
      }
      Text(message.role == .user ? "You" : message.provider.title)
        .font(.caption2)
        .foregroundStyle(.secondary)
    }
    .padding(.horizontal, 14)
    .padding(.vertical, 10)
    .background(
      message.role == .user ? AnyShapeStyle(.tint.opacity(0.14)) : AnyShapeStyle(.regularMaterial),
      in: RoundedRectangle(cornerRadius: 14, style: .continuous)
    )
    .frame(maxWidth: 620, alignment: .leading)
  }
}
