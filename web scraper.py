import os
import sys
import subprocess
import json
import time
import re
import threading
import argparse
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# --- Playwright Installation Check ---
def ensure_playwright():
    """Check for Playwright and install if missing."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
            except Exception as e:
                if "Executable doesn't exist" in str(e):
                    print("📥 Installing Playwright browsers...")
                    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    except ImportError:
        print("📥 Installing Playwright...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])

# --- Main Scraper Class ---
class AdvancedWebScraper:
    def __init__(self, config):
        self.base_url = config['url']
        self.download_dir = Path(config['output'])
        self.max_workers = config['workers']
        self.delay = config['delay']
        self.max_depth = config['depth']
        self.include_keywords = config['include']
        self.exclude_keywords = config['exclude']
        self.stay_on_domain = config['stay_within_domain']
        
        self.visited_urls = set()
        self.failed_downloads = []
        self.stats = {
            'total_pages': 0, 'successful_pages': 0, 'failed_pages': 0,
            'total_files': 0, 'successful_files': 0, 'failed_files': 0,
            'start_time': None, 'end_time': None
        }
        self.lock = threading.Lock()

        ensure_playwright()
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        })

        print("🚀 Advanced Web Scraper Initialized")
        print(f"📁 Output Directory: {self.download_dir}")

    def is_valid_url(self, url, base_domain):
        """Check if a URL is valid and meets filtering criteria."""
        if not url or not isinstance(url, str):
            return False
        
        # Exclude common non-content links
        if any(url.startswith(p) for p in ['mailto:', 'tel:', 'javascript:']):
            return False

        # Apply domain scoping
        if self.stay_on_domain and urlparse(url).netloc != base_domain:
            return False
        
        # Apply keyword filters
        if self.include_keywords and not any(k in url for k in self.include_keywords):
            return False
        if self.exclude_keywords and any(k in url for k in self.exclude_keywords):
            return False
            
        return True

    def discover_links(self, url, depth):
        """Recursively discover links up to a max depth using Playwright."""
        if depth > self.max_depth or url in self.visited_urls:
            return set()

        with self.lock:
            if url in self.visited_urls:
                return set()
            self.visited_urls.add(url)
        
        print(f"🔍[{depth}] Discovering: {url}")

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Scroll to load dynamic content
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                links = page.evaluate("() => Array.from(document.querySelectorAll('a[href]'), a => a.href)")
                browser.close()
                
                base_domain = urlparse(self.base_url).netloc
                valid_links = {urljoin(url, link) for link in links if self.is_valid_url(urljoin(url, link), base_domain)}
                
                # Recursive discovery
                discovered = set(valid_links)
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = [executor.submit(self.discover_links, link, depth + 1) for link in valid_links]
                    for future in futures:
                        discovered.update(future.result())

                return discovered
        except Exception as e:
            print(f"❌ Discovery error on {url}: {e}")
            return set()

    def download_page_assets(self, page_url, page_index, total_pages):
        """Download a single page and all its assets."""
        try:
            response = self.session.get(page_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Create a directory for the page
            page_name = self.get_sanitized_name(page_url, soup)
            page_dir = self.download_dir / page_name
            page_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"\n📥 [{page_index}/{total_pages}] Downloading: {page_name}")
            
            # Save main HTML
            with open(page_dir / 'index.html', 'w', encoding='utf-8') as f:
                f.write(str(soup))
                
            # Find all assets
            assets = self._extract_assets(soup, page_url)
            print(f"   📦 Found {len(assets)} assets to download...")

            # Download assets concurrently
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                list(executor.map(lambda asset: self.download_single_asset(asset[1], page_dir / asset[0]), assets))

            with self.lock:
                self.stats['successful_pages'] += 1
                self.stats['total_files'] += len(assets)

        except Exception as e:
            print(f"   ❌ Failed to process {page_url}: {e}")
            self.failed_downloads.append(page_url)
            with self.lock:
                self.stats['failed_pages'] += 1

    def _extract_assets(self, soup, base_url):
        """Extract all asset URLs from a BeautifulSoup object."""
        asset_list = []
        # CSS
        for link in soup.find_all('link', {'rel': 'stylesheet'}):
            asset_list.append(('css', urljoin(base_url, link.get('href'))))
        # JavaScript
        for script in soup.find_all('script', {'src': True}):
            asset_list.append(('js', urljoin(base_url, script.get('src'))))
        # Images and Media
        for tag in soup.find_all(['img', 'source', 'audio', 'video']):
            for attr in ['src', 'data-src', 'srcset']:
                if src := tag.get(attr):
                    if attr == 'srcset':
                        urls = [urljoin(base_url, u.strip().split(' ')[0]) for u in src.split(',')]
                        asset_list.extend([('media', u) for u in urls])
                    else:
                        asset_list.append(('media', urljoin(base_url, src)))
        
        return list(dict.fromkeys(asset_list))

    def download_single_asset(self, url, target_dir):
        """Download a single asset file."""
        if not url or url in self.visited_urls:
            return False
            
        with self.lock:
            if url in self.visited_urls: return False
            self.visited_urls.add(url)
            
        try:
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # Create filename
            filename = os.path.basename(urlparse(url).path) or f"asset_{hash(url)}.dat"
            filepath = target_dir / re.sub(r'[^\w\-_\.]', '_', filename)
            
            # Ensure subdirectory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            with self.lock:
                self.stats['successful_files'] += 1
            return True
        except Exception:
            with self.lock:
                self.stats['failed_files'] += 1
            return False

    def get_sanitized_name(self, url, soup):
        """Create a clean, file-system-safe name from a URL or title."""
        if soup.title and soup.title.string:
            name = re.sub(r'[^\w\s-]', '', soup.title.string.strip())
            name = re.sub(r'\s+', '-', name).lower()
            if len(name) > 3: return name[:70]

        # Fallback to URL path
        path = urlparse(url).path
        name = re.sub(r'[^\w\-]', '', path.replace('/', '_'))
        return name[:70] or f"page_{abs(hash(url)) % 10000}"

    def run(self):
        """Main execution method."""
        print("="*50)
        self.stats['start_time'] = datetime.now().isoformat()
        
        try:
            # 1. Discover all pages
            print("🌐 PHASE 1: DISCOVERING PAGES")
            all_pages = self.discover_links(self.base_url, depth=0)
            all_pages.add(self.base_url) # Ensure the base URL is included
            self.stats['total_pages'] = len(all_pages)
            
            if not all_pages:
                print("❌ No pages found to scrape.")
                return

            print(f"🎯 Discovered {len(all_pages)} pages to process.")
            
            # 2. Download pages and assets
            print("\n📥 PHASE 2: DOWNLOADING")
            pages_to_download = list(all_pages)
            
            for i, page_url in enumerate(pages_to_download, 1):
                self.download_page_assets(page_url, i, len(pages_to_download))
                if i < len(pages_to_download):
                    time.sleep(self.delay)

        except KeyboardInterrupt:
            print("\n⚠️ Scraping interrupted by user.")
        finally:
            self.stats['end_time'] = datetime.now().isoformat()
            self.generate_report()

    def generate_report(self):
        """Generate and print a final report."""
        start = datetime.fromisoformat(self.stats['start_time'])
        end = datetime.fromisoformat(self.stats['end_time'])
        duration = (end - start).total_seconds()
        
        page_rate = (self.stats['successful_pages'] / max(self.stats['total_pages'], 1)) * 100
        file_rate = (self.stats['successful_files'] / max(self.stats['total_files'], 1)) * 100
        
        report = {
            'summary': {
                'total_pages_found': self.stats['total_pages'],
                'successful_pages': self.stats['successful_pages'],
                'failed_pages': self.stats['failed_pages'],
                'page_success_rate': f"{page_rate:.1f}%",
                'total_files': self.stats['total_files'],
                'successful_files': self.stats['successful_files'],
                'failed_files': self.stats['failed_files'],
                'file_success_rate': f"{file_rate:.1f}%",
                'duration_seconds': duration,
            },
            'failed_urls': self.failed_downloads,
            'config': {
                'url': self.base_url,
                'output': str(self.download_dir),
                'workers': self.max_workers,
                'depth': self.max_depth,
            }
        }
        
        with open(self.download_dir / 'final_report.json', 'w') as f:
            json.dump(report, f, indent=4)
            
        print("\n" + "="*50)
        print("🎉 SCRAPING COMPLETE!")
        print(f"📊 Pages: {self.stats['successful_pages']}/{self.stats['total_pages']} ({page_rate:.1f}%)")
        print(f"💾 Files: {self.stats['successful_files']}/{self.stats['total_files']} ({file_rate:.1f}%)")
        print(f"⏱️  Time: {int(duration // 60)}m {int(duration % 60)}s")
        print(f"📋 Report saved to: {self.download_dir / 'final_report.json'}")
        print("="*50)

# --- CLI Setup ---
def main():
    parser = argparse.ArgumentParser(description="Advanced Web Scraper")
    parser.add_argument('--url', required=True, help="Starting URL to scrape.")
    parser.add_argument('--output', default='./web_collection', help="Directory to save files.")
    parser.add_argument('--workers', type=int, default=5, help="Number of concurrent download threads.")
    parser.add_argument('--delay', type=float, default=1, help="Delay between page downloads.")
    parser.add_argument('--depth', type=int, default=1, help="How many link levels to follow.")
    parser.add_argument('--include', help="Comma-separated keywords to include in URLs.")
    parser.add_argument('--exclude', help="Comma-separated keywords to exclude from URLs.")
    parser.add_argument('--stay-within-domain', action='store_true', help="Only scrape pages on the same domain.")
    
    args = parser.parse_args()
    
    config = {
        'url': args.url,
        'output': args.output,
        'workers': args.workers,
        'delay': args.delay,
        'depth': args.depth,
        'include': args.include.split(',') if args.include else [],
        'exclude': args.exclude.split(',') if args.exclude else [],
        'stay_within_domain': args.stay_within_domain
    }
    
    scraper = AdvancedWebScraper(config)
    scraper.run()

if __name__ == "__main__":
    main()
