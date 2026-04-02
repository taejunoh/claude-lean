# Project Configuration

## Coding Style
- Use 2-space indentation
- Prefer const over let
- Always use TypeScript strict mode
- Never use any type

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | /api/users | List all users | Bearer |
| POST | /api/users | Create user | Bearer |
| GET | /api/users/:id | Get user by ID | Bearer |
| PUT | /api/users/:id | Update user | Bearer |
| DELETE | /api/users/:id | Delete user | Bearer |
| GET | /api/posts | List posts | Public |
| POST | /api/posts | Create post | Bearer |
| GET | /api/posts/:id | Get post | Public |
| PUT | /api/posts/:id | Update post | Bearer |
| DELETE | /api/posts/:id | Delete post | Bearer |
| GET | /api/comments | List comments | Public |
| POST | /api/comments | Create comment | Bearer |

## Deployment Commands

```bash
# Build the project
npm run build

# Run database migrations
npx prisma migrate deploy

# Start production server
NODE_ENV=production npm start

# Deploy to staging
kubectl apply -f k8s/staging/
kubectl rollout status deployment/app -n staging

# Deploy to production
kubectl apply -f k8s/production/
kubectl rollout status deployment/app -n production

# Rollback
kubectl rollout undo deployment/app -n production
```

## Agent IDs

| Agent | UUID | Environment |
|-------|------|-------------|
| primary | 550e8400-e29b-41d4-a716-446655440000 | production |
| backup | 6ba7b810-9dad-11d1-80b4-00c04fd430c8 | production |
| staging | 6ba7b811-9dad-11d1-80b4-00c04fd430c8 | staging |
| dev-1 | f47ac10b-58cc-4372-a567-0e02b2c3d479 | development |
| dev-2 | 7c9e6679-7425-40de-944b-e07fc1f90ae7 | development |

## Incident Log

### 2024-12-15: Database Outage
- Duration: 45 minutes
- Cause: Connection pool exhaustion
- Resolution: Increased max connections from 20 to 50
- Postmortem: Need better connection monitoring

### 2024-11-28: API Rate Limiting
- Duration: 2 hours
- Cause: Missing rate limiter on /api/users endpoint
- Resolution: Added express-rate-limit middleware
- TODO: Add rate limiting to all endpoints

### 2024-10-03: Memory Leak
- Duration: Ongoing (3 days before detection)
- Cause: Event listeners not cleaned up in WebSocket handler
- Resolution: Added proper cleanup in disconnect handler

## Meeting Notes

### Sprint 42 Retro (2024-12-20)
- Good: Faster deploys with new CI pipeline
- Bad: Too many hotfixes this sprint
- Action: Add pre-deploy smoke tests

### Sprint 41 Retro (2024-12-06)
- Good: TypeScript migration completed
- Bad: Documentation lagging behind
- Action: Add docs as acceptance criteria
