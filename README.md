# Advanced Python Web Scraper

A powerful and flexible command-line tool for downloading complete web pages and their assets. This scraper uses Playwright to handle dynamic, JavaScript-rendered content and downloads all associated resources, including CSS, JavaScript files, images, and other media.

It is designed to be highly configurable, making it suitable for a wide range of scraping tasks, from archiving a single page to creating an offline copy of an entire website.

## Features

-   **Dynamic Content Handling**: Uses Playwright and a headless browser to accurately render pages that rely on JavaScript.
-   **Complete Asset Downloading**: Discovers and downloads all linked assets, including CSS, JavaScript, images, audio, and video files.
-   **Command-Line Interface**: Easy to use with clear command-line arguments to control its behavior.
-   **Crawl Depth Control**: Specify how many levels of links to follow from the starting URL.
-   **URL Filtering**: Include or exclude URLs based on keywords to fine-tune the scraping scope.
-   **Domain Scoping**: Optionally restrict the scraper to stay within the initial website's domain, preventing it from crawling external links.
-   **Concurrent Downloads**: Utilizes a thread pool to download multiple assets simultaneously for improved speed.
-   **Detailed Reporting**: Generates a `final_report.json` file at the end of each session with comprehensive statistics.

## Requirements

-   Python 3.7+
-   The following Python libraries:
    -   `requests`
    -   `beautifulsoup4`
    -   `playwright`

## Installation

1.  **Clone the repository or save the script:**
    Save the code as `advanced_scraper.py`.

2.  **Install the required Python libraries:**
    Open your terminal or command prompt and run:
    ```bash
    pip install requests beautifulsoup4 playwright
    ```

3.  **Install the Playwright browser files:**
    This command downloads the necessary headless browser executable (Chromium).
    ```bash
    python -m playwright install chromium
    ```

## How to Use

The script is run from the command line with various arguments to customize the scraping process.

### Basic Syntax

```bash
python advanced_scraper.py --url "YOUR_TARGET_URL" [OPTIONS]
