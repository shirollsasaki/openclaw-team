import Foundation
import Combine

enum ConnectionState: String {
    case connected
    case connecting
    case disconnected
    case error
}

@MainActor
final class ConnectionManager: ObservableObject {
    @Published private(set) var connectionState: ConnectionState = .disconnected
    @Published private(set) var lastUpdated: Date? = nil
    @Published var baseURLString: String

    private let baseURLKey = "openclaw.monitor.baseURL"

    private var cancellables: Set<AnyCancellable> = []

    private(set) var apiClient: APIClient
    private(set) var webSocketManager: WebSocketManager

    init() {
        let saved = UserDefaults.standard.string(forKey: baseURLKey)
        let defaultURL = saved ?? "http://localhost:3001"
        baseURLString = defaultURL

        let url = URL(string: defaultURL) ?? URL(string: "http://localhost:3001") ?? URL(fileURLWithPath: "/")
        apiClient = APIClient(baseURL: url)
        webSocketManager = WebSocketManager(baseURL: url)

        webSocketManager.$isConnected
            .receive(on: DispatchQueue.main)
            .sink { [weak self] connected in
                guard let self else { return }
                self.connectionState = connected ? .connected : .disconnected
            }
            .store(in: &cancellables)

        connectionState = .connecting
        Task { await webSocketManager.connect() }
    }

    func setBaseURL(_ newValue: String) {
        baseURLString = newValue
        UserDefaults.standard.set(newValue, forKey: baseURLKey)

        guard let url = URL(string: newValue) else {
            connectionState = .error
            return
        }

        apiClient.baseURL = url
        webSocketManager.updateBaseURL(url)
        Task { await webSocketManager.disconnect(); await webSocketManager.connect() }
    }

    func markUpdatedNow() {
        lastUpdated = Date()
    }
}
