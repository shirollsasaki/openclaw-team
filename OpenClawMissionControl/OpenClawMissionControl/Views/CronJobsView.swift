import SwiftUI
import Combine

struct CronJobsView: View {
    @EnvironmentObject private var connection: ConnectionManager

    @State private var jobs: [CronJob] = []
    @State private var isLoading: Bool = false
    @State private var errorMessage: String? = nil
    @State private var expanded: Set<String> = []
    @State private var togglingJobs: Set<String> = []

    var body: some View {
        NavigationStack {
            ZStack {
                AppColors.background.ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 12) {
                        Text("Cron")
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

                        ForEach(groupedAgents, id: \.key) { group in
                            VStack(alignment: .leading, spacing: 10) {
                                Text(group.key.capitalized)
                                    .font(.headline)
                                    .foregroundColor(AppColors.textPrimary)

                                ForEach(group.value) { job in
                                    cronRow(job)
                                }
                            }
                            .padding(12)
                            .cardStyle()
                        }
                    }
                    .padding()
                }
            }
            .toolbar(.hidden, for: .navigationBar)
            .task { await refresh() }
            .refreshable { await refresh() }
            .onReceive(connection.webSocketManager.$lastEnvelope.compactMap { $0?.type }.removeDuplicates()) { type in
                if type == "cron_update" {
                    Task { await refresh() }
                }
            }
        }
    }

    private var groupedAgents: [(key: String, value: [CronJob])] {
        let grouped = Dictionary(grouping: jobs) { $0.agent }
        return grouped.keys.sorted().map { ($0, grouped[$0] ?? []) }
    }

    private func refresh() async {
        if isLoading { return }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let response: CronJobsResponse = try await connection.apiClient.fetch("/api/cron/jobs")
            jobs = response.jobs
            connection.markUpdatedNow()
        } catch {
            errorMessage = "Failed to load cron jobs"
        }
    }

    private func cronRow(_ job: CronJob) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(job.name)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundColor(AppColors.textPrimary)
                    Text(job.schedule?.expr ?? "")
                        .font(AppFont.mono(12))
                        .foregroundColor(AppColors.textTertiary)
                    Text(humanReadableCron(job.schedule?.expr))
                        .font(.caption)
                        .foregroundColor(AppColors.textSecondary)
                }
                Spacer()
                if togglingJobs.contains(job.id) {
                    ProgressView()
                        .scaleEffect(0.7)
                } else {
                    Toggle("", isOn: Binding(
                        get: { job.enabled },
                        set: { _ in Task { await toggleCronJob(job) } }
                    ))
                    .labelsHidden()
                    .tint(AppColors.accent)
                }
                statusBadge(enabled: job.enabled, status: job.lastStatus)
            }

            HStack {
                Text("Last: \(formatMs(job.lastRun))")
                    .font(.caption)
                    .foregroundColor(AppColors.textSecondary)
                Spacer()
                Text("Next: \(formatMs(job.nextRun))")
                    .font(.caption)
                    .foregroundColor(AppColors.textSecondary)
            }

            HStack {
                Text("Errors: \(job.consecutiveErrors)")
                    .font(.caption)
                    .foregroundColor(job.consecutiveErrors > 0 ? AppColors.error : AppColors.textTertiary)
                Spacer()
                Button {
                    toggleExpanded(job.id)
                } label: {
                    Text(expanded.contains(job.id) ? "Hide runs" : "Show runs")
                        .font(.caption)
                }
                .buttonStyle(.borderless)
            }

            if expanded.contains(job.id) {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(job.recentRuns.prefix(5)) { run in
                        HStack {
                            Text(run.status ?? "")
                                .font(AppFont.mono(12))
                                .foregroundColor((run.status == "ok") ? AppColors.success : AppColors.warning)
                            Spacer()
                            Text(formatMs(run.startedAtMs))
                                .font(.caption2)
                                .foregroundColor(AppColors.textTertiary)
                        }
                    }
                }
                .padding(10)
                .background(AppColors.surface)
                .cornerRadius(10)
            }
        }
        .padding(12)
        .background(AppColors.surface)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(AppColors.border, lineWidth: 1)
        )
    }

    private func toggleExpanded(_ id: String) {
        if expanded.contains(id) {
            expanded.remove(id)
        } else {
            expanded.insert(id)
        }
    }

    private func toggleCronJob(_ job: CronJob) async {
        togglingJobs.insert(job.id)
        defer { togglingJobs.remove(job.id) }
        let endpoint = job.enabled ? "/api/commands/cron/disable/\(job.id)" : "/api/commands/cron/enable/\(job.id)"
        do {
            let _: CommandResponse = try await connection.apiClient.post(endpoint)
            await refresh()
        } catch {
            errorMessage = "Failed to toggle \(job.name)"
        }
    }

    private func statusBadge(enabled: Bool, status: String?) -> some View {
        let text: String
        let color: Color
        if !enabled {
            text = "DISABLED"
            color = AppColors.idle
        } else if status == "ok" {
            text = "OK"
            color = AppColors.success
        } else if (status ?? "").isEmpty {
            text = "-"
            color = AppColors.idle
        } else {
            text = String(status ?? "ERR").uppercased()
            color = AppColors.warning
        }

        return Text(text)
            .font(.caption2)
            .fontWeight(.bold)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(color.opacity(0.2))
            .foregroundColor(color)
            .cornerRadius(8)
    }

    private func formatMs(_ ms: Int?) -> String {
        guard let ms else { return "-" }
        let date = Date(timeIntervalSince1970: Double(ms) / 1000.0)
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: date, relativeTo: Date())
    }

    private func humanReadableCron(_ expr: String?) -> String {
        guard let expr else { return "" }
        let parts = expr.split(separator: " ").map(String.init)
        guard parts.count >= 5 else { return expr }

        let minute = parts[0]
        let hour = parts[1]
        let dayOfMonth = parts[2]
        let month = parts[3]
        let dayOfWeek = parts[4]

        if hour == "*" && dayOfMonth == "*" && month == "*" && dayOfWeek == "*" {
            if minute.hasPrefix("*/") {
                let interval = String(minute.dropFirst(2))
                return "Every \(interval) min"
            }
            return "Every minute"
        }

        if minute != "*" && hour.hasPrefix("*/") && dayOfMonth == "*" && month == "*" && dayOfWeek == "*" {
            let interval = String(hour.dropFirst(2))
            return "Every \(interval)h"
        }

        if minute != "*" && hour != "*" && !hour.contains("/") && !hour.contains(",") && dayOfMonth == "*" && month == "*" && dayOfWeek == "*" {
            let h = Int(hour) ?? 0
            let ampm = h >= 12 ? "PM" : "AM"
            let h12 = h == 0 ? 12 : (h > 12 ? h - 12 : h)
            let m = minute.padding(toLength: 2, withPad: "0", startingAt: 0)
            return "Daily at \(h12):\(m) \(ampm)"
        }

        return expr
    }
}

#Preview {
    CronJobsView()
}
