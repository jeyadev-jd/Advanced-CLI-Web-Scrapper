

# 🕸️ Advanced Python Web Scraper 🕸️

**A powerful, modern, and flexible command-line tool for downloading complete web pages and their assets with ease.**

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)![License](https://img.shields.io/badge/license-MIT-green.svg)![Status](https://img.shields.io/badge/status-maintained-brightgreen.svg)![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)

</div>

This isn't just another scraper. It's a robust utility designed to handle the modern web. Using **Playwright** for dynamic content rendering and **BeautifulSoup** for precise HTML parsing, this tool can archive websites, gather data, or create complete offline copies of online content.

---

### 🎬 Demo in Action

*(This is a placeholder for a GIF showing the scraper running in a terminal)*

---

## 🚀 Core Features

-   **🤖 Dynamic Content Handling**: Flawlessly renders pages that rely heavily on JavaScript, ensuring you get the content you see in your browser.
-   **📦 Complete Asset Archiving**: Intelligently discovers and downloads all linked assets, including CSS, JS, images, audio, and video files.
-   **⚙️ Powerful CLI**: A rich command-line interface lets you control every aspect of the scraping process.
-   **🕸️ Adjustable Crawl Depth**: You decide how deep to crawl. Scrape a single page or follow links to archive an entire section of a site.
-   **🎯 Precision URL Filtering**: Use include/exclude keywords to target exactly the content you need and avoid what you don't.
-   **🌐 Domain Lock**: Keep the scraper leashed to the original website's domain, preventing it from wandering off to external links.
-   **⚡ Concurrent & Fast**: Leverages a thread pool to download multiple assets simultaneously, significantly speeding up the process.
-   **📊 Detailed Session Reports**: Generates a `final_report.json` at the end of each session with comprehensive statistics and a list of any failed URLs.

---

## 🛠️ Installation & Setup

Getting started is simple. Just follow these steps, and you'll be scraping in minutes.

1.  **Clone or Download the Script**
    Save the code from `advanced_scraper.py` to your local machine.

2.  **Install Python Dependencies**
    Open your terminal and run the following command to install the necessary libraries:
    ```bash
    pip install requests beautifulsoup4 playwright
    ```

3.  **Install Playwright's Browser Files**
    This crucial step downloads the headless browser executable (Chromium) that Playwright needs to run.
    ```bash
    python -m playwright install chromium
    ```

---

## 🕹️ How to Use

The script is controlled entirely through the command line. Here is the basic syntax:

```bash
python advanced_scraper.py --url "YOUR_TARGET_URL" [OPTIONS]


### Command-Line Arguments

| Argument                | Flag                    | Description                                                                  | Default                  |
| ----------------------- | ----------------------- | ---------------------------------------------------------------------------- | ------------------------ |
| **URL**                 | `--url`                 | **(Required)** The starting URL to scrape.                                   | N/A                      |
| **Output Directory**    | `--output`              | The directory where downloaded files will be saved.                          | `./web_collection`       |
| **Worker Threads**      | `--workers`             | The number of concurrent threads for downloading assets.                     | `5`                      |
| **Download Delay**      | `--delay`               | Delay (in seconds) between downloading different pages.                      | `1`                      |
| **Crawl Depth**         | `--depth`               | How many link levels to follow from the start URL (`1` = only the main page). | `1`                      |
| **Include Keywords**    | `--include`             | Comma-separated keywords. Only URLs containing these will be scraped.        | None                     |
| **Exclude Keywords**    | `--exclude`             | Comma-separated keywords. URLs containing these will be ignored.             | None                     |
| **Stay on Domain**      | `--stay-within-domain`  | A flag to prevent the scraper from following external links.                 | Not set                  |

---

## ✨ Usage Examples

#### 1. Quick Scrape of a Single Page
Download a single page and all its assets into the default `web_collection` directory.
```bash
python advanced_scraper.py --url "https://quotes.toscrape.com/"

