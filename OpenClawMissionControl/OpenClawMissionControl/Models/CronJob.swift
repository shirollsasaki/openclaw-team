import Foundation

struct CronJobsResponse: Codable {
    let jobs: [CronJob]
}

struct CronJob: Codable, Identifiable {
    let id: String
    let name: String
    let agent: String
    let schedule: CronSchedule?
    let enabled: Bool
    let lastRun: Int?
    let lastStatus: String?
    let nextRun: Int?
    let consecutiveErrors: Int
    let recentRuns: [CronRun]
}

struct CronSchedule: Codable {
    let expr: String?
}

struct CronRun: Codable, Identifiable {
    var id: String { startedAtMs.map(String.init) ?? UUID().uuidString }

    let startedAtMs: Int?
    let finishedAtMs: Int?
    let status: String?
    let error: String?
    let durationMs: Int?
}
