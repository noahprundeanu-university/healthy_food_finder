from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import selenium for JavaScript-rendered pages (required for HEB)
try:
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    try:
        from webdriver_manager.firefox import GeckoDriverManager
        WEBDRIVER_MANAGER_AVAILABLE = True
    except ImportError:
        WEBDRIVER_MANAGER_AVAILABLE = False
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    WEBDRIVER_MANAGER_AVAILABLE = False
    print("ERROR: Selenium not installed. Install with: pip install selenium webdriver-manager")

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Set to True to use mock data for development/testing
# Real scraping uses Selenium with browser emulation
USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'False').lower() == 'true'

# Default filters for unhealthy ingredients
DEFAULT_FILTERS = [
    "seed oil", "vegetable oil", "canola oil", "soybean oil", "corn oil",
    "sunflower oil", "safflower oil", "rapeseed oil", "palm oil",
    "high fructose corn syrup", "hfcs", "artificial sweetener",
    "artificial flavor", "artificial color", "red 40", "yellow 5", "blue 1",
    "sodium nitrite", "sodium nitrate", "bht", "bha", "tbhq",
    "monosodium glutamate", "msg", "carrageenan", "polysorbate"
]

# In-memory storage (can be replaced with a database)
user_filters = {}
product_cache = {}
cache_expiry = {}

def normalize_text(text):
    """Normalize text for comparison"""
    if not text:
        return ""
    return text.lower().strip()

def check_ingredients(ingredients_text, filters):
    """Check if ingredients contain any filtered items"""
    if not ingredients_text:
        return True  # If no ingredients listed, don't filter out
    
    normalized_ingredients = normalize_text(ingredients_text)
    
    for filter_term in filters:
        if normalize_text(filter_term) in normalized_ingredients:
            return False  # Contains filtered ingredient
    
    return True  # Passes all filters

def get_mock_products(search_term, limit=20):
    """Generate mock products for testing"""
    mock_products = [
        {
            'name': 'Organic Free-Range Chicken Breast',
            'price': '$8.99/lb',
            'url': 'https://www.heb.com/product-detail/organic-chicken-breast',
            'image': 'https://via.placeholder.com/300x300?text=Chicken',
            'ingredients': 'Organic chicken breast',
            'store': 'HEB'
        },
        {
            'name': 'Fresh Wild-Caught Salmon',
            'price': '$12.99/lb',
            'url': 'https://www.heb.com/product-detail/salmon',
            'image': 'https://via.placeholder.com/300x300?text=Salmon',
            'ingredients': 'Wild-caught salmon',
            'store': 'HEB'
        },
        {
            'name': 'Organic Whole Milk',
            'price': '$4.99',
            'url': 'https://www.heb.com/product-detail/organic-milk',
            'image': 'https://via.placeholder.com/300x300?text=Milk',
            'ingredients': 'Organic whole milk',
            'store': 'HEB'
        },
        {
            'name': 'Sourdough Bread',
            'price': '$3.99',
            'url': 'https://www.heb.com/product-detail/sourdough',
            'image': 'https://via.placeholder.com/300x300?text=Bread',
            'ingredients': 'Organic flour, water, sea salt, sourdough starter',
            'store': 'HEB'
        },
        {
            'name': 'Organic Baby Spinach',
            'price': '$3.49',
            'url': 'https://www.heb.com/product-detail/spinach',
            'image': 'https://via.placeholder.com/300x300?text=Spinach',
            'ingredients': 'Organic baby spinach',
            'store': 'HEB'
        },
        {
            'name': 'Processed Cheese Slices',
            'price': '$2.99',
            'url': 'https://www.heb.com/product-detail/cheese',
            'image': 'https://via.placeholder.com/300x300?text=Cheese',
            'ingredients': 'Cheese, canola oil, sodium phosphate, artificial flavor',
            'store': 'HEB'
        },
        {
            'name': 'White Bread',
            'price': '$1.99',
            'url': 'https://www.heb.com/product-detail/white-bread',
            'image': 'https://via.placeholder.com/300x300?text=White+Bread',
            'ingredients': 'Enriched flour, high fructose corn syrup, soybean oil, preservatives',
            'store': 'HEB'
        }
    ]
    
    # Filter mock products based on search term
    filtered = [p for p in mock_products if search_term.lower() in p['name'].lower() or 
                search_term.lower() in p.get('ingredients', '').lower()]
    
    return filtered[:limit] if filtered else mock_products[:limit]

