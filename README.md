# Healthy Food Finder 🥗

A web application that automatically filters out unhealthy food from grocery store websites. Currently supports HEB (H-E-B).

## Features

- **Smart Filtering**: Automatically filters out products containing unhealthy ingredients like seed oils, artificial sweeteners, preservatives, etc.
- **Custom Filters**: Add your own custom filters for ingredients you want to avoid
- **Product Search**: Search for products at HEB and see only healthy options
- **Cart Integration**: Easily view products on HEB's website to add them to your cart

## Default Filters

The application comes with default filters for common unhealthy ingredients:
- Seed oils (canola, soybean, corn, sunflower, etc.)
- High fructose corn syrup
- Artificial sweeteners, flavors, and colors
- Preservatives (BHT, BHA, TBHQ)
- MSG and other additives

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn
- `python3-full` package (for virtual environment support)

**Note**: This project uses a virtual environment as recommended by Debian/Ubuntu Python package management policy. This allows installing non-Debian-packaged Python packages without sudo access.

**No sudo access?** The script will automatically install pip in the virtual environment using `ensurepip` or by downloading `get-pip.py`. No system packages need to be installed.

**Troubleshooting**: If you get "no module named flask" or similar errors:
1. Run the fix script: `./fix_venv.sh`
2. Or manually: `rm -rf venv && python3 -m venv venv && source venv/bin/activate && python -m ensurepip --upgrade && pip install -r requirements.txt`

### Quick Start (Recommended)

Use the provided start script to launch both servers:

```bash
cd /home/school/Documents/healthy_food_finder
./start.sh
```

This will automatically:
- Create a virtual environment (if it doesn't exist)
- Install all Python dependencies in the virtual environment
- Install all Node dependencies
- Start both backend and frontend servers

**Note**: The first time you run this, it will create a `venv/` directory. This is a virtual environment that isolates the project's Python dependencies.

### Manual Setup

#### Backend Setup

1. Navigate to the project root directory:
```bash
cd /home/school/Documents/healthy_food_finder
```

2. Create a virtual environment (as recommended by Debian/Ubuntu):
```bash
python3 -m venv venv
```

If this fails, install `python3-full`:
```bash
sudo apt install python3-full
```

3. Activate the virtual environment:
```bash
source venv/bin/activate
```

4. Install Python dependencies:
```bash
pip install -r requirements.txt
```

5. (Optional) Create a `.env` file in the `backend/` directory:
```bash
# Use mock data for development/testing
USE_MOCK_DATA=True
```

6. Run the backend server:
```bash
cd backend
python app.py
```

**Note**: Make sure the virtual environment is activated (you'll see `(venv)` in your prompt). To deactivate later, run `deactivate`.

The backend will run on `http://localhost:5000`

**Note**: By default, the backend uses real HEB scraping. To use mock data for testing, set `USE_MOCK_DATA=True` in your `.env` file or environment variables.

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will run on `http://localhost:3000` and automatically open in your browser.

## Usage

1. Start both the backend and frontend servers (see Setup Instructions above)
2. Open your browser to `http://localhost:3000`
3. Click "Show Filters" to view and manage your ingredient filters
4. Add custom filters for any ingredients you want to avoid
5. Search for products (e.g., "chicken", "bread", "milk")
6. View filtered results showing only healthy products
7. Click "View on HEB" to open the product page on HEB's website

## Project Structure

```
healthy_food_finder/
├── backend/
│   └── app.py              # Flask API server
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── App.js          # Main app component
│   │   └── index.js        # Entry point
│   └── package.json
├── requirements.txt        # Python dependencies
└── README.md
```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/search` - Search for products
  - Body: `{ "query": "search term", "user_id": "default" }`
- `GET /api/filters?user_id=default` - Get user filters
- `POST /api/filters` - Add a filter
  - Body: `{ "filter": "ingredient name", "user_id": "default" }`
- `DELETE /api/filters` - Remove a filter
  - Body: `{ "filter": "ingredient name", "user_id": "default" }`
- `POST /api/cart/add` - Add product to cart (opens HEB page)
  - Body: `{ "product_url": "https://..." }`

## Development Mode

The application includes a mock data mode for development and testing. By default, it scrapes real HEB products. To use mock data instead, set `USE_MOCK_DATA=True` in your `.env` file. This is useful for:

- Testing the filtering logic without network requests
- Developing the frontend without depending on HEB's website
- Avoiding rate limiting or blocking issues

**Real HEB Scraping**: The application uses Selenium with browser emulation to bypass HEB's bot protection and fetch real products.

**Setup for Real Scraping**:
1. Install Selenium and webdriver-manager (already in requirements.txt):
   ```bash
   pip install selenium webdriver-manager
   ```

2. Install Firefox or LibreWolf (required for Selenium):
   - **Firefox**: `sudo apt install firefox` (or download from https://www.mozilla.org/firefox/)
   - **LibreWolf** (privacy-focused): Download from https://librewolf.net/ or use AppImage
   - GeckoDriver will be automatically downloaded by webdriver-manager

3. The application is configured to use real scraping by default (`USE_MOCK_DATA=False`)

**How it works**:
- Uses headless Firefox/LibreWolf browser via Selenium
- Emulates a real browser to bypass Incapsula bot protection
- Waits for JavaScript-rendered content to load
- Extracts product information from the rendered page
- Automatically detects Firefox or LibreWolf installation

**Note**: 
- First run may take longer as GeckoDriver is downloaded automatically
- The application will search for Firefox/LibreWolf in common locations
- If you have Firefox/LibreWolf in a custom location, you can set the path in the code

## Notes

- **Web Scraping**: The web scraping functionality is a placeholder and will need to be adapted to HEB's actual website structure. HEB's website may:
  - Use JavaScript to render content (requiring Selenium/Playwright)
  - Have anti-scraping measures
  - Change their HTML structure frequently
  
- **HEB API**: For production use, consider using HEB's official API if available, or contact HEB for API access.

- **Product Ingredients**: Product ingredient data may need to be fetched from individual product detail pages, which requires additional API calls.

- **Data Persistence**: User filters are currently stored in memory. For production, consider using a database (SQLite, PostgreSQL, etc.) for persistence.

- **Rate Limiting**: Be respectful when scraping - add delays between requests and respect robots.txt.

## Future Enhancements

- Support for additional grocery stores
- User accounts and saved filter preferences
- Product favorites and shopping lists
- Direct cart API integration (if available)
- Product comparison features
- Nutritional information display

## License

MIT
