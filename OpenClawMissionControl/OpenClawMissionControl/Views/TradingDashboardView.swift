import SwiftUI
import Combine
#if canImport(Charts)
import Charts
#endif

struct TradingDashboardView: View {
    @EnvironmentObject private var connection: ConnectionManager

    @State private var status: TradingStatus? = nil
    @State private var stats: TradeStats? = nil
    @State private var equityHistory: [EquityPoint] = []
    @State private var isLoading: Bool = false
    @State private var errorMessage: String? = nil
    @State private var actionMessage: String = ""
    @State private var isSendingAction: Bool = false
    @State private var actionResult: String? = nil

    private struct EquityChartPoint: Identifiable {
        let date: Date
        let equity: Double
        var id: TimeInterval { date.timeIntervalSince1970 }
    }

    var body: some View {
        NavigationStack {
            ZStack {
                AppColors.background.ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 12) {
                        Text("Trading")
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

                        headerCard
                        quickActionsCard
                        statsSummaryCard
                        equityChartCard
                        assetBreakdownCard
                        positionsCard
                        tradesCard
                    }
                    .padding()
                }
            }
            .toolbar(.hidden, for: .navigationBar)
            .task { await refresh() }
            .refreshable { await refresh() }
            .onReceive(connection.webSocketManager.$lastEnvelope.compactMap { $0?.type }.removeDuplicates()) { type in
                if type == "trading_update" || type == "trade_update" {
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
            async let statusResponse: TradingStatus = connection.apiClient.fetch("/api/trading/status")
            async let statsResponse: TradeStats = connection.apiClient.fetch("/api/trading/stats")
            async let equityResponse: EquityHistoryResponse = connection.apiClient.fetch("/api/trading/equity-history")

            let (tradingStatus, tradeStats, history) = try await (statusResponse, statsResponse, equityResponse)

            status = tradingStatus
            stats = tradeStats
            equityHistory = history.points
            connection.markUpdatedNow()
        } catch {
            errorMessage = "Failed to load trading status"
        }
    }

