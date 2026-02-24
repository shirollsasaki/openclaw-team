import Foundation

struct TokenUsageResponse: Codable {
    let agents: [AgentTokenUsage]
    let total: TokenUsageTotal
}

struct AgentTokenUsage: Codable, Identifiable {
    var id: String { name }

    let name: String
    let model: String
    let totalTokens: Int
    let inputTokens: Int
    let outputTokens: Int
    let estimatedCost: Double
    let sessionCount: Int
}

struct TokenUsageTotal: Codable {
    let tokens: Int
    let estimatedCost: Double
}
