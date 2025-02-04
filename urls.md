# Implementing Shareable URLs for Marketing Plans

## Key Considerations

### 1. URL Structure
- Should URLs be random strings or contain meaningful information?
  - Example: `/plan/abc123` vs `/plan/company-name-date-hash`
- Length of URLs (balance between uniqueness and usability)
- Should URLs expire? If so, after how long?
- Should URLs be public or require authentication?

### 2. Database Requirements

#### Suggested Schema: MongoDB
```javascript
{
  _id: ObjectId,
  url_id: String,          // Unique identifier for the URL
  plan_content: String,    // The actual marketing plan content
  metadata: {
    company_name: String,
    created_at: DateTime,
    last_accessed: DateTime,
    view_count: Number,
    form_data: Object      // Original form inputs
  }
}
```

Why MongoDB?
- Schema-less nature allows for easy updates to plan structure
- Good performance for read-heavy operations
- Simple to set up and maintain
- Built-in TTL (Time To Live) for automatic expiration
- Efficient for storing large text documents

### 3. Security Considerations
- Rate limiting to prevent abuse
- URL entropy to prevent guessing
- Privacy concerns:
  - Should plans be password protected?
  - Should we track who views the plans?
  - Should we allow plan creators to revoke access?

### 4. Implementation Steps

1. **Database Setup**
   - Set up MongoDB instance
   - Create indexes for `url_id` and `created_at`
   - Configure TTL if implementing expiration

2. **Backend Changes**
   - Add URL generation logic
   - Create new endpoints:
     - `/generate-url` (POST)
     - `/plan/:url_id` (GET)
   - Implement caching for frequently accessed plans

3. **Frontend Updates**
   - Add URL sharing UI elements
   - Implement copy-to-clipboard functionality
   - Add loading states for URL generation
   - Create new view for accessing plans via URL

4. **Analytics & Monitoring**
   - Track URL usage
   - Monitor database performance
   - Set up alerts for abuse

### 5. Performance Optimizations
- Implement caching layer (Redis/Memcached)
- CDN for static content
- Database indexing strategy
- Lazy loading of plan content

## Clarified Requirements

### URL Structure
- 6-character unique hash (e.g., `/plan/abc123`)
- No meaningful information in URL for privacy
- URLs expire after exactly 10 days
- No user accounts or authentication required
- Plans are immutable (no editing after creation)
- No password protection
- No view tracking needed
- No manual deletion (automatic expiration only)

### Simplified Database Schema (MongoDB)
```javascript
{
  _id: ObjectId,
  url_id: String,          // 6-character unique hash
  plan_content: String,    // The actual marketing plan content
  created_at: DateTime,    // Used for TTL index
  metadata: {
    company_name: String,  // For internal reference only
    form_data: Object      // Original form inputs
  }
}
```

### Additional Technical Considerations

1. **Hash Generation**
   - Using 6 characters: `[A-Za-z0-9]` gives us 62^6 = ~56.8 billion possibilities
   - Need to handle hash collisions
   - Suggested library: `nanoid` with custom alphabet
   ```javascript
   const alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
   const length = 6;
   ```

2. **TTL Implementation**
   - MongoDB TTL index on `created_at` field
   - Set to exactly 10 days
   - No manual intervention needed
   ```javascript
   db.plans.createIndex({ "created_at": 1 }, { expireAfterSeconds: 864000 }) // 10 days
   ```

3. **UI Updates Needed**
   - Add "Generate URL" button next to existing action buttons
   - Show URL in a modal or inline display
   - Add copy-to-clipboard functionality
   - Display remaining time until expiration
   - Clear success/error messages for URL generation

4. **Rate Limiting**
   - Implement basic rate limiting per IP
   - Suggested limits:
     - 10 URL generations per hour per IP
     - 100 plan views per hour per IP

5. **Error Handling**
   - Handle expired URLs gracefully
   - Show user-friendly messages for:
     - Expired plans
     - Invalid URLs
     - Rate limit exceeded
     - Server errors

### New Implementation Steps

1. **Database Setup**
   - Configure MongoDB with TTL index
   - Create unique index on `url_id`
   - Set up automatic backups

2. **Backend Changes**
   - Add URL generation endpoint
   - Implement collision handling
   - Add rate limiting middleware
   - Create error handling middleware

3. **Frontend Updates**
   - Add URL generation UI
   - Implement remaining time display
   - Add copy URL functionality
   - Create expired plan view

4. **Monitoring**
   - Track URL generation rate
   - Monitor database size
   - Alert on high collision rates
   - Track error rates

### Questions Requiring Clarification

1. **Performance Requirements**
   - Expected number of plans generated per day?
   - Maximum acceptable latency for URL generation?

2. **Storage Requirements**
   - Expected size of average plan?
   - Monthly storage budget?

3. **Error Handling**
   - Should we implement retry logic for failed URL generations?
   - How to handle database outages?

4. **Monitoring**
   - Do we need usage analytics?
   - What metrics should we track?

### Technical Dependencies

```plaintext
Required dependencies:
- mongodb (primary database)
- nanoid (URL generation)
- rate-limiter-flexible (basic rate limiting)
- express-mongo-sanitize (security)

Optional:
- prometheus (monitoring)
- sentry (error tracking)
```

### Security Considerations

1. **URL Security**
   - Implement rate limiting
   - Use cryptographically secure random generation
   - Sanitize database queries

2. **Data Protection**
   - No sensitive data in URLs
   - Basic DDoS protection
   - Input validation

3. **Infrastructure**
   - Regular security updates
   - Database backup strategy
   - Error logging (without sensitive data)

### Deployment Checklist

1. Set up MongoDB with proper indexes
2. Configure TTL for 10-day expiration
3. Implement and test URL generation
4. Add rate limiting
5. Deploy with monitoring
6. Set up error tracking
7. Configure backup strategy

## Next Steps
1. Get clarification on the above questions
2. Create detailed technical specification
3. Set up development environment with MongoDB
4. Create proof of concept with basic URL generation
5. Implement security measures
6. Add analytics and monitoring
7. Perform load testing
8. Deploy to production with monitoring
