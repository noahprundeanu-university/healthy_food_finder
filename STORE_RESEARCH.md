# Grocery Store API and Bot Protection Research

## Current Status

**Active Store**: Kroger (via official API)

**Removed Stores**: HEB and Walmart (no longer supported)

## Research Summary

### HEB (H-E-B) - ❌ Removed
- **API Status**: ❌ No public API available
- **Bot Protection**: 🔴 **Very Aggressive** - Uses Incapsula with strict bot detection
- **Status**: Actively blocks automated requests with error codes and incident tracking
- **Alternative**: HEB offers "H-E-B Select Ingredients®" program (pre-filtered products with 175+ ingredients excluded)
- **Decision**: **REMOVED** - Too difficult to scrape reliably, no official API

### Kroger - ✅ Active
- **API Status**: ✅ Official Products API available
- **Bot Protection**: 🟢 Minimal (using official API)
- **Notes**: 
  - Official Kroger Products API available through developer program
  - OAuth2 client credentials flow
  - Product data includes `ingredientStatement` for filtering
  - Fast, reliable, no scraping needed
- **Status**: **ACTIVE** - Primary store supported

### Walmart - ❌ Removed
- **API Status**: ⚠️ API exists but integration was removed
- **Bot Protection**: 🟡 Moderate
- **Decision**: **REMOVED** - Focus on Kroger for better reliability

### Alternative Grocery Stores (Future Consideration)

#### 1. Target
- **API Status**: ⚠️ Limited public API
- **Bot Protection**: 🟡 Moderate
- **Notes**:
  - Some API access available
  - Less aggressive than HEB
- **Recommendation**: **POSSIBLE** - Future consideration

#### 2. Whole Foods (Amazon)
- **API Status**: ⚠️ Through Amazon API
- **Bot Protection**: 🟡 Moderate
- **Notes**:
  - Access through Amazon Product Advertising API
  - Requires API key and has usage restrictions
- **Recommendation**: **POSSIBLE** - Requires Amazon API setup

#### 3. Instacart
- **API Status**: ✅ Partner API available (requires partnership)
- **Bot Protection**: 🟡 Moderate
- **Notes**:
  - Instacart has partner APIs
  - Aggregates multiple grocery stores
  - Requires business partnership for API access
- **Recommendation**: **CONSIDER** - Good if partnership is possible

## Current Implementation

### Kroger API Integration
- Uses OAuth2 client credentials flow
- Scope: `product.compact`
- Endpoints:
  - Token: `https://api.kroger.com/v1/connect/oauth2/token`
  - Products: `https://api.kroger.com/catalog/v2/products` (v2, falls back to v1 if needed)
- Extracts ingredients from `nutritionInformation[0].ingredientStatement`
- Fast, reliable, no browser automation needed

### Fallback Mechanism
- If Kroger API credentials are not set, falls back to Selenium scraping
- Selenium uses Firefox/LibreWolf in headless mode
- Less reliable due to bot protection
- Only recommended for development/testing

## Recommendations

### Current Approach: Kroger API (BEST)
- **Pros**: Official API, fast, reliable, includes ingredient data
- **Cons**: Requires API credentials
- **Status**: ✅ Implemented and active

### Future: Multi-Store Support
- **Pros**: Users can choose their preferred store
- **Cons**: More complex implementation, need to support multiple APIs
- **Effort**: High - Need to support multiple store APIs
- **Recommendation**: Consider after Kroger integration is stable

## Implementation Notes

- Official APIs are always more reliable than scraping
- Kroger API provides structured data including ingredients
- No browser automation needed when using API
- Selenium fallback exists but is not recommended for production
