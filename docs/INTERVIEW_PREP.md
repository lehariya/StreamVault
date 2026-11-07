# StreamVault — Interview Preparation

## 60-second explanation

“I built StreamVault, a full-stack video download management platform using React, Python Flask, and SQLite. The problem it addresses is controlling downloads fairly across different subscription tiers. Users can register, sign in, browse a video catalogue, view their plan limits, and download videos only when they have the required subscription and remaining daily and monthly quota. The backend validates every download request instead of trusting the frontend. It creates an auditable download record containing the user, video, timestamp, IP address, browser, device identifier, plan, file size, and status. I also implemented idempotency keys to reduce duplicate records on retries, and an optional registered-device check. React provides the dashboard, library, plans and download history, while Flask exposes REST APIs and SQLAlchemy manages the relational data.”

## 3-minute explanation

“StreamVault is a subscription-aware video download platform. The key engineering challenge is that download permissions must be enforced on the server. If the frontend only hides a download button, a user could call the API directly and bypass that restriction.

The React application contains authentication, a dashboard, video library, plan comparison and download history pages. It communicates with Flask using Axios. After login, Flask issues a JWT access token. The frontend sends that token in the Authorization header for protected routes.

The backend uses SQLAlchemy models for User, Plan, Subscription, Video, DownloadRecord and RegisteredDevice. A user can have subscription records over time. The active subscription is resolved by checking its status, start date and expiry date. If no valid paid subscription exists, the Free plan is used.

Before a download, the API checks that the video exists and is active, the user's plan grants access to the video's required tier, the optional device rule passes, and both daily and monthly quotas have remaining capacity. The download endpoint repeats those checks; the earlier authorization endpoint is only a preflight check.

For duplicate and concurrent requests, the client sends an idempotency key. The backend stores a pending download reservation before streaming the file. Pending and completed records count against the quota, preventing ordinary parallel requests from all seeing the same remaining slot. The record includes audit metadata such as IP, user agent, browser, plan and device ID. Once the response closes, the starter implementation attempts to mark it completed.

The Downloads page reads the authenticated user's history from the API. Admin-only endpoints expose audit records and allow catalog metadata creation. I used environment variables for secrets and configuration, password hashing for credentials, and tests for core API behavior.

For production, I would move from SQLite to PostgreSQL, implement atomic quota reservations and a stale-pending reconciliation worker, integrate verified payment webhooks, and use object storage/CDN delivery with signed URLs. I would also add rate limiting, refresh-token rotation, monitoring, and broader integration and concurrency tests.”

## 25 likely interview questions and answers

1. **What problem does the project solve?**  
   It enforces fair, auditable video downloads based on a user's subscription tier and quota, rather than allowing unrestricted downloads.

2. **Why did you choose React?**  
   React lets me build reusable UI components and separate pages for the dashboard, catalogue, plans and history. State updates the interface when API data changes.

3. **Why Flask?**  
   Flask is lightweight and lets me organize REST endpoints into focused blueprints. It is suitable for a small API service and easy to extend.

4. **Why SQLAlchemy?**  
   It maps Python classes to relational tables and provides query and relationship support without writing every query manually.

5. **Why SQLite?**  
   It is easy to run locally and requires no separate database server. For production with multiple API instances and higher write concurrency, I would choose PostgreSQL.

6. **What is a REST API?**  
   It is an HTTP interface where resources are accessed through methods such as GET and POST. For example, GET `/api/videos` lists videos and POST `/api/downloads/4` requests video 4.

7. **How does authentication work?**  
   The user submits credentials. The server verifies the password hash and issues a signed JWT. The client sends it as a Bearer token to protected endpoints.

8. **Is a JWT the same as encryption?**  
   No. A signed JWT provides integrity and authenticity, not confidentiality. Sensitive data should not be placed in its payload.

9. **How are passwords stored?**  
   Werkzeug's password-hashing utilities store a salted password hash. The original password is not stored.

10. **How do you determine the active subscription?**  
    I query active subscription rows for the user and verify the start time and that expiry is either absent or in the future. Otherwise the Free plan applies.

11. **How are video tiers enforced?**  
    Each video has a required plan. The backend compares plan ranks, such as Free < Bronze < Silver < Gold, before serving the file.

12. **Why check permissions on the backend if the frontend already hides the button?**  
    Frontend checks are only for user experience. Anyone can call an API directly, so the server must independently authorize every download.

13. **How is the daily quota calculated?**  
    The server counts pending and completed download records from the start of the current UTC day and subtracts that count from the plan's daily limit.

14. **How is the monthly quota calculated?**  
    It counts qualifying records since the first day of the current UTC month and compares the count with the monthly plan limit.

15. **How does quota reset?**  
    No reset job is required for this design. Each request calculates usage inside the current calendar window. When the date or month changes, earlier records fall outside that window.

16. **What is an idempotency key?**  
    It is a unique request identifier. If a network retry sends the same key again, the server can recognize the same logical request instead of creating a duplicate record.

17. **How do you handle simultaneous downloads?**  
    The implementation creates a pending reservation before streaming and counts pending reservations against quota. A process-local lock serializes reservation checks inside this one API process. It does not coordinate multiple workers or instances; production needs database-level atomic reservation logic and appropriate locking.

18. **What is the difference between pending and completed?**  
    Pending means the server reserved the quota and started the response. Completed means the response close callback ran and the server marked the transfer complete. It does not prove the user saved the file successfully.

19. **What happens if the user refreshes during download?**  
    A new request should use a new key only if it is a genuinely new attempt. Reusing the same key prevents a duplicate logical record. A production service should reconcile stale pending records and support resumable downloads if required.

20. **What audit data is stored?**  
    User ID, video ID, request time, completion time, status, IP address, user-agent string, browser, device ID, plan code, file size and idempotency key.

21. **How do you protect admin routes?**  
    The request must have a valid JWT, and the server loads the user and checks that the role is `admin`. The frontend cannot grant itself that role.

22. **How do you handle subscription expiry?**  
    The active-plan query excludes subscriptions whose expiry is at or before the current server time. Every download re-runs that query.

23. **What is the purpose of environment variables?**  
    They keep deployment-specific settings and secrets out of source code, allowing different configuration in development and production.

24. **What tests did you write?**  
    The included pytest tests check the health endpoint, login/profile behavior, invalid registration, plan listing and empty download history. I would add tests for quota boundaries, expiry, premium access denial, idempotency, interrupted transfers and concurrent reservations.

25. **What would you improve next?**  
    PostgreSQL transactions and row locking, payment-provider webhook verification, background reconciliation, rate limiting, object storage/CDN with expiring signed URLs, resumable downloads, device management UI, observability and broader automated tests.

## Be accurate about your contribution

You can say you implemented the source code and understand its architecture only after you have run it, inspected the files, and practiced explaining the main flows. Do not claim production payment integration, large-scale concurrency validation, or proof of a completed client-side save: those are not delivered by this starter.

## Important files to understand first

1. `backend/app/models.py` — database structure.
2. `backend/app/services.py` — active plan and quota calculations.
3. `backend/app/routes/downloads.py` — authorization, reservation and download flow.
4. `backend/app/routes/auth.py` — registration, password checks and JWT.
5. `frontend/src/pages/Videos.jsx` — user-triggered download flow.
6. `frontend/src/pages/Downloads.jsx` — download history UI.
7. `frontend/src/api.js` — frontend API client and token header.
