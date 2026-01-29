# Healthy Food Finder 🥗

A web application that filters out unhealthy ingredients from Kroger grocery store products using the official Kroger API.

## Features

- **Smart Filtering**: Automatically filters out products containing unhealthy ingredients like seed oils, artificial sweeteners, preservatives, etc.
- **Custom Filters**: Add your own custom filters for ingredients you want to avoid
- **Real Product Data**: Uses Kroger's official Catalog API v2 for reliable product information
- **Fast Search**: Efficient API-based search with intelligent caching
- **Product Links**: Direct links to Kroger product pages

## Tech Stack

- **Backend**: Flask (Python) with Gunicorn for production
- **Frontend**: React with Axios
- **API**: Kroger Catalog API v2 (OAuth2 Client Credentials)
- **Deployment**: Render.com (or any Python/Node.js hosting)

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

5. Create a `.env` file in the `backend/` directory:
```bash
cd backend
```

Create `backend/.env` with your Kroger API credentials:
```bash
# Required: Kroger API credentials
# Get these from https://developer.kroger.com/
KROGER_CLIENT_ID=your_client_id
KROGER_CLIENT_SECRET=your_client_secret

# Optional but recommended for pricing/availability:
KROGER_LOCATION_ID=your_location_id

# Optional: OAuth scope (defaults to product.compact)
# KROGER_SCOPE=product.compact

# Optional: API endpoints (defaults match Kroger Catalog API v2 docs)
# KROGER_TOKEN_URL=https://api.kroger.com/v1/connect/oauth2/token
# KROGER_API_BASE_URL=https://api.kroger.com
# KROGER_PRODUCTS_PATH=/catalog/v2/products
```

**Getting Kroger API Credentials**:
1. Visit https://developer.kroger.com/
2. Sign up for a developer account
3. Create a new application
4. Copy your `client_id` and `client_secret`
5. For `KROGER_LOCATION_ID`, use a store location ID from your area (find it in the Kroger app or website)

6. Run the backend server:
```bash
cd backend
python app.py
```

**Note**: Make sure the virtual environment is activated (you'll see `(venv)` in your prompt). To deactivate later, run `deactivate`.

The backend will run on `http://localhost:5000`

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
│   ├── demo_secrets.py     # Optional: demo credentials (not tracked by git)
│   └── .env                # Environment variables (not tracked by git)
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── FilterManager.js
│   │   │   ├── ProductCard.js
│   │   │   ├── ProductList.js
│   │   │   └── SearchBar.js
│   │   ├── App.js          # Main app component
│   │   └── index.js        # Entry point
│   └── package.json
├── requirements.txt        # Python dependencies
├── start.sh                # Quick start script
├── fix_venv.sh            # Virtual environment fix script
└── README.md
```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/search` - Search for products
  - Body: `{ "query": "search term", "user_id": "default", "store": "kroger" }`
  - Returns: `{ "products": [...], "total_found": N, "filtered_count": M }`
- `GET /api/filters?user_id=default` - Get user filters
  - Returns: `{ "filters": [...] }`
- `POST /api/filters` - Add a filter
  - Body: `{ "filter": "ingredient name", "user_id": "default" }`
  - Returns: `{ "filters": [...] }`
- `DELETE /api/filters` - Remove a filter
  - Body: `{ "filter": "ingredient name", "user_id": "default" }`
  - Returns: `{ "filters": [...] }`
- `POST /api/cart/add` - Get product URL for cart (placeholder)
  - Body: `{ "product_url": "https://..." }`
  - Returns: `{ "success": true, "product_url": "..." }`

## How It Works

1. **API Integration**: Uses Kroger's official Catalog API v2 with OAuth2 Client Credentials flow
2. **Product Data**: Fetches product information including names, prices, images, and ingredient statements directly from the API
3. **Filtering**: Checks product names and ingredient statements against user-defined filters
4. **Caching**: Implements intelligent caching with filter-based invalidation to improve performance
5. **Fallback**: If Catalog API v2 returns insufficient scope, automatically falls back to legacy v1 API

## Deployment to Render.com

### Backend (Flask API)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `healthy-food-finder-backend` (or your choice)
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r ../requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Add Environment Variables:
   - `KROGER_CLIENT_ID` (your Kroger client ID)
   - `KROGER_CLIENT_SECRET` (your Kroger client secret)
   - `KROGER_LOCATION_ID` (optional but recommended)
6. Deploy and copy the backend URL (e.g., `https://your-backend.onrender.com`)

### Frontend (React Static Site)

1. In Render Dashboard, click **New +** → **Static Site**
2. Connect the same GitHub repository
3. Configure:
   - **Name**: `healthy-food-finder-frontend` (or your choice)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm ci && npm run build`
   - **Publish Directory**: `build`
4. Add Environment Variable (if using API base URL):
   - `REACT_APP_API_BASE_URL` = your backend URL (e.g., `https://your-backend.onrender.com`)
5. Deploy

**Note**: The frontend uses a proxy in development (`package.json`). For production, you may need to configure the API base URL or use CORS properly.

## Development Notes

- **Data Source**: All product data comes from Kroger's official API - no web scraping required
- **Ingredient Extraction**: Ingredients are extracted directly from the API response (`nutritionInformation[0].ingredientStatement`)
- **Filtering**: Uses combined text search across product name, ingredient statement, and other metadata
- **Caching**: Search results are cached per user with filter-based invalidation
- **Error Handling**: Comprehensive error handling with fallback to legacy API if needed

## Future Enhancements

- Support for additional grocery stores (via their official APIs)
- User accounts and saved filter preferences
- Product favorites and shopping lists
- Direct cart API integration (if available)
- Product comparison features
- Enhanced nutritional information display
- Price history and alerts

## License

MIT
