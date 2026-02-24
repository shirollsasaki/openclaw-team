import SwiftUI

/// Dark theme color constants for OpenClaw Mission Control
struct AppColors {
    // Backgrounds
    static let background = Color(hex: "#0D0D0D")
    static let card = Color(hex: "#1A1A1A")
    static let surface = Color(hex: "#242424")

    // Brand & Accent
    static let accent = Color(hex: "#007AFF")
    static let accentDim = Color(hex: "#004F9E")

    // Status
    static let success = Color(hex: "#30D158")
    static let warning = Color(hex: "#FF9F0A")
    static let error = Color(hex: "#FF453A")
    static let idle = Color(hex: "#636366")

    // Text
    static let textPrimary = Color.white
    static let textSecondary = Color(hex: "#EBEBF5").opacity(0.6)
    static let textTertiary = Color(hex: "#EBEBF5").opacity(0.3)

    // Borders
    static let border = Color(hex: "#FFFFFF").opacity(0.08)

    // Opus vs Sonnet model badge colors
    static let opusBadge = Color(hex: "#BF5AF2")
    static let sonnetBadge = Color(hex: "#007AFF")
}

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

/// Typography scale
struct AppFont {
    static func mono(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight, design: .monospaced)
    }

    static func display(_ size: CGFloat, weight: Font.Weight = .bold) -> Font {
        .system(size: size, weight: weight, design: .rounded)
    }
}

/// Reusable card background modifier
struct CardModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .background(AppColors.card)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(AppColors.border, lineWidth: 1)
            )
    }
}

extension View {
    func cardStyle() -> some View {
        self.modifier(CardModifier())
    }
}
