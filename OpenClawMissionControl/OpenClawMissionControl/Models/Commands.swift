import Foundation

struct CommandInfo: Codable, Identifiable {
    var id: String
    let method: String
    let path: String
    let label: String
}

struct CommandStatusResponse: Codable {
    let status: String
    let error: String?
}

struct CommandCronRunResponse: Codable {
    let status: String
    let stdout: String?
    let stderr: String?
    let error: String?
}

struct AgentMessageRequest: Encodable {
    let agentId: String
    let message: String
}

struct CommandResponse: Codable {
    let status: String
    let stdout: String?
    let stderr: String?
    let error: String?
}
