import React, { useState, useEffect } from 'react';
import {
    StyleSheet, Text, View, ScrollView, TouchableOpacity, ActivityIndicator, Alert
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { supabase } from '../lib/supabase';

// Define your Python API URL (Use 10.0.2.2 for Android Emulator, or your computer's IP for a physical phone)
const API_BASE_URL = 'http://10.0.2.2:8000';

const DashboardScreen = () => {
    const router = useRouter();

    const [isLoading, setIsLoading] = useState(true);
    const [farmData, setFarmData] = useState(null);
    const [sensorData, setSensorData] = useState({
        temperature: '--',
        moisture: '--',
        humidity: '--',
        battery: '--',
    });

    // 1. Fetch Farm Info from Supabase
    useEffect(() => {
        const fetchFarmData = async () => {
            try {
                const farmerId = await AsyncStorage.getItem('farmerId');
                if (!farmerId) {
                    router.replace('/auth');
                    return;
                }

                const { data, error } = await supabase
                    .from('farms')
                    .select('location, plant_type, sensor_serial')
                    .eq('farmer_id', farmerId)
                    .single();

                if (error) throw error;
                setFarmData(data);

            } catch (error) {
                console.error("Error fetching farm:", error);
                Alert.alert("Error", "Could not load farm data.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchFarmData();
    }, []);

    // 2. Poll the Python Backend for live sensor data
    useEffect(() => {
        if (!farmData?.sensor_serial) return;

        const fetchLiveSensorData = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/sensor/${farmData.sensor_serial}`);
                if (!response.ok) throw new Error("Network response was not ok");

                const data = await response.json();
                setSensorData(data);
            } catch (error) {
                console.error("Error fetching sensor data from Python backend:", error);
            }
        };

        // Fetch immediately, then poll every 3 seconds
        fetchLiveSensorData();
        const pollingInterval = setInterval(fetchLiveSensorData, 3000);

        return () => clearInterval(pollingInterval);
    }, [farmData]); // This effect only runs AFTER farmData is loaded

    const handleLogout = async () => {
        await AsyncStorage.removeItem('farmerId');
        router.replace('/auth');
    };

    if (isLoading) {
        return (
            <SafeAreaView style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#22C55E" />
                <Text style={styles.loadingText}>Connecting to sensors...</Text>
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView style={styles.container}>
            <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>

                <View style={styles.header}>
                    <View>
                        <Text style={styles.greeting}>Overview</Text>
                        <Text style={styles.locationText}>
                            <Ionicons name="location" size={16} color="#22C55E" /> {farmData?.location || "Unknown Location"}
                        </Text>
                    </View>
                    <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
                        <Ionicons name="log-out-outline" size={24} color="#ef4444" />
                    </TouchableOpacity>
                </View>

                <View style={styles.statusCard}>
                    <View style={styles.statusDot} />
                    <Text style={styles.statusText}>Sensor {farmData?.sensor_serial} is Online</Text>
                    <Text style={styles.cropText}>Crop: {farmData?.plant_type}</Text>
                </View>

                <View style={styles.gridContainer}>
                    <View style={styles.card}>
                        <View style={[styles.iconContainer, { backgroundColor: '#FEF08A' }]}>
                            <Ionicons name="thermometer-outline" size={28} color="#CA8A04" />
                        </View>
                        <Text style={styles.cardTitle}>Soil Temp</Text>
                        <Text style={styles.cardValue}>{sensorData.temperature}°C</Text>
                        <Text style={styles.cardSubtext}>Optimal: 20-25°C</Text>
                    </View>

                    <View style={styles.card}>
                        <View style={[styles.iconContainer, { backgroundColor: '#BFDBFE' }]}>
                            <Ionicons name="water-outline" size={28} color="#2563EB" />
                        </View>
                        <Text style={styles.cardTitle}>Moisture</Text>
                        <Text style={styles.cardValue}>{sensorData.moisture}%</Text>
                        <Text style={styles.cardSubtext}>Well watered</Text>
                    </View>

                    <View style={styles.card}>
                        <View style={[styles.iconContainer, { backgroundColor: '#E9D5FF' }]}>
                            <Ionicons name="cloud-outline" size={28} color="#9333EA" />
                        </View>
                        <Text style={styles.cardTitle}>Air Humidity</Text>
                        <Text style={styles.cardValue}>{sensorData.humidity}%</Text>
                        <Text style={styles.cardSubtext}>Normal</Text>
                    </View>

                    <View style={styles.card}>
                        <View style={[styles.iconContainer, { backgroundColor: '#BBF7D0' }]}>
                            <Ionicons name="battery-half-outline" size={28} color="#16A34A" />
                        </View>
                        <Text style={styles.cardTitle}>Sensor Battery</Text>
                        <Text style={styles.cardValue}>{(sensorData.battery)}%</Text>
                        <Text style={styles.cardSubtext}>Good condition</Text>
                    </View>
                </View>

                <TouchableOpacity style={styles.actionButton} activeOpacity={0.8}>
                    <Ionicons name="water" size={20} color="#FFFFFF" style={{ marginRight: 8 }} />
                    <Text style={styles.actionButtonText}>Trigger Irrigation</Text>
                </TouchableOpacity>

            </ScrollView>
        </SafeAreaView>
    );
};

export default DashboardScreen;

// ... keep your existing styles ...
const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#F8FAF5' },
    loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F8FAF5' },
    loadingText: { marginTop: 16, fontSize: 16, color: '#4B5563', fontWeight: '500' },
    scrollContent: { padding: 24 },
    header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
    greeting: { fontSize: 28, fontWeight: '800', color: '#166534', marginBottom: 4 },
    locationText: { fontSize: 14, color: '#4B5563', fontWeight: '600' },
    logoutButton: { padding: 8, backgroundColor: '#FEE2E2', borderRadius: 12 },
    statusCard: { backgroundColor: '#166534', padding: 16, borderRadius: 16, marginBottom: 24, flexDirection: 'row', alignItems: 'center', shadowColor: '#166534', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.2, shadowRadius: 8, elevation: 4 },
    statusDot: { width: 12, height: 12, borderRadius: 6, backgroundColor: '#4ADE80', marginRight: 12 },
    statusText: { color: '#FFFFFF', fontSize: 15, fontWeight: '600', flex: 1 },
    cropText: { color: '#BBF7D0', fontSize: 14, fontWeight: '500' },
    gridContainer: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
    card: { width: '48%', backgroundColor: '#FFFFFF', padding: 16, borderRadius: 16, marginBottom: 16, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.05, shadowRadius: 8, elevation: 2 },
    iconContainer: { width: 48, height: 48, borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginBottom: 16 },
    cardTitle: { fontSize: 14, color: '#6B7280', fontWeight: '600', marginBottom: 4 },
    cardValue: { fontSize: 24, fontWeight: '800', color: '#1F2937', marginBottom: 4 },
    cardSubtext: { fontSize: 12, color: '#22C55E', fontWeight: '500' },
    actionButton: { backgroundColor: '#2563EB', paddingVertical: 16, borderRadius: 16, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', marginTop: 8, shadowColor: '#2563EB', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 8, elevation: 4 },
    actionButtonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' }
});