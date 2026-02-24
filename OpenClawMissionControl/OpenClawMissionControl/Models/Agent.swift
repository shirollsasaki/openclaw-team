import Foundation

struct Agent: Codable, Identifiable {
    var id: String { name }
    let name: String
    let model: String
    let status: String
    let lastActive: String?
    let sessionCount: Int
}

struct AgentsResponse: Codable {
    let agents: [Agent]
}
