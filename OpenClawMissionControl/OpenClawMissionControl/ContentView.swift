import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            AgentDashboardView()
                .tabItem {
                    Label("Agents", systemImage: "person.3")
                }

            TradingDashboardView()
                .tabItem {
                    Label("Trading", systemImage: "chart.line.uptrend.xyaxis")
                }

            CronJobsView()
                .tabItem {
                    Label("Cron", systemImage: "clock")
                }

            TokenUsageView()
                .tabItem {
                    Label("Tokens", systemImage: "dollarsign.circle")
                }

            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gear")
                }
        }
        .tint(AppColors.accent)
        .toolbarBackground(AppColors.background, for: .tabBar)
        .toolbarBackground(.visible, for: .tabBar)
        .preferredColorScheme(.dark)
    }
}

#Preview {
    ContentView()
}