def create_selenium_driver():
    """Create a Selenium WebDriver using Firefox/LibreWolf with proper browser emulation"""
    if not SELENIUM_AVAILABLE:
        raise Exception("Selenium is not installed. Run: pip install selenium webdriver-manager")
    
    firefox_options = FirefoxOptions()
    # Always use headless mode to avoid opening visible browser windows
    # Headless is required for server environments
    firefox_options.add_argument('--headless')
    print("Using headless mode")
    
    # Stealth options to avoid detection
    firefox_options.set_preference("dom.webdriver.enabled", False)
    firefox_options.set_preference("useAutomationExtension", False)
    
    # Realistic user agent (use a more common one)
    firefox_options.set_preference("general.useragent.override", 
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0")
    
    # Accept language
    firefox_options.set_preference("intl.accept_languages", "en-US,en")
    
    # Window size
    firefox_options.set_preference("browser.window.size", "1920,1080")
    
    # Additional stealth preferences
    firefox_options.set_preference("privacy.trackingprotection.enabled", False)
    firefox_options.set_preference("media.navigator.permission.disabled", True)
    firefox_options.set_preference("dom.push.enabled", False)
    
    # Try to find Firefox or LibreWolf binary
    firefox_binary_paths = [
        '/usr/bin/firefox',
        '/usr/bin/librewolf',
        '/usr/local/bin/firefox',
        '/usr/local/bin/librewolf',
        os.path.expanduser('~/.local/bin/firefox'),
        os.path.expanduser('~/.local/bin/librewolf'),
    ]
    
    firefox_binary = None
    for path in firefox_binary_paths:
        if os.path.exists(path):
            firefox_binary = path
            print(f"Found Firefox/LibreWolf at: {path}")
            break
    
    if firefox_binary:
        firefox_options.binary_location = firefox_binary
    
    try:
        if WEBDRIVER_MANAGER_AVAILABLE:
            service = FirefoxService(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=firefox_options)
        else:
            # Try to use system geckodriver
            driver = webdriver.Firefox(options=firefox_options)
        
        # Execute script to hide webdriver property
        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        return driver
    except Exception as e:
        error_msg = f"Failed to create Firefox driver: {e}."
        if not firefox_binary:
            error_msg += " Firefox/LibreWolf not found. Install with: sudo apt install firefox (or download LibreWolf)"
        else:
            error_msg += " Make sure geckodriver is installed."
        raise Exception(error_msg)

def scrape_heb_product_selenium(search_term, limit=20):
    """Scrape HEB using Selenium with browser emulation"""
    import time
    
    driver = None
    start_time = time.time()
    max_total_time = 25  # Maximum 25 seconds total
    
    def check_timeout():
        if time.time() - start_time > max_total_time:
            raise TimeoutError("Scraping operation timed out")
    
    try:
        driver = create_selenium_driver()
        # Set page load timeout
        driver.set_page_load_timeout(12)
        driver.implicitly_wait(2)  # Reduce implicit wait
        
        search_url = f"https://www.heb.com/search/?q={search_term.replace(' ', '+')}"
        
        print(f"Loading HEB search page: {search_url}")
        try:
            driver.get(search_url)
        except Exception as e:
            print(f"Page load timeout or error: {e}")
            # Continue anyway - page might have partially loaded
        
        check_timeout()
        
        # Wait for page to load and bypass Incapsula challenge
        # Incapsula may need more time to verify
        time.sleep(3)  # Increased wait for Incapsula challenge
        
        # Check if we're blocked by Incapsula
        page_source_check = driver.page_source
        if 'Incapsula' in page_source_check[:1000]:
            print("Detected Incapsula challenge, waiting for it to complete...")
            # Wait longer and try to interact with page
            time.sleep(5)
            check_timeout()
            
            # Try scrolling to trigger any lazy loading or verification
            try:
                driver.execute_script("window.scrollTo(0, 100);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
            except:
                pass
        
        check_timeout()
        
        # Try to wait for product elements with multiple strategies
        products = []
        max_wait = 15
        
        # Skip element waiting - go straight to page source parsing (faster)
        print("Parsing page source directly (faster approach)...")
        product_elements = []  # Skip element-based extraction for speed
        
        # If we only found one element, it might be a container - try to find children
        if len(product_elements) == 1:
            print("Only one element found, looking for child product elements...")
            try:
                # Try to find child elements that might be individual products
                child_selectors = [
                    "article",
                    "[data-testid*='product']",
                    "[class*='product']",
                    "a[href*='/product']",
                    "a[href*='/p/']",
                ]
                for child_selector in child_selectors:
                    children = product_elements[0].find_elements(By.CSS_SELECTOR, child_selector)
                    if children and len(children) > 1:
                        product_elements = children
                        print(f"Found {len(children)} child product elements")
                        break
            except:
                pass
        
        # Parse page source for product links (primary method - faster)
        check_timeout()
        
        # Get page source and check if we're blocked
        page_source = driver.page_source
        print(f"Page source length: {len(page_source)} characters")
        
        # Check if page loaded properly (not just Incapsula block page)
        if len(page_source) < 1000 or 'Incapsula' in page_source[:500]:
            print("Warning: Page may be blocked by Incapsula. Waiting longer and retrying...")
            # Wait longer for Incapsula challenge to complete
            time.sleep(5)
            check_timeout()
            page_source = driver.page_source
            print(f"After wait, page source length: {len(page_source)} characters")
            
            # Check again
            if 'Incapsula' in page_source[:1000]:
                print("ERROR: Still blocked by Incapsula. Page may require manual verification.")
                # Try scrolling to trigger any lazy loading
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(2)
                    page_source = driver.page_source
                except:
                    pass
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Look for product links - HEB uses various patterns
        product_link_patterns = [
            r'/product/',
            r'/p/',
            r'/shop/product',
            r'/product-detail',
        ]
        
        all_product_links = []
        for pattern in product_link_patterns:
            links = soup.find_all('a', href=re.compile(pattern, re.I))
            all_product_links.extend(links)
        
        # Remove duplicates based on href
        seen_urls = set()
        unique_links = []
        for link in all_product_links:
            href = link.get('href', '')
            if href and href not in seen_urls:
                seen_urls.add(href)
                unique_links.append(link)
        
        print(f"Found {len(unique_links)} unique product links in page source")
        
        # If no links found and page seems blocked, try alternative extraction
        if len(unique_links) == 0:
            print("No product links found. Trying alternative extraction methods...")
            # Try to find any links that might be products
            all_links = soup.find_all('a', href=True)
            print(f"Total links on page: {len(all_links)}")
            
            # Look for links with product-like characteristics
            for link in all_links[:100]:
                href = link.get('href', '')
                link_text = link.get_text(strip=True)
                
                # Skip obvious non-product links
                if any(skip in href.lower() for skip in ['/cart', '/account', '/help', '/store', '/deals', '/recipes', '/categories']):
                    continue
                
                # Look for links that might be products
                if href and len(href) > 5 and len(link_text) > 5 and len(link_text) < 200:
                    # Check if it's not just navigation text
                    if not any(nav in link_text.lower() for nav in ['shop', 'cart', 'account', 'help', 'menu', 'search', 'browse']):
                        unique_links.append(link)
                        if len(unique_links) >= limit:
                            break
            
            print(f"Found {len(unique_links)} potential product links via alternative method")
        
        # Extract products from links (with timeout checks)
        for link in unique_links[:limit*2]:
            check_timeout()  # Check timeout periodically
            try:
                # Get product URL
                url = link.get('href', '')
                if not url:
                    continue
                if not url.startswith('http'):
                    url = 'https://www.heb.com' + url
                
                # Find product name - try link text first
                name = link.get_text(strip=True)
                
                # If link text is empty or too short, look in parent/sibling elements
                if not name or len(name) < 3:
                    # Walk up the DOM tree to find name
                    parent = link.parent
                    for _ in range(3):  # Check up to 3 levels up
                        if parent:
                            # Look for headings or spans with product name
                            name_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'span', 'div'], 
                                                   class_=re.compile(r'name|title|product', re.I))
                            if name_elem:
                                name = name_elem.get_text(strip=True)
                                if name and len(name) > 3:
                                    break
                            # Try any heading
                            if not name or len(name) < 3:
                                heading = parent.find(['h1', 'h2', 'h3', 'h4'])
                                if heading:
                                    name = heading.get_text(strip=True)
                                    if name and len(name) > 3:
                                        break
                            parent = parent.parent if hasattr(parent, 'parent') else None
                
                # Clean up name - take first line, remove extra whitespace
                if name:
                    name = ' '.join(name.split()[:20])  # Limit to first 20 words
                    if len(name) > 200:
                        name = name[:200] + '...'
                
                if not name or len(name) < 3:
                    continue
                
                # Find price - look in the same container as the link
                price = 'N/A'
                try:
                    # Find parent container
                    container = link.find_parent(['article', 'div', 'li'])
                    if container:
                        # Look for price patterns
                        price_text = container.get_text()
                        # Match price patterns like $4.99, $1.98, etc.
                        price_match = re.search(r'\$[\d,]+\.?\d{0,2}', price_text)
                        if price_match:
                            price = price_match.group(0)
                except:
                    pass
                
                # Find image
                image = ''
                try:
                    img = link.find('img')
                    if not img:
                        container = link.find_parent(['article', 'div'])
                        if container:
                            img = container.find('img')
                    if img:
                        image = img.get('src', img.get('data-src', ''))
                        if image and not image.startswith('http'):
                            image = 'https://www.heb.com' + image
                except:
                    pass
                
                product = {
                    'name': name,
                    'price': price,
                    'url': url,
                    'image': image,
                    'ingredients': '',
                    'store': 'HEB'
                }
                
                # Avoid duplicates
                if not any(p['name'].lower() == product['name'].lower() or 
                          p['url'] == product['url'] for p in products):
                    products.append(product)
                    print(f"Extracted product from link: {name[:60]}...")
                    
                if len(products) >= limit:
                    break
            except Exception as e:
                print(f"Error extracting product from link: {e}")
                continue
        else:
            # Parse found elements
            print(f"Parsing {len(product_elements)} product elements...")
            for i, element in enumerate(product_elements[:limit*2]):  # Get more to filter later
                try:
                    # Skip if element is too large (likely a container)
                    try:
                        element_text = element.text.strip()
                        if len(element_text) > 1000:  # Too much text = probably a container
                            print(f"Element {i}: Skipping - too large (container?)")
                            continue
                    except:
                        pass
                    
                    # Try to get product name - look for specific HEB patterns
                    name = None
                    
                    # Method 1: Look for links with product URLs
                    try:
                        links = element.find_elements(By.CSS_SELECTOR, "a[href*='/product'], a[href*='/p/']")
                        if links:
                            link_text = links[0].text.strip()
                            if link_text and len(link_text) > 3 and len(link_text) < 200:
                                name = link_text.split('\n')[0].strip()
                    except:
                        pass
                    
                    # Method 2: Look for headings (h1-h4) which often contain product names
                    if not name:
                        try:
                            for tag in ['h1', 'h2', 'h3', 'h4']:
                                headings = element.find_elements(By.TAG_NAME, tag)
                                if headings:
                                    heading_text = headings[0].text.strip()
                                    if heading_text and len(heading_text) > 3 and len(heading_text) < 200:
                                        name = heading_text.split('\n')[0].strip()
                                        break
                        except:
                            pass
                    
                    # Method 3: Get element HTML and parse with BeautifulSoup
                    if not name:
                        try:
                            element_html = element.get_attribute('outerHTML')
                            soup = BeautifulSoup(element_html, 'html.parser')
                            
                            # Try to find name in various places
                            name_selectors = [
                                soup.find(['h1', 'h2', 'h3', 'h4']),
                                soup.find('a', href=re.compile(r'/product|/p/', re.I)),
                                soup.find(['span', 'div'], class_=re.compile(r'name|title|product-name', re.I)),
                                soup.find('a'),
                            ]
                            
                            for name_elem in name_selectors:
                                if name_elem:
                                    name_text = name_elem.get_text(strip=True)
                                    if name_text and len(name_text) > 3 and len(name_text) < 200:
                                        name = name_text.split('\n')[0].strip()
                                        break
                        except Exception as e:
                            print(f"Error parsing element HTML: {e}")
                            continue
                    
                    # Method 4: Last resort - use first line of element text
                    if not name:
                        try:
                            element_text = element.text.strip()
                            if element_text:
                                first_line = element_text.split('\n')[0].strip()
                                # Only use if it looks like a product name (not too long, has letters)
                                if len(first_line) > 3 and len(first_line) < 200 and any(c.isalpha() for c in first_line):
                                    name = first_line
                        except:
                            pass
                    
                    # Method 2: Get element HTML and parse with BeautifulSoup
                    if not name or len(name) < 3:
                        try:
                            element_html = element.get_attribute('outerHTML')
                            soup = BeautifulSoup(element_html, 'html.parser')
                            
                            # Try multiple ways to find name
                            name_selectors = [
                                soup.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'name|title|product-name', re.I)),
                                soup.find('a', class_=re.compile(r'name|title', re.I)),
                                soup.find(['span', 'div'], class_=re.compile(r'name|title|product-name', re.I)),
                                soup.find(['h1', 'h2', 'h3', 'h4']),
                                soup.find('a'),
                            ]
                            
                            for name_elem in name_selectors:
                                if name_elem:
                                    name_text = name_elem.get_text(strip=True)
                                    if name_text and len(name_text) > 3 and len(name_text) < 200:
                                        name = name_text.split('\n')[0].strip()
                                        break
                        except Exception as e:
                            print(f"Error parsing element HTML: {e}")
                            continue
                    
                    if not name or len(name) < 3:
                        print(f"Element {i}: Could not extract product name")
                        continue
                    
                    print(f"Element {i}: Found product name: {name[:50]}...")
                    
                    # Find price - try multiple methods
                    price = 'N/A'
                    try:
                        # Try to find price in element directly
                        price_elements = element.find_elements(By.CSS_SELECTOR, "[class*='price'], [class*='cost'], [class*='amount'], [data-testid*='price']")
                        if price_elements:
                            price = price_elements[0].text.strip()
                        else:
                            # Fall back to BeautifulSoup parsing
                            if 'soup' in locals():
                                price_elem = soup.find(['span', 'div'], class_=re.compile(r'price|cost|amount', re.I))
                                if price_elem:
                                    price = price_elem.get_text(strip=True)
                    except:
                        pass
                    
                    # Find URL - try multiple methods
                    url = ''
                    try:
                        # Try to find link in element directly
                        link_elements = element.find_elements(By.TAG_NAME, 'a')
                        if link_elements:
                            url = link_elements[0].get_attribute('href')
                        else:
                            # Fall back to BeautifulSoup
                            if 'soup' in locals():
                                link = soup.find('a', href=True)
                                if link:
                                    url = link.get('href', '')
                        
                        if url and not url.startswith('http'):
                            url = 'https://www.heb.com' + url
                    except:
                        pass
                    
                    # Find image - try multiple methods
                    image = ''
                    try:
                        # Try to find image in element directly
                        img_elements = element.find_elements(By.TAG_NAME, 'img')
                        if img_elements:
                            image = img_elements[0].get_attribute('src') or img_elements[0].get_attribute('data-src')
                        else:
                            # Fall back to BeautifulSoup
                            if 'soup' in locals():
                                img = soup.find('img', src=True)
                                if img:
                                    image = img.get('src', img.get('data-src', ''))
                        
                        if image and not image.startswith('http'):
                            image = 'https://www.heb.com' + image
                    except:
                        pass
                    
                    product = {
                        'name': name,
                        'price': price,
                        'url': url,
                        'image': image,
                        'ingredients': '',
                        'store': 'HEB'
                    }
                    
                    # Avoid duplicates
                    if not any(p['name'].lower() == product['name'].lower() for p in products):
                        products.append(product)
                        print(f"Added product: {name[:50]}... (Price: {price}, URL: {url[:50] if url else 'N/A'}...)")
                    else:
                        print(f"Skipped duplicate: {name[:50]}...")
                        
                except Exception as e:
                    print(f"Error parsing element: {e}")
                    continue
        
        elapsed = time.time() - start_time
        print(f"Total products extracted: {len(products)} (took {elapsed:.1f}s)")
        if products:
            print(f"Sample product: {products[0]}")
        return products[:limit]
        
    except TimeoutError:
        print(f"Scraping operation timed out after {max_total_time} seconds")
        return []
    except Exception as e:
        print(f"Selenium scraping error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def scrape_heb_product(search_term, limit=20):
    """
    Scrape HEB website for products using Selenium browser emulation
    """
    if USE_MOCK_DATA:
        return get_mock_products(search_term, limit)
    
    if not SELENIUM_AVAILABLE:
        print("ERROR: Selenium not available. Install with: pip install selenium webdriver-manager")
        return []
    
    # Use Selenium for real scraping
    products = scrape_heb_product_selenium(search_term, limit)
    
    print(f"Scraped {len(products)} products from HEB")
    
    # Filter products to ensure they're relevant to the search term
    # But be lenient - if HEB returned them, they're probably relevant
    if products:
        search_terms = search_term.lower().split()
        relevant_products = []
        
        for product in products:
            product_name_lower = product.get('name', '').lower()
            # Check if any search term appears in the product name
            if any(term in product_name_lower for term in search_terms if len(term) > 2):
                relevant_products.append(product)
            # Also include if the full search term is in the name
            elif search_term.lower() in product_name_lower:
                relevant_products.append(product)
            # If search term is short or we have few results, include all products
            # (HEB's search is usually good, so trust their results)
            elif len(search_term) < 4 or len(products) <= 5:
                relevant_products.append(product)
        
        print(f"After filtering: {len(relevant_products)} relevant products (out of {len(products)} total)")
        # Return relevant products if found, otherwise return all products (they might still be valid)
        return relevant_products[:limit] if relevant_products else products[:limit]
    
    print("No products found")
    return []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
        'Referer': 'https://www.heb.com/',
    }
    
    products = []
    
    # Strategy 1: Try HEB's various API endpoints
    api_endpoints = [
        'https://www.heb.com/commerce-api/v1/product/search',
        'https://api.heb.com/v1/products/search',
        'https://www.heb.com/api/products/search',
        'https://www.heb.com/shop/api/products/search',
    ]
    
    for api_url in api_endpoints:
        try:
            params = {
                'q': search_term,
                'query': search_term,
                'searchTerm': search_term,
                'page': 1,
                'pageSize': limit,
                'limit': limit
            }
            api_response = requests.get(api_url, headers=headers, params=params, timeout=10)
            
            if api_response.status_code == 200:
                try:
                    data = api_response.json()
                    # Try common JSON structures
                    items = data.get('products', data.get('items', data.get('results', data.get('data', []))))
                    if isinstance(items, dict):
                        items = items.get('products', items.get('items', []))
                    
                    for item in items[:limit*2]:
                        if not isinstance(item, dict):
                            continue
                        product = {
                            'name': item.get('name', item.get('productName', item.get('title', item.get('displayName', '')))),
                            'price': item.get('price', item.get('salePrice', item.get('regularPrice', item.get('currentPrice', 'N/A')))),
                            'url': item.get('url', item.get('productUrl', item.get('link', item.get('productLink', '')))),
                            'image': item.get('image', item.get('imageUrl', item.get('thumbnail', item.get('thumbnailUrl', '')))),
                            'ingredients': item.get('ingredients', item.get('ingredientList', '')),
                            'store': 'HEB'
                        }
                        if product['name'] and len(product['name']) > 3:
                            # Format price if it's a number
                            if isinstance(product['price'], (int, float)):
                                product['price'] = f"${product['price']:.2f}"
                            # Avoid duplicates
                            if not any(p['name'].lower() == product['name'].lower() for p in products):
                                products.append(product)
                    
                    if products:
                        # Filter for relevance before returning
                        search_terms = search_term.lower().split()
                        relevant = [p for p in products if any(term in p['name'].lower() for term in search_terms if len(term) > 2) or search_term.lower() in p['name'].lower()]
                        if relevant:
                            return relevant[:limit]
                        return products[:limit]
                except (json.JSONDecodeError, KeyError, AttributeError) as e:
                    print(f"JSON parsing failed for {api_url}: {e}")
                    continue
        except Exception as e:
            print(f"API attempt failed for {api_url}: {e}")
            continue
    
    # Strategy 2: Try HTML scraping with multiple URL patterns
    # Note: HEB uses Incapsula bot protection, so this may not work
    search_urls = [
        f"https://www.heb.com/search/?q={search_term}",
        f"https://www.heb.com/shop/search?q={search_term}",
        f"https://www.heb.com/products?q={search_term}",
    ]
    
    for search_url in search_urls:
        try:
            # Use session to maintain cookies
            session = requests.Session()
            session.headers.update(headers)
            
            # First, visit the homepage to get cookies
            try:
                session.get('https://www.heb.com', timeout=5)
            except:
                pass
            
            response = session.get(search_url, timeout=15, allow_redirects=True)
            
            if response.status_code != 200:
                continue
            
            # Check if we got blocked by Incapsula
            if 'Incapsula' in response.text or len(response.content) < 500:
                print(f"Blocked by bot protection for {search_url}")
                continue
            
            # Check if response contains JSON data in script tags
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for JSON data in script tags (common pattern)
            script_tags = soup.find_all('script', type=re.compile(r'application/json|application/ld\+json'))
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    # Try to extract products from structured data
                    if isinstance(data, dict):
                        items = data.get('@graph', data.get('itemListElement', data.get('products', [])))
                        for item in items:
                            if isinstance(item, dict):
                                name = item.get('name', item.get('title', ''))
                                if name:
                                    product = {
                                        'name': name,
                                        'price': item.get('offers', {}).get('price', 'N/A') if isinstance(item.get('offers'), dict) else 'N/A',
                                        'url': item.get('url', item.get('@id', '')),
                                        'image': item.get('image', item.get('thumbnailUrl', '')),
                                        'ingredients': '',
                                        'store': 'HEB'
                                    }
                                    if product['url'] and not product['url'].startswith('http'):
                                        product['url'] = 'https://www.heb.com' + product['url']
                                    # Validate product before adding
                                    if product['name'] and len(product['name']) > 3:
                                        # Avoid duplicates
                                        if not any(p['name'].lower() == product['name'].lower() for p in products):
                                            products.append(product)
                except (json.JSONDecodeError, AttributeError):
                    continue
            
            # Strategy 3: HTML parsing with multiple selector patterns
            # Try various common e-commerce patterns
            selectors = [
                {'tag': 'div', 'attrs': {'class': re.compile(r'product', re.I)}},
                {'tag': 'div', 'attrs': {'class': re.compile(r'product-item', re.I)}},
                {'tag': 'div', 'attrs': {'class': re.compile(r'product-card', re.I)}},
                {'tag': 'article', 'attrs': {'class': re.compile(r'product', re.I)}},
                {'tag': 'li', 'attrs': {'class': re.compile(r'product', re.I)}},
                {'tag': 'div', 'attrs': {'data-product-id': True}},
                {'tag': 'div', 'attrs': {'data-sku': True}},
            ]
            
            for selector in selectors:
                product_elements = soup.find_all(selector['tag'], selector['attrs'])[:limit*2]
                if product_elements:
                    for element in product_elements:
                        try:
                            # Try to find product name
                            name = None
                            for tag in ['h1', 'h2', 'h3', 'h4', 'a']:
                                name_elem = element.find(tag, class_=re.compile(r'name|title|product-name', re.I))
                                if not name_elem:
                                    name_elem = element.find(tag)
                                if name_elem:
                                    name = name_elem.get_text(strip=True)
                                    if name and len(name) > 3:
                                        break
                            
                            if not name:
                                continue
                            
                            # Try to find price
                            price = 'N/A'
                            price_elem = element.find(['span', 'div', 'p'], class_=re.compile(r'price|cost|amount', re.I))
                            if price_elem:
                                price_text = price_elem.get_text(strip=True)
                                if '$' in price_text or re.search(r'\d+\.\d{2}', price_text):
                                    price = price_text
                            
                            # Try to find link
                            url = ''
                            link_elem = element.find('a', href=True)
                            if link_elem:
                                url = link_elem['href']
                                if url and not url.startswith('http'):
                                    url = 'https://www.heb.com' + url
                            
                            # Try to find image
                            image = ''
                            img_elem = element.find('img', src=True)
                            if img_elem:
                                image = img_elem.get('src', img_elem.get('data-src', ''))
                                if image and not image.startswith('http'):
                                    image = 'https://www.heb.com' + image
                            
                            product = {
                                'name': name,
                                'price': price,
                                'url': url,
                                'image': image,
                                'ingredients': '',
                                'store': 'HEB'
                            }
                            
                            # Validate product has minimum required info
                            if not product['name'] or len(product['name']) < 3:
                                continue
                            
                            # Avoid duplicates
                            if not any(p['name'].lower() == product['name'].lower() for p in products):
                                products.append(product)
                                
                            if len(products) >= limit:
                                break
                        except Exception as e:
                            continue
                    
                    if products:
                        break
                
            if products:
                break
                
        except Exception as e:
            print(f"Error with URL {search_url}: {e}")
            continue
    
    # Filter products to ensure they're relevant to the search term
    # Only return products that contain the search term in the name (case-insensitive)
    search_terms = search_term.lower().split()
    relevant_products = []
    
    for product in products:
        product_name_lower = product.get('name', '').lower()
        # Check if any search term appears in the product name
        if any(term in product_name_lower for term in search_terms if len(term) > 2):
            relevant_products.append(product)
        # Also include if the full search term is in the name
        elif search_term.lower() in product_name_lower:
            relevant_products.append(product)
    
    # If we found relevant products, return them
    if relevant_products:
        return relevant_products[:limit]
    
    # Strategy 3: Try Selenium if available (for JavaScript-rendered content)
    if SELENIUM_AVAILABLE and not products:
        try:
            print("Attempting to use Selenium for JavaScript-rendered content...")
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            driver = webdriver.Chrome(options=chrome_options)
            try:
                search_url = f"https://www.heb.com/search/?q={search_term}"
                driver.get(search_url)
                
                # Wait for products to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "product"))
                )
                
                # Get page source and parse
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                # Use the same parsing logic as before
                # ... (could add Selenium-specific parsing here)
                
            finally:
                driver.quit()
        except Exception as e:
            print(f"Selenium attempt failed: {e}")
    
    # If no products found, return empty list (don't use mock data)
    if not products:
        print(f"No products found from HEB for search: '{search_term}'")
        print("Note: HEB uses bot protection (Incapsula) which blocks automated requests.")
        print("To enable real HEB scraping, you need to:")
        print("  1. Use a headless browser (Selenium/Playwright) - install: pip install selenium")
        print("  2. Or find HEB's API endpoint by inspecting network requests in browser DevTools")
        print("  3. Or use mock data mode: Set USE_MOCK_DATA=True in .env file")
        return []

