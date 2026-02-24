import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var connection: ConnectionManager

    @State private var draftURL: String = ""
    @State private var commandMessage: String? = nil
    @State private var isRunningCommand: Bool = false
    @State private var showCronSheet: Bool = false
    @State private var cronJobs: [CronJob] = []

    var body: some View {
        NavigationStack {
            ZStack {
                AppColors.background.ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 12) {
                        Text("Settings")
                            .font(AppFont.display(34, weight: .bold))
                            .foregroundColor(AppColors.textPrimary)
                            .frame(maxWidth: .infinity, alignment: .leading)

                        connectionCard
                        commandsCard

                        if let commandMessage {
                            Text(commandMessage)
                                .font(.caption)
                                .foregroundColor(AppColors.textSecondary)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }

                        aboutCard
                    }
                    .padding()
                }
            }
            .toolbar(.hidden, for: .navigationBar)
            .task {
                draftURL = connection.baseURLString
                await preloadCronJobs()
            }
            .sheet(isPresented: $showCronSheet) {
                cronJobPicker
            }
        }
    }

    private var connectionCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Connection")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            VStack(alignment: .leading, spacing: 8) {
                Text("API Base URL")
                    .font(.caption)
                    .foregroundColor(AppColors.textTertiary)

                TextField("http://192.168.1.X:3001", text: $draftURL)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled(true)
                    .keyboardType(.URL)
                    .padding(10)
                    .background(AppColors.surface)
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(AppColors.border, lineWidth: 1)
                    )

                HStack {
                    statusDot(connection.webSocketManager.isConnected)
                    Text(connection.webSocketManager.isConnected ? "WebSocket connected" : "WebSocket disconnected")
                        .font(.caption)
                        .foregroundColor(AppColors.textSecondary)
                    Spacer()
                    Button("Reconnect") {
                        connection.setBaseURL(draftURL)
                    }
                    .disabled(isRunningCommand)
                }
            }
        }
        .padding(12)
        .cardStyle()
    }

    private var commandsCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Commands")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            Button {
                Task { await runRefresh() }
            } label: {
                HStack {
                    Text("Refresh All Data")
                    Spacer()
                    if isRunningCommand { ProgressView().tint(AppColors.accent) }
                }
            }
            .buttonStyle(.borderedProminent)
            .tint(AppColors.accent)
            .disabled(isRunningCommand)

            Button {
                showCronSheet = true
            } label: {
                HStack {
                    Text("Run Cron Job")
                    Spacer()
                    Image(systemName: "chevron.right")
                        .foregroundColor(AppColors.textTertiary)
                }
            }
            .buttonStyle(.bordered)
            .disabled(isRunningCommand)
        }
        .padding(12)
        .cardStyle()
    }

    private var aboutCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("About")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            HStack {
                Text("Version")
                    .font(.subheadline)
                    .foregroundColor(AppColors.textSecondary)
                Spacer()
                Text(appVersion)
                    .font(AppFont.mono(13))
                    .foregroundColor(AppColors.textPrimary)
            }

            HStack {
                Text("Build")
                    .font(.subheadline)
                    .foregroundColor(AppColors.textSecondary)
                Spacer()
                Text(appBuild)
                    .font(AppFont.mono(13))
                    .foregroundColor(AppColors.textPrimary)
            }

            if let lastUpdated = connection.lastUpdated {
                HStack {
                    Text("Last Updated")
                        .font(.subheadline)
                        .foregroundColor(AppColors.textSecondary)
                    Spacer()
                    Text(lastUpdated, style: .relative)
                        .font(.caption)
                        .foregroundColor(AppColors.textTertiary)
                    Text("ago")
                        .font(.caption)
                        .foregroundColor(AppColors.textTertiary)
                }
            }
        }
        .padding(12)
        .cardStyle()
    }

    private var cronJobPicker: some View {
        NavigationStack {
            List {
                ForEach(cronJobs) { job in
                    Button {
                        Task {
                            showCronSheet = false
                            await runCronJob(job.id)
                        }
                    } label: {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(job.name)
                            Text(job.agent)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
            .navigationTitle("Run Cron")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { showCronSheet = false }
                }
            }
        }
    }

    private var appVersion: String {
        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
    }

    private var appBuild: String {
        Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1"
    }

    private func statusDot(_ connected: Bool) -> some View {
        Circle()
            .fill(connected ? AppColors.success : AppColors.error)
            .frame(width: 8, height: 8)
    }

    private func preloadCronJobs() async {
        do {
            let response: CronJobsResponse = try await connection.apiClient.fetch("/api/cron/jobs")
            cronJobs = response.jobs
        } catch {
            cronJobs = []
        }
    }

    private func runRefresh() async {
        if isRunningCommand { return }
        isRunningCommand = true
        commandMessage = nil
        defer { isRunningCommand = false }

        do {
            let resp: CommandStatusResponse = try await connection.apiClient.post("/api/commands/refresh")
            commandMessage = "Refresh: \(resp.status)"
        } catch {
            commandMessage = "Refresh failed"
        }
    }

    private func runCronJob(_ jobId: String) async {
        if isRunningCommand { return }
        isRunningCommand = true
        commandMessage = nil
        defer { isRunningCommand = false }

        do {
            let resp: CommandCronRunResponse = try await connection.apiClient.post("/api/commands/cron/run/\(jobId)")
            commandMessage = "Cron run: \(resp.status)"
        } catch {
            commandMessage = "Cron run failed"
        }
    }
}

#Preview {
    SettingsView()
}
