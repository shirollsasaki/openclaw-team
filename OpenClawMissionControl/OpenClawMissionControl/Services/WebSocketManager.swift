import Combine
import Foundation
import UIKit

@MainActor
final class WebSocketManager: ObservableObject {
    @Published private(set) var isConnected: Bool = false
    @Published private(set) var lastEnvelope: WebSocketEnvelope? = nil

    private var baseURL: URL
    private var webSocketTask: URLSessionWebSocketTask? = nil
    private var receiveTask: Task<Void, Never>? = nil
    private var reconnectTask: Task<Void, Never>? = nil
    private var reconnectAttempt: Int = 0
    private var intentionallyDisconnected: Bool = false

    init(baseURL: URL) {
        self.baseURL = baseURL
        NotificationCenter.default.addObserver(
            forName: UIApplication.willEnterForegroundNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            Task { await self?.connect() }
        }

        NotificationCenter.default.addObserver(
            forName: UIApplication.didEnterBackgroundNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            Task { await self?.disconnect() }
        }
    }

    func updateBaseURL(_ url: URL) {
        baseURL = url
    }

    func connect() async {
        if isConnected { return }

        intentionallyDisconnected = false
        reconnectTask?.cancel()
        reconnectTask = nil

        var components = URLComponents(url: baseURL, resolvingAgainstBaseURL: true)
        let currentScheme = components?.scheme ?? ""
        components?.scheme = (currentScheme == "https") ? "wss" : "ws"
        components?.path = "/ws"

        guard let wsURL = components?.url else {
            isConnected = false
            return
        }

        let task = URLSession.shared.webSocketTask(with: wsURL)
        webSocketTask = task
        task.resume()

        isConnected = true
        reconnectAttempt = 0

        receiveTask?.cancel()
        receiveTask = Task { [weak self] in
            await self?.receiveLoop()
        }
    }

    func disconnect() async {
        intentionallyDisconnected = true
        reconnectTask?.cancel()
        reconnectTask = nil
        receiveTask?.cancel()
        receiveTask = nil
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil
        isConnected = false
    }

    private func scheduleReconnect() {
        if intentionallyDisconnected { return }
        if reconnectTask != nil { return }

        reconnectTask = Task { [weak self] in
            guard let self else { return }
            while !Task.isCancelled {
                let delaySeconds = min(30, Int(pow(2.0, Double(reconnectAttempt))))
                reconnectAttempt = min(reconnectAttempt + 1, 6)
                try? await Task.sleep(nanoseconds: UInt64(delaySeconds) * 1_000_000_000)
                await connect()
                if isConnected { return }
            }
        }
    }

    private func receiveLoop() async {
        guard let task = webSocketTask else {
            isConnected = false
            scheduleReconnect()
            return
        }

        while !Task.isCancelled {
            do {
                let message = try await task.receive()
                let data: Data?

                switch message {
                case .data(let d):
                    data = d
                case .string(let s):
                    data = s.data(using: .utf8)
                @unknown default:
                    data = nil
                }

                guard let data else { continue }
                if let decoded = try? JSONDecoder().decode(WebSocketEnvelope.self, from: data) {
                    lastEnvelope = decoded
                }
            } catch {
                isConnected = false
                scheduleReconnect()
                return
            }
        }
    }
}
