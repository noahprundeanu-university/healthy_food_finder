# Healthy Food Finder 🥗

A web application that filters out unhealthy food from grocery store search results using the Kroger Products API.

## Features

- **Smart Filtering**: Automatically filters out products containing unhealthy ingredients like seed oils, artificial sweeteners, preservatives, etc.
- **Custom Filters**: Add your own custom filters for ingredients you want to avoid
- **Product Search**: Search for products using the official Kroger Products API
- **Fast Results**: Ingredients extracted directly from API responses (no per-product page scraping)
- **Cache Management**: Search results are cached and automatically invalidated when filters change

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

5. **Set up Kroger API credentials** (required for production, optional for development):

   Create a `.env` file in the `backend/` directory:
```bash
# Kroger API credentials (get from https://developer.kroger.com)
KROGER_CLIENT_ID=your_client_id
KROGER_CLIENT_SECRET=your_client_secret
KROGER_LOCATION_ID=your_location_id  # Optional but recommended for pricing/availability

# Optional overrides (defaults match Kroger Catalog API v2 docs):
# KROGER_TOKEN_URL=https://api.kroger.com/v1/connect/oauth2/token
# KROGER_API_BASE_URL=https://api.kroger.com
# KROGER_PRODUCTS_PATH=/catalog/v2/products
# OAuth scopes (defaults to product.compact)
# KROGER_SCOPE=product.compact

# Optional: Use mock data for development/testing (no API calls)
# USE_MOCK_DATA=True

# Optional: allow visible browser for debugging Selenium fallback (default is headless)
# HEADLESS=true
```

   **Getting Kroger API credentials:**
   1. Sign up at https://developer.kroger.com
   2. Create a new application
   3. Get your `client_id` and `client_secret`
   4. Set the OAuth scope to `product.compact`
   5. Optionally set a `location_id` for location-specific pricing

6. Run the backend server:
```bash
cd backend
python app.py
```

**Note**: Make sure the virtual environment is activated (you'll see `(venv)` in your prompt). To deactivate later, run `deactivate`.

The backend will run on `http://localhost:5000`

**Note**: By default, the backend will use the **Kroger API** if `KROGER_CLIENT_ID` and `KROGER_CLIENT_SECRET` are set. If not set, it will attempt Selenium scraping as a fallback (which may be blocked by bot protection). For best results, use the official API.

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
7. Click "View on Kroger" to open the product page on Kroger's website

## Project Structure

```
healthy_food_finder/
├── backend/
│   ├── app.py              # Flask API server
│   └── demo_secrets.py     # Local-only demo credentials (gitignored)
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── SearchBar.js
│   │   │   ├── ProductList.js
│   │   │   ├── ProductCard.js
│   │   │   └── FilterManager.js
│   │   ├── App.js          # Main app component
│   │   └── index.js        # Entry point
│   └── package.json
├── requirements.txt        # Python dependencies
├── start.sh               # Startup script
└── README.md
```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/search` - Search for products
  - Body: `{ "query": "search term", "user_id": "default", "store": "kroger" }`
  - Returns: `{ "products": [...], "total_found": N, "filtered_count": M, "store": "kroger" }`
- `GET /api/filters?user_id=default` - Get user filters
- `POST /api/filters` - Add a filter
  - Body: `{ "filter": "ingredient name", "user_id": "default" }`
- `DELETE /api/filters` - Remove a filter
  - Body: `{ "filter": "ingredient name", "user_id": "default" }`
- `POST /api/cart/add` - Add product to cart (placeholder - returns product URL)
  - Body: `{ "product_url": "https://..." }`

## Development Mode

The application includes a mock data mode for development and testing. To use mock data instead of the Kroger API, set `USE_MOCK_DATA=True` in your `.env` file. This is useful for:

- Testing the filtering logic without network requests
- Developing the frontend without depending on the Kroger API
- Avoiding rate limiting or API quota issues

**Kroger API (Recommended)**: The application uses the official Kroger Products API (OAuth2 client credentials flow) to fetch product data, including ingredients from the `ingredientStatement` field in the API response. This is fast, reliable, and doesn't require browser automation.

**Selenium Fallback**: If Kroger API credentials are not configured, the application will attempt to scrape Kroger's website using Selenium (Firefox/LibreWolf). This is less reliable due to bot protection and is only recommended for development/testing.

**Setup for Selenium Fallback** (if not using API):
1. Install Firefox or LibreWolf (required for Selenium):
   - **Firefox**: `sudo apt install firefox` (or download from https://www.mozilla.org/firefox/)
   - **LibreWolf** (privacy-focused): Download from https://librewolf.net/ or use AppImage
   - GeckoDriver will be automatically managed by Selenium

2. The application is configured to use headless mode by default (`HEADLESS=true`)

## Production Deployment

### Recommended: Render.com

This stack (Flask + React) works well on Render.com:

1. **Backend (Web Service)**:
   - Root Directory: `backend`
   - Build Command: `pip install -r ../requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - Environment Variables: `KROGER_CLIENT_ID`, `KROGER_CLIENT_SECRET`, `KROGER_LOCATION_ID`

2. **Frontend (Static Site)**:
   - Root Directory: `frontend`
   - Build Command: `npm ci && npm run build`
   - Publish Directory: `build`
   - Environment Variables: `REACT_APP_API_BASE_URL` (set to your backend URL)

See the deployment section in the codebase for more details.

## Notes

- **Kroger API**: The application uses the official Kroger Products API for reliable, fast product data. API credentials are required for production use.

- **Product Ingredients**: Product ingredient data is extracted directly from the Kroger API response (`nutritionInformation[0].ingredientStatement`), making searches fast and reliable.

- **Data Persistence**: User filters are currently stored in memory. For production, consider using a database (SQLite, PostgreSQL, etc.) for persistence across server restarts.

- **Rate Limiting**: The Kroger API has rate limits. The application includes caching (5-minute TTL) to reduce API calls. Cache is automatically invalidated when filters change.

- **CORS**: The backend uses Flask-CORS to allow frontend requests. In production, configure CORS to only allow your frontend domain.

## Future Enhancements

- Support for additional grocery stores (Walmart, Target, etc.)
- User accounts and saved filter preferences (database persistence)
- Product favorites and shopping lists
- Direct cart API integration (if available)
- Product comparison features
- Nutritional information display
- Price history and alerts

## License

MIT
