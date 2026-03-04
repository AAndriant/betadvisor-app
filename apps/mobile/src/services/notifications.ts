/**
 * S8-03: Push notification setup for Expo.
 * Handles permission request, token registration, and notification listeners.
 */
import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { api } from './api';

// Configure how notifications appear when app is in foreground
Notifications.setNotificationHandler({
    handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
        shouldShowBanner: true,
        shouldShowList: true,
    }),
});

/**
 * Request push notification permissions and register the token with the backend.
 */
export async function registerForPushNotifications(): Promise<string | null> {
    // Push notifications only work on physical devices
    if (!Device.isDevice) {
        console.log('Push notifications require a physical device');
        return null;
    }

    try {
        // Check existing permissions
        const { status: existingStatus } = await Notifications.getPermissionsAsync();
        let finalStatus = existingStatus;

        // Request if not already granted
        if (existingStatus !== 'granted') {
            const { status } = await Notifications.requestPermissionsAsync();
            finalStatus = status;
        }

        if (finalStatus !== 'granted') {
            console.log('Push notification permission denied');
            return null;
        }

        // Get Expo push token
        const tokenData = await Notifications.getExpoPushTokenAsync({
            projectId: undefined, // Uses expo-constants project ID
        });

        const pushToken = tokenData.data;
        console.log('Expo push token:', pushToken);

        // Register token with backend
        await registerTokenWithBackend(pushToken);

        // Android-specific: set notification channel
        if (Platform.OS === 'android') {
            await Notifications.setNotificationChannelAsync('default', {
                name: 'BetAdvisor',
                importance: Notifications.AndroidImportance.MAX,
                vibrationPattern: [0, 250, 250, 250],
                lightColor: '#10b981',
            });
        }

        return pushToken;
    } catch (error) {
        console.error('Error registering for push notifications:', error);
        return null;
    }
}

/**
 * Register the push token with the BetAdvisor backend.
 */
async function registerTokenWithBackend(token: string): Promise<void> {
    try {
        await api.post('/api/me/push-token/', {
            token,
            device_name: `${Device.modelName || 'Unknown'} (${Platform.OS})`,
        });
        console.log('Push token registered with backend');
    } catch (error) {
        console.error('Failed to register push token with backend:', error);
    }
}

/**
 * Add a listener for incoming notifications (foreground).
 */
export function addNotificationListener(
    handler: (notification: Notifications.Notification) => void
) {
    return Notifications.addNotificationReceivedListener(handler);
}

/**
 * Add a listener for when a user taps on a notification.
 */
export function addNotificationResponseListener(
    handler: (response: Notifications.NotificationResponse) => void
) {
    return Notifications.addNotificationResponseReceivedListener(handler);
}
