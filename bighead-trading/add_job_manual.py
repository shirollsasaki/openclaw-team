"""
Manual job entry tool - Add jobs to dashboard when found manually
"""
import csv
from datetime import datetime
import sys

def add_job():
    """Interactive tool to add a job to the dashboard"""
    
    print("="*70)
    print("ADD JOB TO DASHBOARD")
    print("="*70)
    print()
    
    # Collect info
    platform = input("Platform (Braintrust/Upwork/Fiverr): ").strip()
    agent = input("Agent(s) (comma-separated): ").strip()
    title = input("Job title: ").strip()
    url = input("Job URL: ").strip()
    budget = input("Budget (optional): ").strip()
    
    # Write to dashboard
    with open('platform-revenue-dashboard.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime('%Y-%m-%d'),
            platform,
            agent,
            title,
            url,
            'N',  # Proposal sent
            '',   # Proposal date
            'N',  # Client response
            '',   # Response date
            'N',  # Converted
            '',   # Conversion date
            budget if budget else '',  # Revenue amount
            'Prospecting',  # Status
            ''  # Notes
        ])
    
    print()
    print("✅ Added to dashboard!")
    print()

def update_job():
    """Update job status (proposal sent, response, converted)"""
    
    print("="*70)
    print("UPDATE JOB STATUS")
    print("="*70)
    print()
    
    # Show recent jobs
    with open('platform-revenue-dashboard.csv', 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if len(rows) <= 1:
        print("No jobs in dashboard yet.")
        return
    
    print("Recent jobs:")
    for i, row in enumerate(rows[-10:], 1):
        print(f"{i}. [{row['Status']}] {row['Lead Source']} ({row['Platform']}) - {row['Agent']}")
    print()
    
    choice = input("Job number to update (or 0 to cancel): ").strip()
    
    if choice == '0':
        return
    
    try:
        job_idx = len(rows) - 10 + int(choice) - 1
        job = rows[job_idx]
    except:
        print("Invalid choice")
        return
    
    print()
    print(f"Updating: {job['Lead Source']}")
    print()
    print("What to update?")
    print("1. Proposal sent")
    print("2. Client responded")
    print("3. Converted (won)")
    print("4. Lost")
    print("5. Update revenue amount")
    
    action = input("Choice (1-5): ").strip()
    
    if action == '1':
        job['Proposal Sent'] = 'Y'
        job['Proposal Date'] = datetime.now().strftime('%Y-%m-%d')
        job['Status'] = 'Proposal Sent'
    elif action == '2':
        job['Client Response'] = 'Y'
        job['Response Date'] = datetime.now().strftime('%Y-%m-%d')
        job['Status'] = 'Negotiating'
    elif action == '3':
        job['Converted'] = 'Y'
        job['Conversion Date'] = datetime.now().strftime('%Y-%m-%d')
        job['Status'] = 'Closed'
        revenue = input("Revenue amount ($): ").strip()
        if revenue:
            job['Revenue Amount'] = revenue
    elif action == '4':
        job['Status'] = 'Lost'
    elif action == '5':
        revenue = input("Revenue amount ($): ").strip()
        if revenue:
            job['Revenue Amount'] = revenue
    
    # Write back
    with open('platform-revenue-dashboard.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    
    print()
    print("✅ Updated!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'update':
        update_job()
    else:
        add_job()
