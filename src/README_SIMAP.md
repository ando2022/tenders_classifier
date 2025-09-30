# SIMAP.ch API Integration

This module provides a Python client for interacting with the SIMAP.ch API, which is the Swiss public procurement platform.

## Overview

SIMAP (Système d'information pour les marchés publics) is the official Swiss platform for public procurement. This integration allows you to:

- Retrieve public tenders and procurement opportunities
- Search for specific types of contracts
- Access organization information
- Filter by dates, categories, and other criteria

## Setup

### 1. Install Dependencies

```bash
conda env update -f environment.yml
```

### 2. Configure API Access

The SIMAP API requires authentication. You have two options:

#### Option A: Environment Variable (Recommended)
```bash
export SIMAP_API_KEY="your_api_key_here"
```

#### Option B: Direct Initialization
```python
from src.simap import SimapAPI

client = SimapAPI(api_key="your_api_key_here")
```

### 3. Get API Access

To obtain an API key:
1. Visit [SIMAP API Documentation](https://int.simap.ch/api-doc)
2. Register for machine-to-machine access
3. Complete the registration form
4. Note: 2FA (Two-Factor Authentication) is required for all actions

## Usage

### Basic Usage

```python
from src.simap import SimapAPI

# Initialize client
client = SimapAPI()

# Test connection
health = client.health_check()
print(f"API Status: {health}")

# Get recent tenders
tenders = client.get_tenders(limit=10)
print(f"Found {len(tenders['data'])} tenders")
```

### Searching for Tenders

```python
# Search for economics-related tenders
results = client.search_tenders(
    query="economics OR policy OR research",
    limit=20
)

# Filter by date range
from datetime import datetime, timedelta
date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
date_to = datetime.now().strftime('%Y-%m-%d')

filtered_tenders = client.get_tenders(
    limit=50,
    date_from=date_from,
    date_to=date_to,
    search_term="consulting"
)
```

### Getting Specific Information

```python
# Get a specific tender by ID
tender = client.get_tender_by_id("tender_id_here")

# Get organizations
organizations = client.get_organizations(limit=20)

# Get categories and locations
categories = client.get_categories()
locations = client.get_locations()
```

## API Methods

### Core Methods

- `get_tenders(limit, offset, search_term, date_from, date_to, **filters)` - Retrieve tenders
- `get_tender_by_id(tender_id)` - Get specific tender
- `search_tenders(query, limit, offset, **filters)` - Search tenders
- `get_organizations(limit, offset, **filters)` - Get organizations
- `get_organization_by_id(org_id)` - Get specific organization
- `get_categories()` - Get tender categories
- `get_locations()` - Get available locations
- `health_check()` - Check API connectivity

### Parameters

- `limit`: Maximum number of results (default: 100, max: 1000)
- `offset`: Number of results to skip (for pagination)
- `search_term`: Text to search for in tender content
- `date_from`: Start date in YYYY-MM-DD format
- `date_to`: End date in YYYY-MM-DD format
- `query`: Search query string for search_tenders method

## BAK Economics Integration

The module includes specific functionality for BAK Economics opportunity identification:

### Keywords
The system uses predefined keywords relevant to BAK Economics:
- Economics, policy, research, consulting
- Data, statistics, forecasting, modeling
- Public sector, government, federal, cantonal

### Opportunity Scoring
Tenders are scored based on:
- Keyword matches (30% weight)
- Company fit (40% weight)
- Budget size (20% weight)
- Timeline (10% weight)

### Example: Finding BAK Economics Opportunities

```python
from src.example_usage import example_opportunity_identification

# Run the opportunity identification example
example_opportunity_identification()
```

## Error Handling

The client includes comprehensive error handling:

```python
try:
    tenders = client.get_tenders(limit=10)
except requests.exceptions.RequestException as e:
    print(f"API request failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Logging

The client uses Python's logging module. To enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Rate Limiting

The SIMAP API may have rate limits. The client includes:
- Request timeout handling (30 seconds default)
- Retry logic (3 attempts with 1-second delay)
- Proper error handling for rate limit responses

## Examples

See `src/example_usage.py` for comprehensive examples including:
- Basic API usage
- Advanced search with filters
- BAK Economics opportunity identification
- Scoring and ranking of opportunities

## API Documentation

For complete API documentation, visit:
- [SIMAP API Documentation](https://int.simap.ch/api-doc)
- [API Version 1.3.0 Change Log](https://int.simap.ch/api-doc)

## Support

For questions about the SIMAP API:
- Visit the [SIMAP Forum](https://forum.simap.ch)
- Check the official API documentation
- Review the change log for updates

## Notes

- All API actions require 2FA (Two-Factor Authentication)
- The API is designed for machine-to-machine interaction
- Some endpoints may require specific permissions
- Rate limits may apply for high-volume usage