    private var headerCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("V2 + Squeeze")
                    .font(.headline)
                    .foregroundColor(AppColors.textPrimary)
                Spacer()
                HStack(spacing: 6) {
                    Circle()
                        .fill((status?.botRunning ?? false) ? AppColors.success : AppColors.error)
                        .frame(width: 8, height: 8)
                    Text((status?.botRunning ?? false) ? "RUNNING" : "STOPPED")
                        .font(.caption2)
                        .fontWeight(.bold)
                        .foregroundColor(AppColors.textSecondary)
                }
            }

            HStack(spacing: 12) {
                metric("Equity", money(status?.equity))
                metric("Unrealized", moneySigned(status?.unrealized))
                metric("Total", money(status?.total))
            }

            Text("Updated: \(status?.lastUpdate ?? "-")")
                .font(.caption2)
                .foregroundColor(AppColors.textTertiary)
        }
        .padding(12)
        .cardStyle()
    }

    private var positionsCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Open Positions")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            if (status?.openPositions ?? []).isEmpty {
                Text("No open positions")
                    .font(.callout)
                    .foregroundColor(AppColors.textSecondary)
            } else {
                ForEach(Array((status?.openPositions ?? []).enumerated()), id: \.offset) { _, p in
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text(p.asset)
                                .font(AppFont.mono(13, weight: .semibold))
                                .foregroundColor(AppColors.textPrimary)
                            Text(p.side)
                                .font(.caption2)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background((p.side == "LONG" ? AppColors.success : AppColors.error).opacity(0.2))
                                .foregroundColor(p.side == "LONG" ? AppColors.success : AppColors.error)
                                .cornerRadius(6)
                            Spacer()
                            Text(moneySigned(p.unrealized))
                                .font(AppFont.mono(13, weight: .semibold))
                                .foregroundColor((p.unrealized ?? 0) >= 0 ? AppColors.success : AppColors.error)
                        }
                        HStack(spacing: 12) {
                            if let entry = p.entry {
                                Text("Entry: \(String(format: "$%.2f", entry))")
                                    .font(.caption2)
                                    .foregroundColor(AppColors.textTertiary)
                            }
                            if let sl = p.sl {
                                Text("SL: \(String(format: "$%.2f", sl))")
                                    .font(.caption2)
                                    .foregroundColor(AppColors.error)
                            }
                            if let tp = p.tp {
                                Text("TP: \(String(format: "$%.2f", tp))")
                                    .font(.caption2)
                                    .foregroundColor(AppColors.success)
                            }
                            Spacer()
                        }
                    }
                    .padding(10)
                    .background(AppColors.surface)
                    .cornerRadius(10)
                }
            }
        }
        .padding(12)
        .cardStyle()
    }

    private var statsSummaryCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Stats Summary")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            if let stats {
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                    statTile("Win Rate", "\(stats.winRate)%", color: AppColors.textPrimary)
                    statTile("Total P&L", moneySigned(stats.totalPnl), color: stats.totalPnl >= 0 ? AppColors.success : AppColors.error)
                    statTile("Avg P&L", moneySigned(stats.avgPnl), color: stats.avgPnl >= 0 ? AppColors.success : AppColors.error)
                    statTile("Biggest Win", moneySigned(stats.biggestWin), color: stats.biggestWin >= 0 ? AppColors.success : AppColors.error)
                    statTile("Biggest Loss", moneySigned(stats.biggestLoss), color: stats.biggestLoss >= 0 ? AppColors.success : AppColors.error)
                    statTile("Total Trades", "\(stats.totalTrades)", color: AppColors.textPrimary)
                }
            } else {
                Text("No stats data")
                    .font(.callout)
                    .foregroundColor(AppColors.textSecondary)
            }
        }
        .padding(12)
        .cardStyle()
    }

    private var equityChartCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Equity Curve")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            #if canImport(Charts)
            if chartPoints.isEmpty {
                Text("No equity history")
                    .font(.callout)
                    .foregroundColor(AppColors.textSecondary)
            } else {
                Chart(chartPoints) { point in
                    AreaMark(
                        x: .value("Time", point.date),
                        y: .value("Equity", point.equity)
                    )
                    .foregroundStyle(
                        LinearGradient(
                            colors: [AppColors.accent.opacity(0.35), AppColors.accent.opacity(0.02)],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )

                    LineMark(
                        x: .value("Time", point.date),
                        y: .value("Equity", point.equity)
                    )
                    .interpolationMethod(.catmullRom)
                    .foregroundStyle(AppColors.accent)
                    .lineStyle(StrokeStyle(lineWidth: 2.5, lineCap: .round, lineJoin: .round))
                }
                .chartYAxis {
                    AxisMarks(position: .leading)
                }
                .chartXAxis {
                    AxisMarks(values: .automatic(desiredCount: 4))
                }
                .frame(height: 190)
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

    private var assetBreakdownCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Asset Breakdown")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            if let assets = stats?.assetBreakdown, !assets.isEmpty {
                HStack {
                    Text("Asset")
                    Spacer()
                    Text("Trades")
                    Spacer()
                    Text("P&L")
                    Spacer()
                    Text("Win")
                }
                .font(.caption2)
                .foregroundColor(AppColors.textTertiary)

                ForEach(assets) { asset in
                    HStack {
                        Text(asset.asset)
                            .font(AppFont.mono(12, weight: .semibold))
                            .foregroundColor(AppColors.textPrimary)
                            .frame(maxWidth: .infinity, alignment: .leading)

                        Text("\(asset.trades)")
                            .font(AppFont.mono(12, weight: .medium))
                            .foregroundColor(AppColors.textSecondary)
                            .frame(width: 44, alignment: .trailing)

                        Text(moneySigned(asset.pnl))
                            .font(AppFont.mono(12, weight: .semibold))
                            .foregroundColor(asset.pnl >= 0 ? AppColors.success : AppColors.error)
                            .frame(width: 76, alignment: .trailing)

                        Text("\(asset.winRate)%")
                            .font(.caption2)
                            .fontWeight(.bold)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 3)
                            .background((asset.winRate >= 50 ? AppColors.success : AppColors.error).opacity(0.18))
                            .foregroundColor(asset.winRate >= 50 ? AppColors.success : AppColors.error)
                            .cornerRadius(6)
                            .frame(width: 52, alignment: .trailing)
                    }
                    .padding(.vertical, 4)
                    .overlay(
                        Rectangle()
                            .fill(AppColors.border)
                            .frame(height: 1)
                            .opacity(0.6),
                        alignment: .bottom
                    )
                }
            } else {
                Text("No asset breakdown")
                    .font(.callout)
                    .foregroundColor(AppColors.textSecondary)
            }
        }
        .padding(12)
        .cardStyle()
    }

    private var tradesCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Recent Trades")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            if (status?.recentTrades ?? []).isEmpty {
                Text("No recent trades")
                    .font(.callout)
                    .foregroundColor(AppColors.textSecondary)
            } else {
                ForEach(status?.recentTrades.suffix(10) ?? []) { t in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(t.asset ?? "")
                                .font(AppFont.mono(12, weight: .semibold))
                                .foregroundColor(AppColors.textPrimary)
                            Text(t.direction ?? "")
                                .font(.caption2)
                                .foregroundColor(AppColors.textTertiary)
                            Spacer()
                            Text(t.pnl ?? "")
                                .font(AppFont.mono(12, weight: .semibold))
                                .foregroundColor((Double(t.pnl ?? "") ?? 0) >= 0 ? AppColors.success : AppColors.error)
                        }
                        if let exitTime = t.exitTime, !exitTime.isEmpty {
                            Text(exitTime)
                                .font(.caption2)
                                .foregroundColor(AppColors.textTertiary)
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


    private var quickActionsCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Quick Actions")
                .font(.headline)
                .foregroundColor(AppColors.textPrimary)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    tradingActionButton("Status report", icon: "doc.text")
                    tradingActionButton("P&L summary", icon: "chart.bar")
                    tradingActionButton("Close all positions", icon: "xmark.circle", destructive: true)
                }
            }

            HStack(spacing: 8) {
                TextField("Message Big Head...", text: $actionMessage)
                    .textFieldStyle(.roundedBorder)
                    .font(.callout)

                if isSendingAction {
                    ProgressView()
                        .scaleEffect(0.8)
                } else {
                    Button {
                        Task { await sendTradingAction(actionMessage) }
                    } label: {
                        Image(systemName: "paperplane.fill")
                            .foregroundColor(actionMessage.isEmpty ? AppColors.textTertiary : AppColors.accent)
                    }
                    .disabled(actionMessage.isEmpty)
                }
            }

            if let actionResult {
                Text(actionResult)
                    .font(.caption)
                    .foregroundColor(AppColors.textSecondary)
                    .lineLimit(5)
            }
        }
        .padding(12)
        .cardStyle()
    }

    private func tradingActionButton(_ text: String, icon: String, destructive: Bool = false) -> some View {
        Button {
            Task { await sendTradingAction(text) }
        } label: {
            HStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.caption2)
                Text(text)
                    .font(.caption)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background((destructive ? AppColors.error : AppColors.accent).opacity(0.15))
            .foregroundColor(destructive ? AppColors.error : AppColors.accent)
            .cornerRadius(8)
        }
        .disabled(isSendingAction)
    }

    private func sendTradingAction(_ text: String) async {
        guard !text.isEmpty else { return }
        isSendingAction = true
        actionResult = nil
        defer { isSendingAction = false }
        let request = AgentMessageRequest(agentId: "bighead", message: text)
        do {
            let response: CommandResponse = try await connection.apiClient.post("/api/commands/agent/message", body: request)
            if response.status == "ok" {
                actionResult = response.stdout ?? "Message sent to Big Head"
                actionMessage = ""
            } else {
                actionResult = response.error ?? "Unknown error"
            }
        } catch {
            actionResult = "Failed to send message"
        }
    }
    private func metric(_ label: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(.caption)
                .foregroundColor(AppColors.textTertiary)
            Text(value)
                .font(AppFont.mono(16, weight: .semibold))
                .foregroundColor(AppColors.textPrimary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(AppColors.surface)
        .cornerRadius(10)
    }

    private func statTile(_ label: String, _ value: String, color: Color) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.caption)
                .foregroundColor(AppColors.textTertiary)
            Text(value)
                .font(AppFont.mono(14, weight: .semibold))
                .foregroundColor(color)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(AppColors.surface)
        .cornerRadius(10)
    }

    private func money(_ value: Double?) -> String {
        guard let value else { return "-" }
        return String(format: "$%.2f", value)
    }

    private func moneySigned(_ value: Double?) -> String {
        guard let value else { return "-" }
        if value >= 0 {
            return String(format: "+$%.2f", value)
        }
        return String(format: "-$%.2f", abs(value))
    }

    private var chartPoints: [EquityChartPoint] {
        equityHistory.compactMap { point in
            guard let date = parseISODate(point.timestamp) else { return nil }
            return EquityChartPoint(date: date, equity: point.equity)
        }
        .sorted { $0.date < $1.date }
    }

    private func parseISODate(_ value: String) -> Date? {
        let formatterWithFractional = ISO8601DateFormatter()
        formatterWithFractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

        if let date = formatterWithFractional.date(from: value) {
            return date
        }

        return ISO8601DateFormatter().date(from: value)
    }
}

#Preview {
    TradingDashboardView()
}
