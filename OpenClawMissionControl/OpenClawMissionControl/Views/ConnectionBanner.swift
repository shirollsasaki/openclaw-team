import SwiftUI

struct ConnectionBanner: View {
    let state: ConnectionState
    let baseURL: String
    let lastUpdated: Date?

    var body: some View {
        if state == .connected {
            EmptyView()
        } else {
            HStack(spacing: 10) {
                Circle()
                    .fill(state == .connecting ? AppColors.warning : AppColors.error)
                    .frame(width: 8, height: 8)
                VStack(alignment: .leading, spacing: 2) {
                    Text(state == .connecting ? "Connecting" : "Disconnected")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundColor(AppColors.textPrimary)
                    Text(baseURL)
                        .font(.caption2)
                        .foregroundColor(AppColors.textTertiary)
                }
                Spacer()
                Text(lastUpdatedText)
                    .font(.caption2)
                    .foregroundColor(AppColors.textTertiary)
            }
            .padding(10)
            .background(AppColors.surface)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(AppColors.border, lineWidth: 1)
            )
        }
    }

    private var lastUpdatedText: String {
        guard let lastUpdated else { return "" }
        let f = RelativeDateTimeFormatter()
        f.unitsStyle = .abbreviated
        return "Updated \(f.localizedString(for: lastUpdated, relativeTo: Date()))"
    }
}

#Preview {
    ConnectionBanner(state: .disconnected, baseURL: "http://localhost:3001", lastUpdated: Date().addingTimeInterval(-120))
}
