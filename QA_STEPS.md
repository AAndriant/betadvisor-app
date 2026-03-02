# QA Steps: Mobile Token Refresh Interceptor

## Overview
These steps describe how to manually test the automatic token refresh functionality on the mobile application when the access token expires. The interceptor should catch a 401 error, refresh the token, and replay the original request. If the refresh fails, it should log out the user.

## QA Step 1: Verify Automatic Refresh (Happy Path)
1. Ensure you are logged into the mobile application and are on the main feed screen.
2. In your backend or database, manually expire or invalidate your current `accessToken`. Keep the `refreshToken` valid.
3. On the mobile application, trigger a network request (e.g., pull to refresh the feed, or navigate to a screen that fetches data).
4. **Expected Outcome**:
   - The app should automatically detect the 401 error and send a request to `/api/auth/token/refresh/`.
   - The request should succeed, and the new access token should be saved.
   - The original request (e.g., fetching the feed) should be replayed and succeed, reloading the feed automatically without redirecting to the login screen.

## QA Step 2: Verify Logout on Expired Refresh Token (Failure Path)
1. Ensure you are logged into the mobile application.
2. In your backend or database, invalidate or expire both your `accessToken` and your `refreshToken`.
3. Trigger a network request on the mobile app (e.g., pull to refresh).
4. **Expected Outcome**:
   - The app detects the 401 error and attempts to refresh the token.
   - The refresh request fails (e.g., 401 or 403 response).
   - The application clears the stored tokens (`SecureStore` or `localStorage`).
   - The user is seamlessly redirected to the `/login` screen.

## QA Step 3: Verify Concurrent Requests Handling
1. Log into the mobile application.
2. Manually expire your `accessToken` but keep the `refreshToken` valid.
3. Trigger multiple network requests simultaneously (e.g., navigate to a screen that fires several parallel requests for stats, profile, and feed).
4. **Expected Outcome**:
   - Only **one** request to `/api/auth/token/refresh/` should be sent.
   - The other requests should be queued while the token is being refreshed.
   - Once the refresh succeeds, all pending requests should be replayed with the new access token and succeed.
   - No duplicate refresh requests or infinite refresh loops should occur.
