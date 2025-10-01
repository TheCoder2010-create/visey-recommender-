// Demo data for testing Visey Recommender when WordPress is not available

const DEMO_DATA = {
    // Demo user profiles
    users: {
        1: {
            id: 1,
            name: "Sarah Chen",
            email: "sarah@techstartup.com",
            industry: "technology",
            stage: "growth",
            team_size: "10-50",
            funding: "series-a",
            location: "San Francisco",
            bio: "Tech entrepreneur focused on AI and machine learning solutions",
            registered_date: "2023-01-15T00:00:00"
        },
        2: {
            id: 2,
            name: "Marcus Johnson",
            email: "marcus@retailco.com",
            industry: "retail",
            stage: "startup",
            team_size: "1-10",
            funding: "seed",
            location: "New York",
            bio: "E-commerce entrepreneur building sustainable retail solutions",
            registered_date: "2023-03-22T00:00:00"
        },
        3: {
            id: 3,
            name: "Elena Rodriguez",
            email: "elena@healthtech.com",
            industry: "healthcare",
            stage: "scale",
            team_size: "50-100",
            funding: "series-b",
            location: "Austin",
            bio: "Healthcare innovation leader developing digital health platforms",
            registered_date: "2022-11-08T00:00:00"
        }
    },

    // Demo posts/resources
    posts: [
        {
            id: 1,
            title: "Building Scalable AI Systems for Startups",
            link: "https://demo.com/ai-systems",
            excerpt: "Learn how to build and scale AI systems that grow with your startup, from MVP to enterprise.",
            content: "Complete guide to AI architecture for startups...",
            categories: [1, 3],
            tags: [1, 2, 5],
            category_names: ["Technology", "Artificial Intelligence"],
            tag_names: ["AI", "Scalability", "Architecture"],
            author_id: 1,
            author_name: "Tech Expert",
            date: "2024-01-15T10:00:00",
            modified: "2024-01-16T14:30:00"
        },
        {
            id: 2,
            title: "Fundraising Strategies for Series A",
            link: "https://demo.com/series-a-fundraising",
            excerpt: "Essential strategies and tips for successfully raising your Series A funding round.",
            content: "Comprehensive guide to Series A fundraising...",
            categories: [2, 4],
            tags: [3, 4, 6],
            category_names: ["Funding", "Business Strategy"],
            tag_names: ["Series A", "Investors", "Pitch Deck"],
            author_id: 2,
            author_name: "Funding Expert",
            date: "2024-01-10T09:00:00",
            modified: "2024-01-11T16:45:00"
        },
        {
            id: 3,
            title: "Building High-Performance Teams",
            link: "https://demo.com/team-building",
            excerpt: "How to recruit, manage, and scale high-performance teams in fast-growing companies.",
            content: "Team building strategies for startups...",
            categories: [5, 6],
            tags: [7, 8, 9],
            category_names: ["Team Management", "Leadership"],
            tag_names: ["Hiring", "Culture", "Management"],
            author_id: 3,
            author_name: "HR Expert",
            date: "2024-01-08T11:30:00",
            modified: "2024-01-09T13:20:00"
        },
        {
            id: 4,
            title: "Digital Marketing for B2B SaaS",
            link: "https://demo.com/b2b-marketing",
            excerpt: "Proven digital marketing strategies specifically designed for B2B SaaS companies.",
            content: "B2B SaaS marketing playbook...",
            categories: [7, 8],
            tags: [10, 11, 12],
            category_names: ["Marketing", "SaaS"],
            tag_names: ["Digital Marketing", "B2B", "Customer Acquisition"],
            author_id: 1,
            author_name: "Marketing Expert",
            date: "2024-01-05T14:15:00",
            modified: "2024-01-06T10:30:00"
        },
        {
            id: 5,
            title: "Legal Considerations for Tech Startups",
            link: "https://demo.com/startup-legal",
            excerpt: "Essential legal considerations every tech startup founder should know about.",
            content: "Legal guide for tech entrepreneurs...",
            categories: [9, 10],
            tags: [13, 14, 15],
            category_names: ["Legal", "Compliance"],
            tag_names: ["Intellectual Property", "Contracts", "Compliance"],
            author_id: 2,
            author_name: "Legal Expert",
            date: "2024-01-03T16:45:00",
            modified: "2024-01-04T09:15:00"
        }
    ],

    // Demo categories
    categories: [
        { id: 1, name: "Technology", slug: "technology", count: 25 },
        { id: 2, name: "Funding", slug: "funding", count: 18 },
        { id: 3, name: "Artificial Intelligence", slug: "ai", count: 12 },
        { id: 4, name: "Business Strategy", slug: "business-strategy", count: 22 },
        { id: 5, name: "Team Management", slug: "team-management", count: 15 },
        { id: 6, name: "Leadership", slug: "leadership", count: 20 },
        { id: 7, name: "Marketing", slug: "marketing", count: 28 },
        { id: 8, name: "SaaS", slug: "saas", count: 16 },
        { id: 9, name: "Legal", slug: "legal", count: 10 },
        { id: 10, name: "Compliance", slug: "compliance", count: 8 }
    ],

    // Demo tags
    tags: [
        { id: 1, name: "AI", slug: "ai", count: 15 },
        { id: 2, name: "Scalability", slug: "scalability", count: 12 },
        { id: 3, name: "Series A", slug: "series-a", count: 8 },
        { id: 4, name: "Investors", slug: "investors", count: 14 },
        { id: 5, name: "Architecture", slug: "architecture", count: 10 },
        { id: 6, name: "Pitch Deck", slug: "pitch-deck", count: 9 },
        { id: 7, name: "Hiring", slug: "hiring", count: 18 },
        { id: 8, name: "Culture", slug: "culture", count: 16 },
        { id: 9, name: "Management", slug: "management", count: 20 },
        { id: 10, name: "Digital Marketing", slug: "digital-marketing", count: 22 },
        { id: 11, name: "B2B", slug: "b2b", count: 19 },
        { id: 12, name: "Customer Acquisition", slug: "customer-acquisition", count: 17 },
        { id: 13, name: "Intellectual Property", slug: "ip", count: 7 },
        { id: 14, name: "Contracts", slug: "contracts", count: 11 },
        { id: 15, name: "Compliance", slug: "compliance", count: 6 }
    ],

    // Demo recommendations
    recommendations: {
        1: [ // For user 1 (Sarah Chen - Tech/AI)
            {
                resource_id: 1,
                title: "Building Scalable AI Systems for Startups",
                link: "https://demo.com/ai-systems",
                score: 0.95,
                reason: "Matches your AI and technology interests"
            },
            {
                resource_id: 4,
                title: "Digital Marketing for B2B SaaS",
                link: "https://demo.com/b2b-marketing",
                score: 0.82,
                reason: "Relevant for tech startup growth"
            },
            {
                resource_id: 2,
                title: "Fundraising Strategies for Series A",
                link: "https://demo.com/series-a-fundraising",
                score: 0.78,
                reason: "Matches your growth stage funding needs"
            },
            {
                resource_id: 3,
                title: "Building High-Performance Teams",
                link: "https://demo.com/team-building",
                score: 0.71,
                reason: "Important for scaling your team"
            },
            {
                resource_id: 5,
                title: "Legal Considerations for Tech Startups",
                link: "https://demo.com/startup-legal",
                score: 0.65,
                reason: "Essential legal knowledge for tech founders"
            }
        ],
        2: [ // For user 2 (Marcus Johnson - Retail/E-commerce)
            {
                resource_id: 4,
                title: "Digital Marketing for B2B SaaS",
                link: "https://demo.com/b2b-marketing",
                score: 0.88,
                reason: "Digital marketing strategies applicable to retail"
            },
            {
                resource_id: 2,
                title: "Fundraising Strategies for Series A",
                link: "https://demo.com/series-a-fundraising",
                score: 0.85,
                reason: "Next funding round preparation"
            },
            {
                resource_id: 3,
                title: "Building High-Performance Teams",
                link: "https://demo.com/team-building",
                score: 0.79,
                reason: "Team scaling for growing retail business"
            },
            {
                resource_id: 5,
                title: "Legal Considerations for Tech Startups",
                link: "https://demo.com/startup-legal",
                score: 0.72,
                reason: "Legal compliance for e-commerce"
            },
            {
                resource_id: 1,
                title: "Building Scalable AI Systems for Startups",
                link: "https://demo.com/ai-systems",
                score: 0.58,
                reason: "AI applications in retail technology"
            }
        ],
        3: [ // For user 3 (Elena Rodriguez - Healthcare/Scale)
            {
                resource_id: 3,
                title: "Building High-Performance Teams",
                link: "https://demo.com/team-building",
                score: 0.92,
                reason: "Critical for scaling healthcare operations"
            },
            {
                resource_id: 5,
                title: "Legal Considerations for Tech Startups",
                link: "https://demo.com/startup-legal",
                score: 0.89,
                reason: "Healthcare compliance and regulations"
            },
            {
                resource_id: 1,
                title: "Building Scalable AI Systems for Startups",
                link: "https://demo.com/ai-systems",
                score: 0.81,
                reason: "AI applications in digital health"
            },
            {
                resource_id: 4,
                title: "Digital Marketing for B2B SaaS",
                link: "https://demo.com/b2b-marketing",
                score: 0.74,
                reason: "B2B marketing for healthcare platforms"
            },
            {
                resource_id: 2,
                title: "Fundraising Strategies for Series A",
                link: "https://demo.com/series-a-fundraising",
                score: 0.67,
                reason: "Advanced funding strategies"
            }
        ]
    },

    // Demo health status
    health: {
        status: "healthy",
        wordpress_api: {
            status: "healthy",
            auth_status: "demo_mode",
            base_url: "https://demo.visey.com"
        },
        cache_healthy: true,
        last_sync: "2024-01-15T10:30:00Z",
        sync_status: "recent",
        service_status: "healthy"
    },

    // Demo sync results
    syncResult: {
        success: true,
        users_synced: 3,
        posts_synced: 5,
        categories_synced: 10,
        tags_synced: 15,
        duration: 2.45,
        errors: [],
        last_sync: "2024-01-15T10:30:00Z",
        triggered_by: "manual"
    }
};

