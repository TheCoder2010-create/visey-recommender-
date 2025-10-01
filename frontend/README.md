# Visey Recommender Frontend

A simple, modern web interface for testing the Visey Recommender API.

## Features

### 🏥 System Monitoring
- **Real-time API status** - Check if the recommender service is online
- **WordPress health** - Monitor WordPress API connectivity
- **Cache status** - View cache health and data freshness
- **Data statistics** - See counts of cached posts, users, categories, and tags

### 🎯 Recommendation Testing
- **Get personalized recommendations** - Test recommendations for any user ID
- **Configurable results** - Choose number of recommendations (5-20)
- **Performance metrics** - See response times and success rates
- **Interactive results** - Click through to actual WordPress posts

### 🔍 WordPress Data Explorer
- **Content search** - Search through WordPress posts and pages
- **User profiles** - View detailed user profiles and metadata
- **Data browsing** - Explore cached WordPress content

### ⚙️ WordPress Management
- **Manual sync** - Trigger WordPress data synchronization
- **Health checks** - Verify WordPress API connectivity
- **Sync monitoring** - View sync results and error logs

### 📊 Performance Testing
- **Load testing** - Run concurrent requests to test performance
- **Response time charts** - Visual performance metrics
- **Success rate monitoring** - Track API reliability

## Quick Start

### 1. Start the API Server
First, make sure the Visey Recommender API is running:

```bash
# From project root
python -m uvicorn visey_recommender.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the Frontend Server
```bash
# From project root
cd frontend
python server.py
```

The frontend will automatically open in your browser at `http://localhost:3000`.

### 3. Configure WordPress (Optional)
If you want to test with real WordPress data, set these environment variables:

```bash
export WP_BASE_URL="https://your-wordpress-site.com"
export WP_AUTH_TYPE="basic"  # or jwt, application_password
export WP_USERNAME="your_username"
export WP_PASSWORD="your_password"
```

## Usage Guide

### Testing Recommendations

1. **Enter a User ID** - Use any WordPress user ID (try 1 for testing)
2. **Select number of recommendations** - Choose 5-20 recommendations
3. **Click "Get Recommendations"** - View personalized results
4. **Check performance** - See response time and recommendation scores

### Exploring WordPress Data

1. **Search Content** - Enter keywords to search WordPress posts
2. **View User Profiles** - Enter user ID to see profile details
3. **Check Data Stats** - View counts of cached content

### Managing WordPress Integration

1. **Sync Data** - Click "Sync WordPress Data" to refresh cache
2. **Check Health** - Verify WordPress API connectivity
3. **Monitor Status** - View sync status and data freshness

### Performance Testing

1. **Select request count** - Choose 10, 50, or 100 concurrent requests
2. **Run load test** - Click "Run Load Test"
3. **View results** - See response times, success rate, and performance chart

## API Configuration

The frontend connects to the API server at `http://localhost:8000` by default. 

To change this, edit the `apiBaseUrl` in `script.js`:

```javascript
constructor() {
    this.apiBaseUrl = 'http://your-api-server:8000';
    this.init();
}
```

## Troubleshooting

### API Connection Issues
- **Check API server** - Make sure it's running on port 8000
- **CORS errors** - The frontend server handles CORS automatically
- **Network issues** - Verify firewall settings

### WordPress Integration Issues
- **Authentication errors** - Check WordPress credentials
- **No data** - Run a manual sync to populate cache
- **Slow responses** - Check WordPress server performance

### Performance Issues
- **Slow recommendations** - Check if cache is populated
- **High error rates** - Verify API server health
- **Browser issues** - Try refreshing or clearing cache

## Development

### File Structure
```
frontend/
├── index.html          # Main HTML structure
├── styles.css          # CSS styling
├── script.js           # JavaScript functionality
├── server.py           # Development server
└── README.md           # This file
```

### Customization

#### Styling
Edit `styles.css` to customize the appearance:
- CSS variables for colors and spacing
- Responsive design for mobile devices
- Dark/light theme support ready

#### Functionality
Edit `script.js` to add features:
- New API endpoints
- Additional charts and visualizations
- Custom data processing

#### Layout
Edit `index.html` to modify the interface:
- Add new sections
- Rearrange components
- Update content

## Browser Compatibility

- **Chrome/Edge** - Full support
- **Firefox** - Full support
- **Safari** - Full support
- **Mobile browsers** - Responsive design

## Security Notes

- **Development only** - This frontend is for testing/development
- **No authentication** - All API endpoints are accessible
- **CORS enabled** - Allows cross-origin requests
- **Local network** - Designed for local development

For production use, implement proper authentication and security measures.

## Features in Detail

### Real-time Status Updates
The interface automatically checks API status every few seconds and updates indicators.

### Interactive Charts
Performance testing includes visual charts showing response time distribution.

### Toast Notifications
Success/error messages appear as toast notifications in the top-right corner.

### Loading States
All operations show loading spinners and disable buttons to prevent double-clicks.

### Responsive Design
The interface works on desktop, tablet, and mobile devices.

### Error Handling
Comprehensive error handling with user-friendly error messages.

## API Endpoints Used

The frontend interacts with these API endpoints:

- `GET /health` - System health check
- `GET /recommend` - Get recommendations
- `GET /wordpress/health` - WordPress health
- `GET /wordpress/search` - Search content
- `GET /wordpress/users/{id}` - Get user profile
- `GET /wordpress/data/{type}` - Get cached data
- `POST /wordpress/sync` - Sync WordPress data

## Next Steps

1. **Add authentication** - Implement user login/logout
2. **Real-time updates** - WebSocket support for live updates
3. **Advanced charts** - More detailed performance visualizations
4. **Export functionality** - Download test results as CSV/JSON
5. **Saved configurations** - Store frequently used test parameters