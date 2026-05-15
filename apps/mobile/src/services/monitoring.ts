const SENTRY_DSN = process.env.EXPO_PUBLIC_SENTRY_DSN;

let initialized = false;

export async function initMonitoring(): Promise<void> {
    if (initialized || !SENTRY_DSN) {
        initialized = true;
        return;
    }

    try {
        const packageName = '@sentry/react-native';
        const sentry = await import(packageName);
        if (sentry && 'init' in sentry) {
            (sentry as any).init({
                dsn: SENTRY_DSN,
                enableAutoSessionTracking: true,
            });
        }
    } catch {
        if (__DEV__) {
            console.log('[Monitoring] Sentry package unavailable; monitoring disabled');
        }
    } finally {
        initialized = true;
    }
}
