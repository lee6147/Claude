You are a Data Engineer. Build the data layer for a SaaS analytics dashboard.

## Your file (create ONLY this one file):
- src/lib/mock-data.ts

## Requirements:

### TypeScript interfaces:
- DailyStat: date, users, pageViews, revenue
- TrafficSource: source, visitors, percentage
- DeviceBreakdown: device, sessions, percentage

### Data arrays:
- dailyStats: 30 days of sample data with realistic growth trend
- trafficSources: 5 sources (Direct, Organic, Social, Referral, Email)
- deviceBreakdown: Desktop 58%, Mobile 35%, Tablet 7%

### Utility functions:
- formatNumber(n): 1234 → "1,234"
- formatCurrency(n): 1234 → "$1,234"
- getGrowthRate(data, days): calculate percentage growth
- getTopSource(data): return highest traffic source

All named exports. No default exports.

Create the file now.
