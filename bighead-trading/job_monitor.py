"""
Job Board Monitor - Tracks relevant jobs on Braintrust, Upwork, Fiverr
Runs 3x daily (10 AM, 2 PM, 6 PM IST) or on-demand
"""
import asyncio
import csv
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
import os

# Keywords to monitor
KEYWORDS = {
    'core': ['AI', 'automation', 'ops', 'strategy', 'research', 'content', 'marketing', 'sales', 'BD'],
    'crypto': ['crypto', 'web3', 'DeFi', 'DAO', 'blockchain'],
    'work_type': ['24/7', 'remote', 'fractional', 'consultant', 'advisor']
}

# Agent specializations for routing
AGENT_SPECIALIZATIONS = {
    'Monica': ['content', 'marketing', 'writing', 'social media', 'copywriting'],
    'Jared': ['GTM', 'growth', 'marketing', 'sales', 'BD', 'partnerships'],
    'Erlich': ['BD', 'sales', 'partnerships', 'deals', 'negotiation'],
    'Dinesh': ['research', 'analysis', 'strategy', 'competitive intelligence'],
    'Gilfoyle': ['technical', 'infrastructure', 'devops', 'security', 'blockchain'],
    'BigHead': ['data', 'analytics', 'scraping', 'automation', 'ops'],
    'Richard': ['strategy', 'product', 'founder', 'executive', 'vision']
}

class JobMonitor:
    def __init__(self):
        self.dashboard_file = "platform-revenue-dashboard.csv"
        self.jobs_cache_file = "jobs_seen.txt"
        self.seen_jobs = self.load_seen_jobs()
    
    def load_seen_jobs(self):
        """Load previously seen job IDs to avoid duplicates"""
        if os.path.exists(self.jobs_cache_file):
            with open(self.jobs_cache_file, 'r') as f:
                return set(line.strip() for line in f)
        return set()
    
    def save_seen_job(self, job_id):
        """Mark a job as seen"""
        self.seen_jobs.add(job_id)
        with open(self.jobs_cache_file, 'a') as f:
            f.write(f"{job_id}\n")
    
    def match_agent(self, job_title, job_description):
        """Determine which agent(s) should bid on this job"""
        text = f"{job_title} {job_description}".lower()
        
        matches = []
        for agent, keywords in AGENT_SPECIALIZATIONS.items():
            if any(kw.lower() in text for kw in keywords):
                matches.append(agent)
        
        if not matches:
            matches = ['Richard']  # Default to Richard for review
        
        return matches
    
    def calculate_relevance_score(self, job_title, job_description):
        """Score job relevance (0-100)"""
        text = f"{job_title} {job_description}".lower()
        
        score = 0
        
        # Core keywords
        for kw in KEYWORDS['core']:
            if kw.lower() in text:
                score += 15
        
        # Crypto keywords (bonus)
        for kw in KEYWORDS['crypto']:
            if kw.lower() in text:
                score += 10
        
        # Work type match
        for kw in KEYWORDS['work_type']:
            if kw.lower() in text:
                score += 5
        
        return min(score, 100)
    
    async def check_braintrust(self):
        """Check Braintrust for new jobs"""
        print("🔍 Checking Braintrust...")
        
        # Braintrust requires auth - would need API key or scraping
        # For now, return placeholder structure
        jobs = []
        
        # TODO: Implement Braintrust scraping/API
        # Would check: https://app.braintrust.com/jobs
        
        return jobs
    
    async def check_upwork(self):
        """Check Upwork for new jobs"""
        print("🔍 Checking Upwork...")
        
        jobs = []
        
        # Upwork RSS feeds for specific searches
        search_terms = [
            'AI automation',
            'crypto research',
            'web3 marketing',
            'strategy consultant'
        ]
        
        # TODO: Implement Upwork RSS parsing or API
        # Would use: https://www.upwork.com/ab/feed/jobs/rss?...
        
        return jobs
    
    async def check_fiverr(self):
        """Check Fiverr for buyer requests"""
        print("🔍 Checking Fiverr...")
        
        jobs = []
        
        # Fiverr buyer requests (requires seller account)
        # TODO: Implement Fiverr buyer request checking
        
        return jobs
    
    def format_alert(self, job):
        """Format job alert for Discord #ops"""
        agents = ", ".join([f"@{a}" for a in job['agents']])
        
        alert = f"""
🚨 **NEW JOB ALERT**

**Platform:** {job['platform']}
**Title:** {job['title']}
**Budget:** {job.get('budget', 'Not specified')}
**Relevance:** {job['score']}/100

**Recommended agents:** {agents}

**Link:** {job['url']}

**Description:**
{job['description'][:200]}...

---
"""
        return alert
    
    async def monitor_all(self):
        """Run full monitoring cycle across all platforms"""
        print("="*70)
        print(f"JOB MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
        print("="*70)
        print()
        
        all_jobs = []
        
        # Check each platform
        braintrust_jobs = await self.check_braintrust()
        upwork_jobs = await self.check_upwork()
        fiverr_jobs = await self.check_fiverr()
        
        all_jobs.extend(braintrust_jobs)
        all_jobs.extend(upwork_jobs)
        all_jobs.extend(fiverr_jobs)
        
        # Filter out already seen jobs
        new_jobs = [j for j in all_jobs if j['id'] not in self.seen_jobs]
        
        print(f"Found {len(all_jobs)} total jobs")
        print(f"New jobs: {len(new_jobs)}")
        print()
        
        if not new_jobs:
            print("✅ No new relevant jobs found")
            return []
        
        # Score and filter
        for job in new_jobs:
            job['score'] = self.calculate_relevance_score(job['title'], job['description'])
            job['agents'] = self.match_agent(job['title'], job['description'])
        
        # Filter by relevance score (min 30)
        relevant_jobs = [j for j in new_jobs if j['score'] >= 30]
        
        print(f"Relevant jobs (score >= 30): {len(relevant_jobs)}")
        print()
        
        # Sort by score
        relevant_jobs.sort(key=lambda x: x['score'], reverse=True)
        
        # Display alerts
        for job in relevant_jobs:
            print(self.format_alert(job))
            self.save_seen_job(job['id'])
            
            # Add to dashboard
            self.add_to_dashboard(job)
        
        return relevant_jobs
    
    def add_to_dashboard(self, job):
        """Add new lead to dashboard CSV"""
        with open(self.dashboard_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d'),
                job['platform'],
                ', '.join(job['agents']),
                job['title'],
                job['url'],
                'N',  # Proposal sent
                '',   # Proposal date
                'N',  # Client response
                '',   # Response date
                'N',  # Converted
                '',   # Conversion date
                '',   # Revenue amount
                'Prospecting',  # Status
                f"Score: {job['score']}"  # Notes
            ])

async def main():
    monitor = JobMonitor()
    await monitor.monitor_all()

if __name__ == "__main__":
    asyncio.run(main())
