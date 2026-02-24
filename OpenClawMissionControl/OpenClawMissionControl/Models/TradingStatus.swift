import Foundation

struct TradingStatus: Codable {
    let equity: Double?
    let unrealized: Double?
    let realized: Double?
    let total: Double?
    let openPositions: [Position]
    let recentTrades: [Trade]
    let botRunning: Bool
    let lastUpdate: String?
}

struct Position: Codable, Identifiable {
    var id: String { "\(asset)-\(side)-\(entry ?? 0)-\(sl ?? 0)" }

    let asset: String
    let side: String
    let entry: Double?
    let sl: Double?
    let tp: Double?
    let unrealized: Double?
    let flags: [String]?
}

struct Trade: Codable, Identifiable {
    var id: String { "\(entryTime ?? "")-\(asset ?? "")-\(direction ?? "")" }

    let entryTime: String?
    let exitTime: String?
    let asset: String?
    let direction: String?
    let entry: String?
    let exit: String?
    let sl: String?
    let tp: String?
    let size: String?
    let leverage: String?
    let pnl: String?
    let partialTaken: String?
    let breakevenMoved: String?
    let trailingActive: String?

    enum CodingKeys: String, CodingKey {
        case entryTime = "entry_time"
        case exitTime = "exit_time"
        case asset
        case direction
        case entry
        case exit
        case sl
        case tp
        case size
        case leverage
        case pnl
        case partialTaken = "partial_taken"
        case breakevenMoved = "breakeven_moved"
        case trailingActive = "trailing_active"
    }
}
