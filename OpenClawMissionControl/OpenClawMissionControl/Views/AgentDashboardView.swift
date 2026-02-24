import SwiftUI
import Combine

struct AgentDashboardView: View {
    @EnvironmentObject private var connection: ConnectionManager

    // Populated by API: GET /api/agents
    @State private var agents: [Agent] = []
    @State private var isLoading: Bool = false
    @State private var errorMessage: String? = nil

    // Known team members from openclaw.json (used as fallback skeleton)
    private let knownAgents: [(name: String, model: String, role: String)] = [
        ("richard",  "claude-opus-4-6",             "Co-Founder"),
        ("jared",    "claude-sonnet-4-5-20250929",  "CMO"),
        ("erlich",   "claude-sonnet-4-5-20250929",  "BD"),
        ("gilfoyle", "claude-opus-4-6",             "CTO"),
        ("monica",   "claude-sonnet-4-5-20250929",  "Writer"),
        ("bighead",  "claude-sonnet-4-5-20250929",  "Intern"),
        ("dinesh",   "claude-sonnet-4-5-20250929",  "Researcher"),
    ]

    var body: some View {
        NavigationStack {
            ZStack {
                AppColors.background.ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 16) {
                        Text("Agents")
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
                        summaryBar
                        agentGrid
                    }
                    .padding()
                }
            }
            .toolbar(.hidden, for: .navigationBar)
            .task {
                await refresh()
            }
            .refreshable {
                await refresh()
            }
            .onReceive(connection.webSocketManager.$lastEnvelope.compactMap { $0?.type }.removeDuplicates()) { type in
                if type == "agent_update" {
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
            let response: AgentsResponse = try await connection.apiClient.fetch("/api/agents")
            agents = response.agents
            connection.markUpdatedNow()
        } catch {
            errorMessage = "Failed to load agents"
        }
    }

    // MARK: - Summary Bar

    private var summaryBar: some View {
        HStack(spacing: 12) {
            StatBadge(label: "Active", value: "\(agents.filter { $0.status == "active" }.count)", color: AppColors.success)
            StatBadge(label: "Idle", value: "\(agents.filter { $0.status == "idle" }.count)", color: AppColors.warning)
            StatBadge(label: "Offline", value: "\(agents.filter { $0.status == "offline" }.count)", color: AppColors.idle)
            Spacer()
        }
    }

    // MARK: - Agent Grid

    private var agentGrid: some View {
        LazyVGrid(
            columns: [GridItem(.flexible()), GridItem(.flexible())],
            spacing: 12
        ) {
            if agents.isEmpty {
                ForEach(knownAgents, id: \.name) { skeleton in
                    AgentCard(
                        name: skeleton.name,
                        role: skeleton.role,
                        model: skeleton.model,
                        status: "unknown",
                        sessionCount: 0,
                        lastActive: nil
                    )
                }
            } else {
                ForEach(agents) { agent in
                    NavigationLink {
                        AgentDetailView(agent: agent)
                    } label: {
                        AgentCard(
                            name: agent.name,
                            role: nil,
                            model: agent.model,
                            status: agent.status,
                            sessionCount: agent.sessionCount,
                            lastActive: agent.lastActive
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }
}

// MARK: - AgentCard

private struct AgentCard: View {
    let name: String
    let role: String?
    let model: String
    let status: String
    let sessionCount: Int
    let lastActive: String?

    private var statusColor: Color {
        switch status {
        case "active": return AppColors.success
        case "idle": return AppColors.warning
        case "offline": return AppColors.error
        default: return AppColors.idle
        }
    }

    private var modelBadgeColor: Color {
        model.contains("opus") ? AppColors.opusBadge : AppColors.sonnetBadge
    }

    private var modelShortName: String {
        if model.contains("opus") { return "Opus" }
        if model.contains("sonnet") { return "Sonnet" }
        return model
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Circle()
                    .fill(statusColor)
                    .frame(width: 8, height: 8)
                Text(name.capitalized)
                    .font(AppFont.display(15, weight: .semibold))
                    .foregroundColor(AppColors.textPrimary)
                Spacer()
            }

            if let role = role {
                Text(role)
                    .font(.caption)
                    .foregroundColor(AppColors.textSecondary)
            }

            Spacer()

            HStack {
                Text(modelShortName)
                    .font(.caption2)
                    .fontWeight(.medium)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(modelBadgeColor.opacity(0.2))
                    .foregroundColor(modelBadgeColor)
                    .cornerRadius(4)
                Spacer()
                Text("\(sessionCount) sess")
                    .font(.caption2)
                    .foregroundColor(AppColors.textTertiary)
            }

            if let lastActive {
                Text(relativeTime(lastActive))
                    .font(.caption2)
                    .foregroundColor(AppColors.textTertiary)
            }
        }
        .padding(12)
        .frame(minHeight: 100)
        .cardStyle()
    }
    private func relativeTime(_ iso: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        guard let date = formatter.date(from: iso) ?? ISO8601DateFormatter().date(from: iso) else {
            return iso
        }
        let relative = RelativeDateTimeFormatter()
        relative.unitsStyle = .abbreviated
        return relative.localizedString(for: date, relativeTo: Date())
    }
}

// MARK: - StatBadge

private struct StatBadge: View {
    let label: String
    let value: String
    let color: Color

    var body: some View {
        HStack(spacing: 4) {
            Circle().fill(color).frame(width: 6, height: 6)
            Text(label).font(.caption).foregroundColor(AppColors.textSecondary)
            Text(value).font(.caption).fontWeight(.bold).foregroundColor(AppColors.textPrimary)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(AppColors.card)
        .cornerRadius(8)
    }
}

#Preview {
    AgentDashboardView()
}
