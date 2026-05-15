/**
 * P2-19: Analytics service for BetAdvisor.
 * 
 * Lightweight analytics abstraction layer.
 * In production, this can be wired to PostHog, Amplitude, or Mixpanel.
 * Until a provider package is explicitly added, it stays console-only.
 * 
 * Usage:
 *   import { analytics } from '../services/analytics';
 *   analytics.track('bet_created', { sport: 'FOOTBALL', odds: 2.5 });
 *   analytics.screen('Feed');
 *   analytics.identify(userId, { is_tipster: true });
 */

// Event queue for calls made before analytics initialization.
let eventQueue: Array<{ type: string; args: any[] }> = [];
let isInitialized = false;

/**
 * Initialize analytics provider. Call once in _layout.tsx.
 * Does nothing if no API key is configured (dev mode).
 */
export async function initAnalytics(): Promise<void> {
    if (__DEV__) {
        console.log('[Analytics] No POSTHOG_KEY configured — running in dev mode (console only)');
    }
    isInitialized = true;
    flushQueue();
}

function flushQueue(): void {
    for (const event of eventQueue) {
        if (event.type === 'track') analytics.track(event.args[0], event.args[1]);
        if (event.type === 'screen') analytics.screen(event.args[0]);
        if (event.type === 'identify') analytics.identify(event.args[0], event.args[1]);
    }
    eventQueue = [];
}

export const analytics = {
    /**
     * Track a custom event.
     */
    track(event: string, properties?: Record<string, any>): void {
        if (!isInitialized) {
            eventQueue.push({ type: 'track', args: [event, properties] });
            return;
        }
        if (__DEV__) {
            console.log(`[Analytics] track: ${event}`, properties || '');
        }
        // When PostHog is wired: PostHog.capture(event, properties);
    },

    /**
     * Track a screen view.
     */
    screen(screenName: string): void {
        if (!isInitialized) {
            eventQueue.push({ type: 'screen', args: [screenName] });
            return;
        }
        if (__DEV__) {
            console.log(`[Analytics] screen: ${screenName}`);
        }
        // When PostHog is wired: PostHog.screen(screenName);
    },

    /**
     * Identify a user (after login).
     */
    identify(userId: string, traits?: Record<string, any>): void {
        if (!isInitialized) {
            eventQueue.push({ type: 'identify', args: [userId, traits] });
            return;
        }
        if (__DEV__) {
            console.log(`[Analytics] identify: ${userId}`, traits || '');
        }
        // When PostHog is wired: PostHog.identify(userId, traits);
    },

    /**
     * Reset analytics (on logout).
     */
    reset(): void {
        if (__DEV__) {
            console.log('[Analytics] reset');
        }
        // When PostHog is wired: PostHog.reset();
    },
};
