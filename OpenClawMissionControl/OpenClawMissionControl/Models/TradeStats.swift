import Foundation

struct TradeStats: Codable {
    let totalTrades: Int
    let wins: Int
    let losses: Int
    let winRate: Int
    let totalPnl: Double
    let avgPnl: Double
    let biggestWin: Double
    let biggestLoss: Double
    let totalLongs: Int
    let totalShorts: Int
    let assetBreakdown: [AssetBreakdown]
}

struct AssetBreakdown: Codable, Identifiable {
    var id: String { asset }

    let asset: String
    let trades: Int
    let pnl: Double
    let winRate: Int
}

struct EquityPoint: Codable, Identifiable {
    var id: String { timestamp }

    let timestamp: String
    let equity: Double
    let total: Double?
    let unrealized: Double?
    let realized: Double?
}

struct EquityHistoryResponse: Codable {
    let points: [EquityPoint]
}