def get_product_details(product_url):
    """Fetch detailed product information including ingredients using Selenium"""
    if not product_url or not product_url.startswith('http'):
        return None
    
    if not SELENIUM_AVAILABLE:
        # Fallback to requests if Selenium not available (will likely fail due to bot protection)
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            response = requests.get(product_url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            soup = BeautifulSoup(response.content, 'html.parser')
        except:
            return None
    else:
        # Use Selenium to fetch product page (bypasses bot protection)
        driver = None
        try:
            driver = create_selenium_driver()
            driver.set_page_load_timeout(10)  # 10 second timeout for ingredient pages
            driver.implicitly_wait(2)
            
            print(f"Fetching ingredients from: {product_url}")
            driver.get(product_url)
            
            # Wait a moment for page to load
            import time
            time.sleep(1.5)
            
            # Get page source and parse
            soup = BeautifulSoup(driver.page_source, 'html.parser')
        except Exception as e:
            print(f"Error loading product page {product_url}: {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    # Now parse ingredients from the page
    ingredients_text = ""
    
    # Strategy 1: Look for HEB's specific ingredients structure
    # <div class="sc-578c3839-3 frvaxi"><h4>Ingredients</h4><span>...</span></div>
    ingredients_div = soup.find('div', class_=re.compile(r'sc-578c3839-3|frvaxi', re.I))
    if ingredients_div:
        # Look for h4 with "Ingredients" text
        h4 = ingredients_div.find('h4', string=re.compile(r'ingredients?', re.I))
        if h4:
            # Find the span with actual ingredients
            span = ingredients_div.find('span')
            if span:
                ingredients_text = span.get_text(strip=True)
                print(f"Found ingredients using HEB structure: {ingredients_text[:100]}...")
    
    # Strategy 2: Look for any div containing "Ingredients" heading
    if not ingredients_text:
        ingredients_heading = soup.find(['h4', 'h3', 'h2'], string=re.compile(r'ingredients?', re.I))
        if ingredients_heading:
            # Look in parent or next sibling
            parent = ingredients_heading.parent
            if parent:
                # Try to find span or div with ingredients text
                ingredients_elem = parent.find(['span', 'div', 'p'])
                if ingredients_elem:
                    ingredients_text = ingredients_elem.get_text(strip=True)
    
    # Strategy 3: Look for structured data (JSON-LD)
    if not ingredients_text:
        script_tags = soup.find_all('script', type=re.compile(r'application/json|application/ld\+json'))
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    ingredients = data.get('ingredients', data.get('nutrition', {}).get('ingredients', ''))
                    if ingredients:
                        ingredients_text = ingredients if isinstance(ingredients, str) else ', '.join(ingredients) if isinstance(ingredients, list) else str(ingredients)
                        break
            except (json.JSONDecodeError, AttributeError):
                continue
    
    # Strategy 4: Generic search for ingredients section
    if not ingredients_text:
        # Look for any div with class containing "ingredient"
        ingredient_divs = soup.find_all('div', class_=re.compile(r'ingredient', re.I))
        for div in ingredient_divs:
            text = div.get_text(strip=True)
            if 'ingredient' in text.lower() and len(text) > 20:
                # Extract text after "Ingredients" label
                parts = re.split(r'ingredients?:?\s*', text, flags=re.I)
                if len(parts) > 1:
                    ingredients_text = parts[1].strip()
                    break
    
    return {
        'ingredients': ingredients_text.strip() if ingredients_text else ""
    }

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

def scrape_kroger_product(search_term, limit=20):
    """Scrape Kroger website for products using Selenium"""
    if USE_MOCK_DATA:
        return get_mock_products(search_term, limit)
    
    if not SELENIUM_AVAILABLE:
        print("ERROR: Selenium not available. Install with: pip install selenium webdriver-manager")
        return []
    
    driver = None
    import time
    start_time = time.time()
    max_total_time = 25
    
    try:
        driver = create_selenium_driver()
        driver.set_page_load_timeout(12)
        driver.implicitly_wait(2)
        
        # Kroger search URL - try multiple URL patterns
        search_urls = [
            f"https://www.kroger.com/search?query={search_term.replace(' ', '+')}",
            f"https://www.kroger.com/search?q={search_term.replace(' ', '+')}",
            f"https://www.kroger.com/s/search?query={search_term.replace(' ', '+')}",
        ]
        
        soup = None
        for search_url in search_urls:
            print(f"Loading Kroger search page: {search_url}")
            try:
                driver.get(search_url)
                time.sleep(3)  # Wait for page to load
                
                # Check if page loaded properly
                page_source = driver.page_source
                if len(page_source) > 5000:  # Reasonable page size
                    soup = BeautifulSoup(page_source, 'html.parser')
                    print(f"Successfully loaded page from {search_url}")
                    break
                else:
                    print(f"Page too small ({len(page_source)} chars), trying next URL...")
            except Exception as e:
                print(f"Page load error for {search_url}: {e}")
                continue
        
        if soup is None:
            print("ERROR: Could not load any Kroger search page")
            return []
        
        # Parse page source
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        products = []
        
        # Look for product links - Kroger uses various patterns
        product_link_patterns = [
            r'/p/',
            r'/product/',
            r'/shop/product',
        ]
        
        all_product_links = []
        for pattern in product_link_patterns:
            links = soup.find_all('a', href=re.compile(pattern, re.I))
            all_product_links.extend(links)
        
        # Remove duplicates
        seen_urls = set()
        unique_links = []
        for link in all_product_links:
            href = link.get('href', '')
            if href and href not in seen_urls:
                seen_urls.add(href)
                unique_links.append(link)
        
        print(f"Found {len(unique_links)} unique product links from Kroger")
        
        # If no links found with standard patterns, try broader search
        if len(unique_links) == 0:
            print("No product links found with standard patterns. Trying broader search...")
            # Look for any links that might be products
            all_links = soup.find_all('a', href=True)
            print(f"Total links on page: {len(all_links)}")
            
            # Sample some links for debugging
            if all_links:
                print("Sample links found:")
                for link in all_links[:5]:
                    href = link.get('href', '')[:80]
                    text = link.get_text(strip=True)[:50]
                    print(f"  - {href} | {text}")
            
            # Look for product-like links
            for link in all_links[:200]:
                href = link.get('href', '')
                link_text = link.get_text(strip=True)
                
                # Skip obvious non-product links
                skip_patterns = ['/cart', '/account', '/help', '/store', '/deals', '/recipes', 
                               '/categories', '/brands', '/coupons', '/flyer', '/delivery', '/sign-in']
                if any(skip in href.lower() for skip in skip_patterns):
                    continue
                
                # Look for links that might be products
                if href and len(href) > 5:
                    # Check if link text looks like a product name
                    if link_text and len(link_text) > 5 and len(link_text) < 200:
                        # Exclude navigation text
                        nav_words = ['shop', 'cart', 'account', 'help', 'menu', 'search', 'browse', 
                                   'view all', 'see more', 'learn more', 'sign in', 'register']
                        if not any(nav in link_text.lower() for nav in nav_words):
                            unique_links.append(link)
                            if len(unique_links) >= limit * 2:
                                break
            
            print(f"Found {len(unique_links)} potential product links via alternative method")
        
        # Extract products from links
        for link in unique_links[:limit*2]:
            if time.time() - start_time > max_total_time:
                break
            try:
                url = link.get('href', '')
                if not url:
                    continue
                if not url.startswith('http'):
                    url = 'https://www.kroger.com' + url
                
                name = link.get_text(strip=True)
                if not name or len(name) < 3:
                    # Try to find name in parent elements
                    parent = link.parent
                    for _ in range(3):
                        if parent:
                            name_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'span', 'div'], 
                                                   class_=re.compile(r'name|title|product', re.I))
                            if name_elem:
                                name = name_elem.get_text(strip=True)
                                if name and len(name) > 3:
                                    break
                            parent = parent.parent if hasattr(parent, 'parent') else None
                
                if not name or len(name) < 3:
                    continue
                
                # Find price
                price = 'N/A'
                try:
                    container = link.find_parent(['article', 'div', 'li'])
                    if container:
                        price_text = container.get_text()
                        price_match = re.search(r'\$[\d,]+\.?\d{0,2}', price_text)
                        if price_match:
                            price = price_match.group(0)
                except:
                    pass
                
                # Find image
                image = ''
                try:
                    img = link.find('img')
                    if not img:
                        container = link.find_parent(['article', 'div'])
                        if container:
                            img = container.find('img')
                    if img:
                        image = img.get('src', img.get('data-src', ''))
                        if image and not image.startswith('http'):
                            image = 'https://www.kroger.com' + image
                except:
                    pass
                
                product = {
                    'name': name[:200],
                    'price': price,
                    'url': url,
                    'image': image,
                    'ingredients': '',
                    'store': 'Kroger'
                }
                
                if not any(p['name'].lower() == product['name'].lower() or 
                          p['url'] == product['url'] for p in products):
                    products.append(product)
                    if len(products) >= limit:
                        break
            except Exception as e:
                print(f"Error extracting product from Kroger: {e}")
                continue
        
        print(f"Scraped {len(products)} products from Kroger")
        return products[:limit]
        
    except Exception as e:
        print(f"Kroger scraping error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

@app.route('/api/search', methods=['POST'])
def search_products():
    """Search for products and filter based on user criteria"""
    import signal
    
    data = request.json
    search_term = data.get('query', '')
    user_id = data.get('user_id', 'default')
    store = data.get('store', 'kroger').lower()  # Default to kroger
    
    if not search_term:
        return jsonify({'error': 'Search term required'}), 400
    
    # Get user's filters
    filters = user_filters.get(user_id, DEFAULT_FILTERS.copy())
    
    # Check cache (include store in cache key)
    cache_key = f"{store}_{search_term}_{user_id}"
    if cache_key in product_cache:
        cache_time = cache_expiry.get(cache_key)
        if cache_time and datetime.now() < cache_time:
            return jsonify({'products': product_cache[cache_key]})
    
    # Scrape products based on selected store
    try:
        if store == 'heb':
            products = scrape_heb_product(search_term)
        elif store == 'kroger':
            products = scrape_kroger_product(search_term)
        else:
            return jsonify({'error': f'Unknown store: {store}. Supported stores: heb, kroger'}), 400
    except TimeoutError:
        return jsonify({
            'error': 'Search timed out. Please try again with a different search term.',
            'products': []
        }), 408
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({
            'error': f'Search failed: {str(e)}',
            'products': []
        }), 500
    
    # Filter products based on ingredients
    filtered_products = []
    for product in products:
        # If ingredients not available, try to fetch them (but don't block if it fails)
        if not product.get('ingredients') and product.get('url'):
            try:
                details = get_product_details(product.get('url', ''))
                if details and details.get('ingredients'):
                    product['ingredients'] = details.get('ingredients', '')
            except Exception as e:
                # If fetching ingredients fails, continue without them
                # Products without ingredients will pass the filter check
                print(f"Could not fetch ingredients for {product.get('name', 'unknown')}: {e}")
        
        # Check if product passes filters
        # Products without ingredients listed will pass (assumed safe)
        if check_ingredients(product.get('ingredients', ''), filters):
            filtered_products.append(product)
    
    # Cache results for 5 minutes
    product_cache[cache_key] = filtered_products
    cache_expiry[cache_key] = datetime.now() + timedelta(minutes=5)
    
    return jsonify({
        'products': filtered_products,
        'total_found': len(products),
        'filtered_count': len(filtered_products),
        'store': store
    })

@app.route('/api/filters', methods=['GET'])
def get_filters():
    """Get user's current filters"""
    user_id = request.args.get('user_id', 'default')
    filters = user_filters.get(user_id, DEFAULT_FILTERS.copy())
    return jsonify({'filters': filters})

@app.route('/api/filters', methods=['POST'])
def add_filter():
    """Add a new filter for the user"""
    data = request.json
    user_id = data.get('user_id', 'default')
    filter_term = data.get('filter', '').strip()
    
    if not filter_term:
        return jsonify({'error': 'Filter term required'}), 400
    
    if user_id not in user_filters:
        user_filters[user_id] = DEFAULT_FILTERS.copy()
    
    if filter_term.lower() not in [f.lower() for f in user_filters[user_id]]:
        user_filters[user_id].append(filter_term)
    
    return jsonify({'filters': user_filters[user_id]})

@app.route('/api/filters', methods=['DELETE'])
def remove_filter():
    """Remove a filter for the user"""
    data = request.json
    user_id = data.get('user_id', 'default')
    filter_term = data.get('filter', '').strip()
    
    if not filter_term:
        return jsonify({'error': 'Filter term required'}), 400
    
    if user_id in user_filters:
        user_filters[user_id] = [f for f in user_filters[user_id] 
                                if f.lower() != filter_term.lower()]
    
    return jsonify({'filters': user_filters.get(user_id, DEFAULT_FILTERS.copy())})

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """Add product to cart (placeholder for cart integration)"""
    data = request.json
    product_url = data.get('product_url', '')
    
    # This would integrate with HEB's cart API if available
    # For now, return the product URL so frontend can redirect
    return jsonify({
        'success': True,
        'message': 'Product URL ready for cart',
        'product_url': product_url
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
