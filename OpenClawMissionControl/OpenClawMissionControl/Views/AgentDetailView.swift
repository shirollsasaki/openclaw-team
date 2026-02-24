import SwiftUI

struct AgentDetailView: View {
    @EnvironmentObject private var connection: ConnectionManager

    let agent: Agent

    @State private var tokenUsage: AgentTokenUsage? = nil
    @State private var cronJobs: [CronJob] = []
    @State private var isLoading: Bool = false
    @State private var errorMessage: String? = nil
    @State private var messageText: String = ""
    @State private var isSending: Bool = false
    @State private var sendResult: String? = nil

    private var agentId: String {
        let mapping: [String: String] = [
            "Richard Hendricks": "richard",
            "Jared Dunn": "jared",
            "Erlich Bachman": "erlich",
            "Gilfoyle": "gilfoyle",
            "Monica Hall": "monica",
            "Big Head": "bighead",
            "Dinesh Chugtai": "dinesh"
        ]
        return mapping[agent.name] ?? agent.name.lowercased()
    }

    private var displayName: String {
        if agent.name.contains(" ") {
            return agent.name
        }
        return agent.name.capitalized
    }

    private var modelBadgeColor: Color {
        agent.model.lowercased().contains("opus") ? AppColors.error : AppColors.accent
    }

    private var modelShortName: String {
        let lowered = agent.model.lowercased()
        if lowered.contains("opus") { return "Opus" }
        if lowered.contains("sonnet") { return "Sonnet" }
        return agent.model
    }

    private var statusColor: Color {
        switch agent.status.lowercased() {
        case "active":
            return AppColors.success
        case "idle":
            return AppColors.warning
        case "offline":
            return AppColors.idle
        default:
            return AppColors.idle
        }
    }

    var body: some View {
        ZStack {
            AppColors.background.ignoresSafeArea()

            ScrollView {
                VStack(spacing: 12) {
                    if let errorMessage {
                        Text(errorMessage)
                            .font(.caption)
                            .foregroundColor(AppColors.error)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    statusHeaderCard
                    tokenUsageCard
                    cronJobsCard
                    recentActivityCard
                    messageCard
                }
                .padding()
            }
        }
        .navigationTitle(displayName)
        .navigationBarTitleDisplayMode(.inline)
        .toolbarBackground(AppColors.background, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
        .task {
            await loadData()
        }
    }

    private var statusHeaderCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 6) {
                    Text(displayName)
                        .font(AppFont.display(20, weight: .bold))
                        .foregroundColor(AppColors.textPrimary)

                    HStack(spacing: 8) {
                        Text(modelShortName)
                            .font(.caption2)
                            .fontWeight(.semibold)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(modelBadgeColor.opacity(0.2))
                            .foregroundColor(modelBadgeColor)
                            .cornerRadius(6)

                        HStack(spacing: 5) {
                            Circle()
                                .fill(statusColor)
                                .frame(width: 8, height: 8)
                            Text(agent.status.uppercased())
                                .font(.caption2)
                                .fontWeight(.bold)
                                .foregroundColor(AppColors.textSecondary)
                        }
                    }
                }
                Spacer()
                Text("\(agent.sessionCount) sessions")
                    .font(AppFont.mono(12, weight: .semibold))
                    .foregroundColor(AppColors.textPrimary)
            }