// Demo mode detection and API override
class DemoMode {
    constructor() {
        this.enabled = false;
        this.checkDemoMode();
    }

    checkDemoMode() {
        // Enable demo mode if WordPress is not configured or API is not available
        const urlParams = new URLSearchParams(window.location.search);
        this.enabled = urlParams.get('demo') === 'true' || 
                      localStorage.getItem('visey_demo_mode') === 'true';
    }

    enableDemo() {
        this.enabled = true;
        localStorage.setItem('visey_demo_mode', 'true');
        console.log('🎭 Demo mode enabled - using mock data');
    }

    disableDemo() {
        this.enabled = false;
        localStorage.removeItem('visey_demo_mode');
        console.log('🔌 Demo mode disabled - using real API');
    }

    // Mock API responses
    async mockFetch(url, options = {}) {
        await this.delay(200, 800); // Simulate network delay

        const urlObj = new URL(url, 'http://localhost:8000');
        const path = urlObj.pathname;
        const params = urlObj.searchParams;

        console.log(`🎭 Demo API call: ${options.method || 'GET'} ${path}`);

        // Health endpoint
        if (path === '/health') {
            return this.mockResponse(DEMO_DATA.health);
        }

        // WordPress health
        if (path === '/wordpress/health') {
            return this.mockResponse(DEMO_DATA.health);
        }

        // Recommendations
        if (path === '/recommend') {
            const userId = params.get('user_id') || '1';
            const topN = parseInt(params.get('top_n')) || 10;
            const recommendations = DEMO_DATA.recommendations[userId] || DEMO_DATA.recommendations['1'];
            
            return this.mockResponse({
                user_id: parseInt(userId),
                items: recommendations.slice(0, topN)
            });
        }

        // WordPress search
        if (path === '/wordpress/search') {
            const query = params.get('q') || '';
            const limit = parseInt(params.get('limit')) || 10;
            
            const results = DEMO_DATA.posts.filter(post => 
                post.title.toLowerCase().includes(query.toLowerCase()) ||
                post.excerpt.toLowerCase().includes(query.toLowerCase())
            ).slice(0, limit);

            return this.mockResponse({
                query: query,
                results: results,
                count: results.length
            });
        }

        // User profile
        if (path.startsWith('/wordpress/users/')) {
            const userId = path.split('/').pop();
            const user = DEMO_DATA.users[userId];
            
            if (user) {
                return this.mockResponse(user);
            } else {
                return this.mockResponse({ detail: 'User not found' }, 404);
            }
        }

        // WordPress data
        if (path.startsWith('/wordpress/data/')) {
            const dataType = path.split('/').pop();
            const data = DEMO_DATA[dataType] || [];
            
            return this.mockResponse({
                data: data,
                count: data.length,
                cached: true
            });
        }

        // WordPress sync
        if (path === '/wordpress/sync' && options.method === 'POST') {
            return this.mockResponse(DEMO_DATA.syncResult);
        }

        // Default response
        return this.mockResponse({ error: 'Demo endpoint not implemented' }, 404);
    }

