import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';
import { supabase } from '../../lib/supabase'; // Adjust path if necessary

const ScanQRScreen = () => {
    const router = useRouter();
    const [permission, requestPermission] = useCameraPermissions();

    const [scanned, setScanned] = useState(false);
    const [sensorId, setSensorId] = useState('');
    const [isVerifying, setIsVerifying] = useState(false); // New loading state

    if (!permission) return <View style={styles.container} />;

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

    const handleBarcodeScanned = ({ type, data }) => {
        setScanned(true);
        setSensorId(data);
    };

    // New verification logic
    const handleVerifyAndContinue = async () => {
        setIsVerifying(true);

        try {
            // Check Supabase for the scanned serial number
            const { data, error } = await supabase
                .from('sensors') // Change this if your table is named differently
                .select('serial_number')
                .eq('serial_number', sensorId)
                .maybeSingle(); // maybeSingle returns null if not found, instead of throwing an error

            if (error) {
                console.error("Database error:", error);
                Alert.alert("Verification Error", "Could not connect to the database to verify the sensor.");
                return;
            }

            if (!data) {
                // The serial number does not exist in the database
                Alert.alert(
                    "Invalid Sensor",
                    "This QR code does not match any registered Smart Agri sensors in our system.",
                    [{ text: "Try Again", onPress: () => setScanned(false) }] // Resets scanner
                );
            } else {
                // Match found! Proceed to the next step
                router.push({
                    pathname: '/register/details',
                    params: { deviceId: sensorId }
                });
            }
        } catch (err) {
            Alert.alert("Error", "An unexpected network error occurred.");
        } finally {
            setIsVerifying(false);
        }
    };

    return (
        <SafeAreaView style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.headerTitle}>Connect Device</Text>
                <Text style={styles.headerSubtitle}>
                    Scan the QR code printed on the back of your soil sensor.
                </Text>
            </View>

            <View style={styles.cameraContainer}>
                <CameraView
                    style={StyleSheet.absoluteFill}
                    facing="back"
                    onBarcodeScanned={scanned ? undefined : handleBarcodeScanned}
                    barcodeScannerSettings={{
                        barcodeTypes: ["qr"],
                    }}
                />

                <View style={styles.overlay}>
                    <View style={styles.scanBox} />
                </View>
            </View>

            <View style={styles.footer}>
                {scanned ? (
                    <View style={styles.successContainer}>
                        <Text style={styles.successText}>Scanned: {sensorId}</Text>

                        <TouchableOpacity
                            style={styles.primaryButton}
                            onPress={handleVerifyAndContinue}
                            disabled={isVerifying}
                        >
                            {isVerifying ? (
                                <ActivityIndicator color="#FFFFFF" />
                            ) : (
                                <Text style={styles.buttonText}>Verify & Continue</Text>
                            )}
                        </TouchableOpacity>

                        {/* Hide the scan again button while verifying */}
                        {!isVerifying && (
                            <TouchableOpacity
                                style={styles.secondaryButton}
                                onPress={() => setScanned(false)}
                            >
                                <Text style={styles.secondaryButtonText}>Scan Again</Text>
                            </TouchableOpacity>
                        )}
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
    container: { flex: 1, backgroundColor: '#F8FAF5' },
    centerContent: { flex: 1, justifyContent: 'center', paddingHorizontal: 24 },
    header: { paddingTop: 20, paddingHorizontal: 24, paddingBottom: 20 },
    headerTitle: { fontSize: 28, fontWeight: '800', color: '#166534', marginBottom: 8 },
    headerSubtitle: { fontSize: 16, color: '#6B7280', lineHeight: 22 },
    cameraContainer: {
        aspectRatio: 1,
        width: '100%',
        borderRadius: 24,
        overflow: 'hidden',
        backgroundColor: '#000',
    },
    overlay: { ...StyleSheet.absoluteFill, justifyContent: 'center', alignItems: 'center' },
    scanBox: { width: 250, height: 250, borderWidth: 2, borderColor: '#22C55E', borderRadius: 16, backgroundColor: 'rgba(255, 255, 255, 0.1)' },
    footer: { paddingHorizontal: 24, paddingVertical: 32, minHeight: 180, justifyContent: 'center' },
    scanningText: { textAlign: 'center', fontSize: 16, color: '#6B7280', fontWeight: '500' },
    successContainer: { width: '100%' },
    successText: { textAlign: 'center', fontSize: 18, fontWeight: '700', color: '#166534', marginBottom: 16 },
    primaryButton: { backgroundColor: '#22C55E', paddingVertical: 16, borderRadius: 16, alignItems: 'center', marginBottom: 12, minHeight: 56, justifyContent: 'center' },
    buttonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
    secondaryButton: { paddingVertical: 16, borderRadius: 16, alignItems: 'center', backgroundColor: '#E5E7EB' },
    secondaryButtonText: { color: '#4B5563', fontSize: 16, fontWeight: '600' },
    title: { fontSize: 24, fontWeight: '700', color: '#1F2937', marginBottom: 8, textAlign: 'center' },
    subtitle: { fontSize: 16, color: '#6B7280', textAlign: 'center', marginBottom: 32, lineHeight: 24 }
});