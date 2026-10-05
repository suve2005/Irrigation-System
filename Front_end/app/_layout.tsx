import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { Stack, useRouter, useSegments } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function RootLayout() {
    const router = useRouter();
    const segments = useSegments(); // Tracks which page the user is currently on
    const [isCheckingAuth, setIsCheckingAuth] = useState(true);

    useEffect(() => {
        const checkLoginState = async () => {
            try {
                // 1. Check if the farmerId exists in local storage
                const farmerId = await AsyncStorage.getItem('farmerId');

                // 2. Give the router a fraction of a second to mount (Expo Router quirk)
                setTimeout(() => {
                    if (farmerId) {
                        // If they have an ID, push them to the dashboard
                        router.replace('/Dashboard');
                    }
                    // Stop the loading spinner
                    setIsCheckingAuth(false);
                }, 100);

            } catch (error) {
                console.error("Error checking auth state:", error);
                setIsCheckingAuth(false);
            }
        };

        checkLoginState();
    }, []);

    // While checking storage, show a green loading spinner on a background that matches the app
    if (isCheckingAuth) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#22C55E" />
            </View>
        );
    }

    // Stack configuration hides the default ugly top headers from Expo
    return (
        <Stack screenOptions={{ headerShown: false }}>
            {/* The screens will automatically load here based on the URL */}
        </Stack>
    );
}

const styles = StyleSheet.create({
    loadingContainer: {
        flex: 1,
        backgroundColor: '#F8FAF5', // Matches your app's background theme
        justifyContent: 'center',
        alignItems: 'center',
    }
});