# BetAdvisor Security Configuration

This document outlines the security mechanisms implemented to enforce production safety, data privacy, and mitigation of brute-force attacks.

## 1. Environment and SSL/HTTPS Enforcement

The project relies on the `DJANGO_ENV` environment variable to toggle production features:

*   **`DJANGO_ENV=development`**:
    *   CORS is fully permissive (`CORS_ALLOW_ALL_ORIGINS=True`).
    *   SSL redirection and HSTS are disabled.
    *   Secure cookie flags are disabled.
*   **`DJANGO_ENV=production`**:
    *   CORS is restricted.
    *   SSL and Secure cookies should be explicitly enabled.

### Security Variables for Production

When deploying to production, ensure these variables are properly set:

| Variable | Type | Default | Description |
|---|---|---|---|
| `SECURE_SSL_REDIRECT` | boolean | `False` | Forces all HTTP traffic to redirect to HTTPS. |
| `SECURE_HSTS_SECONDS` | integer | `0` | Enables HTTP Strict Transport Security (HSTS). Recommend setting to `31536000` (1 year) in production. |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | boolean | `False` | Applies HSTS to all subdomains. |
| `SECURE_HSTS_PRELOAD` | boolean | `False` | Permits the site to be submitted to the browser HSTS preload list. |
| `SESSION_COOKIE_SECURE` | boolean | `False` | Ensures session cookies are only transmitted over HTTPS. |
| `CSRF_COOKIE_SECURE` | boolean | `False` | Ensures CSRF cookies are only transmitted over HTTPS. |

## 2. CORS Configuration

Cross-Origin Resource Sharing (CORS) is strictly controlled in production to prevent unauthorized domains from accessing the API.

*   Set `DJANGO_ENV=production`.
*   Provide a comma-separated list of allowed origins via the `CORS_ALLOWED_ORIGINS` environment variable.

Example:
```env
CORS_ALLOWED_ORIGINS=https://app.betadvisor.com,https://admin.betadvisor.com
```

## 3. Rate Limiting (Throttling)

Django Rest Framework (DRF) throttling is configured to prevent abuse, scraping, and brute-force attacks on sensitive endpoints.

### Global API Limits

*   **Anonymous Users:** 100 requests per minute.
*   **Authenticated Users:** 100 requests per minute.

These can be configured via DRF settings if needed.

### Login and Registration Limits (Brute Force Protection)

Authentication endpoints (`/api/auth/token/` and `/api/auth/register/`) have stricter limits.

*   **Limit:** 5 requests per minute (applies to both anonymous and authenticated states attempting these actions).

These specific limits are enforced via the `login_anon` and `login_user` throttle scopes.
