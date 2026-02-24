"""
Competitor Tracking System
Track who's bidding on same jobs, their pricing, and success rates
"""
import csv
from datetime import datetime
from collections import defaultdict

class CompetitorTracker:
    def __init__(self):
        self.competitors_file = "competitors.csv"
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        """Create competitors file if it doesn't exist"""
        try:
            with open(self.competitors_file, 'r') as f:
                pass
        except FileNotFoundError:
            with open(self.competitors_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Date',
                    'Platform',
                    'Job URL',
                    'Competitor Name',
                    'Competitor Profile',
                    'Their Price',
                    'Our Price',
                    'Their Review Count',
                    'Did They Win',
                    'Notes'
                ])
    
    def add_competitor_sighting(self):
        """Add a competitor we saw on a job"""
        print("="*70)
        print("ADD COMPETITOR SIGHTING")
        print("="*70)
        print()
        
        platform = input("Platform: ").strip()
        job_url = input("Job URL: ").strip()
        comp_name = input("Competitor name/username: ").strip()
        comp_profile = input("Competitor profile URL: ").strip()
        their_price = input("Their bid/rate: ").strip()
        our_price = input("Our bid/rate (if applicable): ").strip()
        review_count = input("Their review count: ").strip()
        
        with open(self.competitors_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d'),
                platform,
                job_url,
                comp_name,
                comp_profile,
                their_price,
                our_price,
                review_count,
                '',  # Did they win (TBD)
                ''   # Notes
            ])
        
        print()
        print("✅ Competitor tracked!")
        print()
    
    def show_competitors(self):
        """Show competitor activity summary"""
        try:
            with open(self.competitors_file, 'r') as f:
                reader = csv.DictReader(f)
                data = list(reader)
        except:
            print("No competitor data yet.")
            return
        
        if not data:
            print("No competitor data yet.")
            return
        
        print("="*70)
        print("COMPETITOR ANALYSIS")
        print("="*70)
        print()
        
        # Count sightings per competitor
        comp_sightings = defaultdict(list)
        
        for row in data:
            comp_name = row['Competitor Name']
            comp_sightings[comp_name].append(row)
        
        print("📊 MOST ACTIVE COMPETITORS")
        print()
        
        sorted_comps = sorted(comp_sightings.items(), key=lambda x: len(x[1]), reverse=True)
        
        for comp_name, sightings in sorted_comps[:10]:
            count = len(sightings)
            
            # Calculate win rate if known
            wins = sum(1 for s in sightings if s['Did They Win'].lower() == 'yes')
            known_outcomes = sum(1 for s in sightings if s['Did They Win'])
            win_rate = (wins / known_outcomes * 100) if known_outcomes > 0 else 0
            
            # Average price
            prices = [s['Their Price'] for s in sightings if s['Their Price']]
            
            print(f"  {comp_name}")
            print(f"    Sightings: {count}")
            if known_outcomes > 0:
                print(f"    Win rate: {win_rate:.0f}% ({wins}/{known_outcomes})")
            if prices:
                print(f"    Typical bid: {prices[-1]}")  # Most recent
            print()
        
        # Pricing intelligence
        print("💰 PRICING INTELLIGENCE")
        print()
        
        # Group by platform
        platform_prices = defaultdict(list)
        
        for row in data:
            if row['Their Price'] and row['Their Price'].replace('$','').replace(',','').replace('.','').isdigit():
                try:
                    price = float(row['Their Price'].replace('$','').replace(',',''))
                    platform_prices[row['Platform']].append(price)
                except:
                    pass
        
        for platform, prices in platform_prices.items():
            if prices:
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)
                
                print(f"  {platform}:")
                print(f"    Average: ${avg_price:,.2f}")
                print(f"    Range: ${min_price:,.2f} - ${max_price:,.2f}")
                print()
        
        # Undercutting analysis
        print("⚠️  UNDERCUT ALERTS")
        print()
        
        undercuts = []
        for row in data:
            if row['Their Price'] and row['Our Price']:
                try:
                    their = float(row['Their Price'].replace('$','').replace(',',''))
                    ours = float(row['Our Price'].replace('$','').replace(',',''))
                    
                    if their < ours * 0.7:  # They're 30%+ cheaper
                        undercut_pct = (1 - their/ours) * 100
                        undercuts.append({
                            'comp': row['Competitor Name'],
                            'platform': row['Platform'],
                            'their': their,
                            'ours': ours,
                            'pct': undercut_pct
                        })
                except:
                    pass
        
        if undercuts:
            undercuts.sort(key=lambda x: x['pct'], reverse=True)
            for u in undercuts[:5]:
                print(f"  {u['comp']} on {u['platform']}: ${u['their']:,.2f} vs our ${u['ours']:,.2f} (-{u['pct']:.0f}%)")
        else:
            print("  No significant undercuts detected ✅")
        
        print()
        print("="*70)

def main():
    import sys
    
    tracker = CompetitorTracker()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'add':
        tracker.add_competitor_sighting()
    else:
        tracker.show_competitors()

if __name__ == "__main__":
    main()
