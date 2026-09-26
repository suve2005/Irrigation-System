import React, { useState } from 'react';
import {
    StyleSheet,
    Text,
    View,
    TextInput,
    TouchableOpacity,
    KeyboardAvoidingView,
    Platform,
    ActivityIndicator,
    Alert
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as Location from 'expo-location';
import { Ionicons } from '@expo/vector-icons'; // Built-in Expo icon library


const DetailsScreen = () => {
    const router = useRouter();
    const { deviceId } = useLocalSearchParams();

    const [location, setLocation] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    // Loading state for the GPS fetch
    const [isFetchingLocation, setIsFetchingLocation] = useState(false);

    const handleGetLocation = async () => {
        setIsFetchingLocation(true);
        try {
            // 1. Ask the user for GPS hardware permission
            let { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert("Permission Denied", "Please allow location access to automatically find your field.");
                setIsFetchingLocation(false);
                return;
            }

            // 2. Fetch the exact GPS coordinates
            let locationData = await Location.getCurrentPositionAsync({});
            const { latitude, longitude } = locationData.coords;

            // 3. Convert coordinates into a human-readable street address
            let address = await Location.reverseGeocodeAsync({ latitude, longitude });

            if (address.length > 0) {
                const place = address[0];
                // Formats it like "Main Street, Springfield"
                const formattedName = [place.name, place.street, place.city].filter(Boolean).join(', ');
                setLocation(formattedName);
            } else {
                // Fallback to exact coordinates if the address lookup fails
                setLocation(`Lat: ${latitude.toFixed(4)}, Lon: ${longitude.toFixed(4)}`);
            }
        } catch (error) {
            Alert.alert("Error", "Could not fetch your location. Please check your GPS signal.");
            console.error(error);
        } finally {
            setIsFetchingLocation(false);
        }
    };

    const handleCompleteSetup = () => {
        console.log("Device:", deviceId);
        console.log("Location:", location);
        console.log("Username:", username);
        console.log("Password:", password);

        alert("Registration Complete! Your sensor is linked.");
    };

    return (
        <SafeAreaView style={styles.container}>
            <KeyboardAvoidingView
                style={styles.keyboardView}
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            >
                <View style={styles.content}>

                    <View style={styles.headerContainer}>
                        <Text style={styles.title}>Sensor Details</Text>
                        <Text style={styles.subtitle}>
                            Link your newly scanned device to a farm location and create your account.
                        </Text>
                    </View>

                    <View style={styles.sensorBadge}>
                        <Text style={styles.sensorBadgeLabel}>Linked Device ID:</Text>
                        <Text style={styles.sensorBadgeValue}>{deviceId || "Unknown Device"}</Text>
                    </View>

                    <View style={styles.formContainer}>

                        {/* Updated Location Input with GPS Button */}
                        <View style={styles.inputGroup}>
                            <Text style={styles.inputLabel}>Farm / Field Location</Text>
                            <View style={styles.locationRow}>
                                <TextInput
                                    style={[styles.input, styles.locationInput]}
                                    placeholder="e.g., North Field Greenhouse"
                                    value={location}
                                    onChangeText={setLocation}
                                />
                                <TouchableOpacity
                                    style={styles.locationButton}
                                    activeOpacity={0.8}
                                    onPress={handleGetLocation}
                                    disabled={isFetchingLocation}
                                >
                                    {isFetchingLocation ? (
                                        <ActivityIndicator color="#FFFFFF" size="small" />
                                    ) : (
                                        <Ionicons name="location" size={24} color="#FFFFFF" />
                                    )}
                                </TouchableOpacity>
                            </View>
                        </View>

                        <View style={styles.inputGroup}>
                            <Text style={styles.inputLabel}>Username</Text>
                            <TextInput
                                style={styles.input}
                                placeholder="farmer_john"
                                value={username}
                                onChangeText={setUsername}
                                autoCapitalize="none"
                            />
                        </View>

                        <View style={styles.inputGroup}>
                            <Text style={styles.inputLabel}>Password</Text>
                            <TextInput
                                style={styles.input}
                                placeholder="••••••••"
                                value={password}
                                onChangeText={setPassword}
                                secureTextEntry
                            />
                        </View>
                    </View>

                    <View style={styles.actionContainer}>
                        <TouchableOpacity style={styles.primaryButton} activeOpacity={0.8} onPress={handleCompleteSetup}>
                            <Text style={styles.buttonText}>Complete Registration</Text>
                        </TouchableOpacity>
                        <TouchableOpacity onPress={() => router.back()}>
                            <Text style={styles.cancelText}>Go Back</Text>
                        </TouchableOpacity>
                    </View>

                </View>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
};

export default DetailsScreen;

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#F8FAF5', padding: 2, paddingVertical: 2 },
    keyboardView: { flex: 1 },
    content: { flex: 1, paddingHorizontal: 24, justifyContent: 'center' },
    headerContainer: { marginBottom: 24 },
    title: { fontSize: 32, fontWeight: '800', color: '#166534', marginBottom: 8 },
    subtitle: { fontSize: 16, color: '#6B7280', lineHeight: 24 },
    sensorBadge: {
        backgroundColor: '#DCFCE7',
        padding: 16,
        borderRadius: 12,
        marginBottom: 32,
        borderWidth: 1,
        borderColor: '#86EFAC',
    },
    sensorBadgeLabel: { fontSize: 12, color: '#166534', fontWeight: '600', textTransform: 'uppercase', marginBottom: 4 },
    sensorBadgeValue: { fontSize: 16, color: '#14532D', fontWeight: '700' },
    formContainer: { marginBottom: 32 },
    inputGroup: { marginBottom: 16 },
    inputLabel: { fontSize: 14, fontWeight: '600', color: '#4B5563', marginBottom: 8 },

    // --- New Styles for the Location Row ---
    locationRow: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    input: {
        backgroundColor: '#FFFFFF',
        borderWidth: 1,
        borderColor: '#E5E7EB',
        borderRadius: 12,
        paddingVertical: 14,
        paddingHorizontal: 16,
        fontSize: 16,
        color: '#1F2937',
    },
    locationInput: {
        flex: 1, // Takes up remaining space
        borderTopRightRadius: 0,
        borderBottomRightRadius: 0,
        borderRightWidth: 0, // Removes double border between input and button
    },
    locationButton: {
        backgroundColor: '#22C55E',
        paddingHorizontal: 16,
        height: '100%',
        justifyContent: 'center',
        alignItems: 'center',
        borderTopRightRadius: 12,
        borderBottomRightRadius: 12,
        borderWidth: 1,
        borderColor: '#22C55E',
    },
    // ---------------------------------------

    actionContainer: { width: '100%', alignItems: 'center' },
    primaryButton: {
        backgroundColor: '#22C55E',
        paddingVertical: 16,
        borderRadius: 16,
        alignItems: 'center',
        width: '100%',
        shadowColor: '#22C55E',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 4,
        marginBottom: 16,
    },
    buttonText: { color: '#FFFFFF', fontSize: 18, fontWeight: '700' },
    cancelText: { color: '#6B7280', fontSize: 16, fontWeight: '600', padding: 8 }
});