            Text("Last active: \(relativeTime(agent.lastActive))")
                .font(.caption)
                .foregroundColor(AppColors.textSecondary)
        }
        .padding(12)
        .cardStyle()
    }

    private var tokenUsageCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Token Usage")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            if let tokenUsage {
                infoRow("Model", tokenUsage.model)
                infoRow("Input", formatTokens(tokenUsage.inputTokens), mono: true)
                infoRow("Output", formatTokens(tokenUsage.outputTokens), mono: true)
                infoRow("Estimated Cost", money(tokenUsage.estimatedCost), valueColor: AppColors.textPrimary, mono: true)
            } else if isLoading {
                Text("Loading token usage...")
                    .font(.callout)
                    .foregroundColor(AppColors.textSecondary)
            } else {
                Text("No token usage data")
                    .font(.callout)
                    .foregroundColor(AppColors.textSecondary)
            }
        }
        .padding(12)
        .cardStyle()
    }

    private var cronJobsCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Cron Jobs")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            if cronJobs.isEmpty {
                Text("No cron jobs assigned")
                    .font(.callout)
                    .foregroundColor(AppColors.textSecondary)
            } else {
                ForEach(cronJobs) { job in
                    HStack(alignment: .top, spacing: 10) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(job.name)
                                .font(.subheadline)
                                .fontWeight(.semibold)
                                .foregroundColor(AppColors.textPrimary)
                            Text(job.schedule?.expr ?? "No schedule")
                                .font(AppFont.mono(12))
                                .foregroundColor(AppColors.textSecondary)
                            Text(job.enabled ? "Enabled" : "Disabled")
                                .font(.caption2)
                                .foregroundColor(job.enabled ? AppColors.success : AppColors.idle)
                        }

                        Spacer()

                        HStack(spacing: 4) {
                            Image(systemName: lastStatusIcon(job.lastStatus))
                                .font(.caption)
                                .foregroundColor(lastStatusColor(job.lastStatus))
                            Text(lastStatusText(job.lastStatus))
                                .font(.caption2)
                                .fontWeight(.medium)
                                .foregroundColor(lastStatusColor(job.lastStatus))
                        }
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
        }
        .padding(12)
        .cardStyle()
    }

    private var recentActivityCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Recent Activity")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            Text("\(agent.sessionCount) sessions")
                .font(AppFont.mono(14, weight: .semibold))
                .foregroundColor(AppColors.textPrimary)

            Text(relativeDate(agent.lastActive))
                .font(.caption)
                .foregroundColor(AppColors.textSecondary)
        }
        .padding(12)
        .cardStyle()
    }


    private var messageCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Send Message")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    quickActionButton("Status report")
                    quickActionButton("Summarize recent activity")
                    quickActionButton("List active tasks")
                }
            }

            HStack(spacing: 8) {
                TextField("Message \(displayName)...", text: $messageText)
                    .textFieldStyle(.roundedBorder)
                    .font(.callout)

                if isSending {
                    ProgressView()
                        .scaleEffect(0.8)
                } else {
                    Button {
                        Task { await sendMessage(messageText) }
                    } label: {
                        Image(systemName: "paperplane.fill")
                            .foregroundColor(messageText.isEmpty ? AppColors.textTertiary : AppColors.accent)
                    }
                    .disabled(messageText.isEmpty)
                }
            }

            if let sendResult {
                Text(sendResult)
                    .font(.caption)
                    .foregroundColor(AppColors.textSecondary)
                    .lineLimit(5)
            }
        }
        .padding(12)
        .cardStyle()
    }

    private func quickActionButton(_ text: String) -> some View {
        Button {
            Task { await sendMessage(text) }
        } label: {
            Text(text)
                .font(.caption)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(AppColors.accent.opacity(0.15))
                .foregroundColor(AppColors.accent)
                .cornerRadius(8)
        }
        .disabled(isSending)
    }

    private func sendMessage(_ text: String) async {
        guard !text.isEmpty else { return }
        isSending = true
        sendResult = nil
        defer { isSending = false }
        let request = AgentMessageRequest(agentId: agentId, message: text)
        do {
            let response: CommandResponse = try await connection.apiClient.post("/api/commands/agent/message", body: request)
            if response.status == "ok" {
                sendResult = response.stdout ?? "Message sent"
                messageText = ""
            } else {
                sendResult = response.error ?? "Unknown error"
            }
        } catch {
            sendResult = "Failed to send message"
        }
    }
    private func loadData() async {
        if isLoading { return }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            async let tokenResponse: TokenUsageResponse = connection.apiClient.fetch("/api/tokens/usage")
            async let cronResponse: CronJobsResponse = connection.apiClient.fetch("/api/cron/jobs")

            let (tokens, cron) = try await (tokenResponse, cronResponse)

            tokenUsage = tokens.agents.first(where: { usage in
                let usageName = usage.name.lowercased()
                let id = agentId.lowercased()
                return usageName == id || usageName.contains(id)
            })

            cronJobs = cron.jobs.filter { $0.agent.lowercased() == agentId.lowercased() }
            connection.markUpdatedNow()
        } catch {
            errorMessage = "Failed to load agent details"
        }
    }

    @ViewBuilder
    private func infoRow(_ label: String, _ value: String, valueColor: Color = AppColors.textPrimary, mono: Bool = false) -> some View {
        HStack {
            Text(label)
                .font(.caption)
                .foregroundColor(AppColors.textTertiary)
            Spacer()
            Text(value)
                .font(mono ? AppFont.mono(13, weight: .semibold) : .caption)
                .foregroundColor(valueColor)
        }
    }

    private func formatTokens(_ count: Int) -> String {
        if count >= 1_000_000 {
            return String(format: "%.2fM", Double(count) / 1_000_000.0)
        }
        if count >= 1_000 {
            return String(format: "%.1fK", Double(count) / 1_000.0)
        }
        return String(count)
    }

    private func money(_ value: Double) -> String {
        String(format: "$%.4f", value)
    }

    private func relativeTime(_ iso: String?) -> String {
        guard let iso else { return "Unknown" }
        guard let date = parseISODate(iso) else { return iso }
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: date, relativeTo: Date())
    }

    private func relativeDate(_ iso: String?) -> String {
        guard let iso else { return "No recent activity" }
        guard let date = parseISODate(iso) else { return iso }

        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return "Last active \(formatter.string(from: date))"
    }

    private func parseISODate(_ value: String) -> Date? {
        let formatterWithFractional = ISO8601DateFormatter()
        formatterWithFractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

        if let date = formatterWithFractional.date(from: value) {
            return date
        }

        return ISO8601DateFormatter().date(from: value)
    }

    private func lastStatusIcon(_ status: String?) -> String {
        if status?.lowercased() == "ok" {
            return "checkmark.circle.fill"
        }
        if status == nil || status?.isEmpty == true {
            return "minus.circle"
        }
        return "xmark.circle.fill"
    }

    private func lastStatusColor(_ status: String?) -> Color {
        if status?.lowercased() == "ok" {
            return AppColors.success
        }
        if status == nil || status?.isEmpty == true {
            return AppColors.idle
        }
        return AppColors.error
    }

    private func lastStatusText(_ status: String?) -> String {
        if status?.lowercased() == "ok" {
            return "OK"
        }
        if status == nil || status?.isEmpty == true {
            return "-"
        }
        return "ERROR"
    }
}

#Preview {
    AgentDetailView(agent: Agent(name: "richard", model: "claude-opus-4-6", status: "active", lastActive: nil, sessionCount: 3))
}