    mockResponse(data, status = 200) {
        return {
            ok: status >= 200 && status < 300,
            status: status,
            json: async () => data,
            text: async () => JSON.stringify(data)
        };
    }

    async delay(min, max) {
        const delay = Math.random() * (max - min) + min;
        return new Promise(resolve => setTimeout(resolve, delay));
    }
}

// Global demo mode instance
window.demoMode = new DemoMode();

// Override fetch for demo mode
const originalFetch = window.fetch;
window.fetch = function(url, options) {
    if (window.demoMode && window.demoMode.enabled && url.includes('localhost:8000')) {
        return window.demoMode.mockFetch(url, options);
    }
    return originalFetch(url, options);
};

// Add demo mode toggle to the interface
document.addEventListener('DOMContentLoaded', () => {
    // Add demo mode indicator and toggle
    const header = document.querySelector('.header');
    if (header) {
        const demoToggle = document.createElement('div');
        demoToggle.className = 'demo-toggle';
        demoToggle.innerHTML = `
            <label style="display: flex; align-items: center; gap: 8px; font-size: 0.9rem;">
                <input type="checkbox" id="demo-mode-toggle" ${window.demoMode.enabled ? 'checked' : ''}>
                <span>Demo Mode</span>
                <i class="fas fa-theater-masks" style="color: var(--warning-color);"></i>
            </label>
        `;
        
        header.appendChild(demoToggle);
        
        // Toggle functionality
        document.getElementById('demo-mode-toggle').addEventListener('change', (e) => {
            if (e.target.checked) {
                window.demoMode.enableDemo();
                window.location.reload(); // Reload to apply demo mode
            } else {
                window.demoMode.disableDemo();
                window.location.reload(); // Reload to disable demo mode
            }
        });
    }
});