import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';

const ScanQRScreen = () => {
    const router = useRouter();

    // Expo Camera hooks for handling permissions natively
    const [permission, requestPermission] = useCameraPermissions();

    // State to hold the scanned data and prevent multiple scans
    const [scanned, setScanned] = useState(false);
    const [sensorId, setSensorId] = useState('');

    // 1. Loading state while checking permissions
    if (!permission) {
        return <View style={styles.container} />;
    }

    // 2. Permission denied / not granted yet UI
    if (!permission.granted) {
        return (
            <SafeAreaView style={styles.container}>
                <View style={styles.centerContent}>
                    <Text style={styles.title}>Camera Access Required</Text>
                    <Text style={styles.subtitle}>
                        We need access to your camera to scan the QR code on your Smart Agri sensor.
                    </Text>
                    <TouchableOpacity style={styles.primaryButton} onPress={requestPermission}>
                        <Text style={styles.buttonText}>Allow Camera</Text>
                    </TouchableOpacity>
                </View>
            </SafeAreaView>
        );
    }

    // 3. Handle what happens when a QR code is detected
    const handleBarcodeScanned = ({ type, data }) => {
        setScanned(true);
        setSensorId(data); // Save the QR code text (e.g., the sensor serial number)
        console.log(`Scanned QR Type: ${type}, Data: ${data}`);
    };

    // 4. Navigate to the next page, passing the scanned ID
    const handleContinue = () => {
        // We will create this 'details' page next
        router.push({
            pathname: '/register/details',
            params: { deviceId: sensorId }
        });
    };

    return (
        <SafeAreaView style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.headerTitle}>Connect Device</Text>
                <Text style={styles.headerSubtitle}>
                    Scan the QR code printed on the back of your soil sensor.
                </Text>
            </View>

            {/* Camera Viewport */}
            <View style={styles.cameraContainer}>
                <CameraView
                    style={styles.absoluteFillObject}
                    facing="back"
                    onBarcodeScanned={scanned ? undefined : handleBarcodeScanned}
                    barcodeScannerSettings={{
                        barcodeTypes: ["qr"], // Only look for QR codes to save battery
                    }}
                />

                {/* Visual Overlay to guide the user */}
                <View style={styles.absoluteFillObject}>
                    <View style={styles.scanBox} />
                </View>
            </View>

            {/* Bottom Action Area */}
            <View style={styles.footer}>
                {scanned ? (
                    <View style={styles.successContainer}>
                        <Text style={styles.successText}>Device Found: {sensorId}</Text>
                        <TouchableOpacity style={styles.primaryButton} onPress={handleContinue}>
                            <Text style={styles.buttonText}>Continue Setup</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                            style={styles.secondaryButton}
                            onPress={() => setScanned(false)}
                        >
                            <Text style={styles.secondaryButtonText}>Scan Again</Text>
                        </TouchableOpacity>
                    </View>
                ) : (
                    <Text style={styles.scanningText}>Looking for QR code...</Text>
                )}
            </View>
        </SafeAreaView>
    );
};

export default ScanQRScreen;

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F8FAF5',
    },
    centerContent: {
        flex: 1,
        justifyContent: 'center',
        paddingHorizontal: 24,
    },
    header: {
        paddingTop: 20,
        paddingHorizontal: 24,
        paddingBottom: 20,
    },
    headerTitle: {
        fontSize: 28,
        fontWeight: '800',
        color: '#166534',
        marginBottom: 8,
    },
    headerSubtitle: {
        fontSize: 16,
        color: '#6B7280',
        lineHeight: 22,
    },
    cameraContainer: {
        flex: 1,
        marginHorizontal: 24,
        borderRadius: 24,
        overflow: 'hidden', // Ensures the camera doesn't bleed outside the rounded corners
        backgroundColor: '#000',
    },
    absoluteFillObject: {
        // ...StyleSheet.absoluteFillObject,
        justifyContent: 'center',
        alignItems: 'center',
    },
    scanBox: {
        width: 250,
        height: 250,
        borderWidth: 2,
        borderColor: '#22C55E', // Green targeting box
        borderRadius: 16,
        backgroundColor: 'rgba(255, 255, 255, 0.1)', // Very slight white tint inside the box
    },
    footer: {
        paddingHorizontal: 24,
        paddingVertical: 32,
        minHeight: 180,
        justifyContent: 'center',
    },
    scanningText: {
        textAlign: 'center',
        fontSize: 16,
        color: '#6B7280',
        fontWeight: '500',
    },
    successContainer: {
        width: '100%',
    },
    successText: {
        textAlign: 'center',
        fontSize: 18,
        fontWeight: '700',
        color: '#166534',
        marginBottom: 16,
    },
    primaryButton: {
        backgroundColor: '#22C55E',
        paddingVertical: 16,
        borderRadius: 16,
        alignItems: 'center',
        marginBottom: 12,
    },
    buttonText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '700',
    },
    secondaryButton: {
        paddingVertical: 16,
        borderRadius: 16,
        alignItems: 'center',
        backgroundColor: '#E5E7EB',
    },
    secondaryButtonText: {
        color: '#4B5563',
        fontSize: 16,
        fontWeight: '600',
    },
    title: {
        fontSize: 24,
        fontWeight: '700',
        color: '#1F2937',
        marginBottom: 8,
        textAlign: 'center',
    },
    subtitle: {
        fontSize: 16,
        color: '#6B7280',
        textAlign: 'center',
        marginBottom: 32,
        lineHeight: 24,
    }
});