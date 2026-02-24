import SwiftUI
import Combine
#if canImport(Charts)
import Charts
#endif

struct TokenUsageView: View {
    @EnvironmentObject private var connection: ConnectionManager

    @State private var usage: TokenUsageResponse? = nil
    @State private var isLoading: Bool = false
    @State private var errorMessage: String? = nil

    var body: some View {
        NavigationStack {
            ZStack {
                AppColors.background.ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 12) {
                        Text("Tokens")
                            .font(AppFont.display(34, weight: .bold))
                            .foregroundColor(AppColors.textPrimary)
                            .frame(maxWidth: .infinity, alignment: .leading)

                        ConnectionBanner(
                            state: connection.connectionState,
                            baseURL: connection.baseURLString,
                            lastUpdated: connection.lastUpdated
                        )

                        if let errorMessage {
                            Text(errorMessage)
                                .font(.caption)
                                .foregroundColor(AppColors.error)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }

                        totalCard
                        chartCard
                        listCard
                    }
                    .padding()
                }
            }
            .toolbar(.hidden, for: .navigationBar)
            .task { await refresh() }
            .refreshable { await refresh() }
            .onReceive(connection.webSocketManager.$lastEnvelope.compactMap { $0?.type }.removeDuplicates()) { type in
                if type == "token_update" {
                    Task { await refresh() }
                }
            }
        }
    }

    private func refresh() async {
        if isLoading { return }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let response: TokenUsageResponse = try await connection.apiClient.fetch("/api/tokens/usage")
            usage = response
            connection.markUpdatedNow()
        } catch {
            errorMessage = "Failed to load token usage"
        }
    }

    private var totalCard: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Estimated Spend")
                .font(.caption)
                .foregroundColor(AppColors.textTertiary)
            Text(money(usage?.total.estimatedCost))
                .font(AppFont.display(34, weight: .bold))
                .foregroundColor(AppColors.textPrimary)
            Text("Total tokens: \(usage?.total.tokens ?? 0)")
                .font(.caption)
                .foregroundColor(AppColors.textSecondary)
        }
        .padding(12)
        .cardStyle()
    }

    private var chartCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("By Agent")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            #if canImport(Charts)
            if let agents = usage?.agents, !agents.isEmpty {
                Chart(agents) { a in
                    BarMark(
                        x: .value("Agent", a.name),
                        y: .value("Cost", a.estimatedCost)
                    )
                    .foregroundStyle(a.model.contains("opus") ? AppColors.opusBadge : AppColors.sonnetBadge)
                }
                .chartYAxis {
                    AxisMarks(position: .leading)
                }
                .frame(height: 180)
            } else {
                Text("No data")
                    .font(.callout)
                    .foregroundColor(AppColors.textSecondary)
            }
            #else
            Text("Charts unavailable")
                .font(.callout)
                .foregroundColor(AppColors.textSecondary)
            #endif
        }
        .padding(12)
        .cardStyle()
    }

    private var listCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Agents")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            ForEach(usage?.agents ?? []) { a in
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(a.name.capitalized)
                            .font(.subheadline)
                            .foregroundColor(AppColors.textPrimary)
                        HStack(spacing: 4) {
                            Text(a.model.contains("opus") ? "Opus" : "Sonnet")
                                .font(.caption2)
                                .fontWeight(.medium)
                                .padding(.horizontal, 5)
                                .padding(.vertical, 1)
                                .background((a.model.contains("opus") ? AppColors.opusBadge : AppColors.sonnetBadge).opacity(0.2))
                                .foregroundColor(a.model.contains("opus") ? AppColors.opusBadge : AppColors.sonnetBadge)
                                .cornerRadius(4)
                            Text(formatTokens(a.inputTokens) + "↑ " + formatTokens(a.outputTokens) + "↓")
                                .font(.caption2)
                                .foregroundColor(AppColors.textTertiary)
                        }
                    }
                    Spacer()
                    Text(money(a.estimatedCost))
                        .font(AppFont.mono(13, weight: .semibold))
                        .foregroundColor(AppColors.textPrimary)
                }
                .padding(.vertical, 6)
                .overlay(
                    Rectangle()
                        .fill(AppColors.border)
                        .frame(height: 1)
                        .opacity(0.6),
                    alignment: .bottom
                )
            }
        }
        .padding(12)
        .cardStyle()
    }
    private func money(_ value: Double?) -> String {
        guard let value else { return "-" }
        return String(format: "$%.2f", value)
    }
    private func formatTokens(_ count: Int) -> String {
        if count >= 1_000_000 {
            return String(format: "%.1fM", Double(count) / 1_000_000.0)
        } else if count >= 1_000 {
            return String(format: "%.1fK", Double(count) / 1_000.0)
        }
        return String(count)
    }
    }

#Preview {
    TokenUsageView()
}
