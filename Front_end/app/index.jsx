import React from 'react';
// 1. Remove SafeAreaView from the react-native import
import { StyleSheet, Text, View, TouchableOpacity } from 'react-native';
// 2. Import it from react-native-safe-area-context instead
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';

const Index = () => {
    const router = useRouter();
    return (
        <SafeAreaView style={styles.container}>
            <View style={styles.content}>

                {/* Header Section */}
                <View style={styles.headerContainer}>
                    <Text style={styles.title}>Welcome to</Text>
                    <Text style={styles.brandTitle}>Smart Agri</Text>
                    <Text style={styles.subtitle}>
                        Monitor your fields, optimize irrigation, and maximize your crop yield with real-time sensor data.
                    </Text>
                </View>

                {/* Action Section */}
                <View style={styles.actionContainer}>
                    <TouchableOpacity
                        style={styles.primaryButton}
                        activeOpacity={0.8}
                        onPress={() => {
                            router.push('/Register/login')
                        }
                        }
                    >
                        <Text style={styles.buttonText}>Get Started</Text>
                    </TouchableOpacity>
                </View>

            </View>
        </SafeAreaView>
    );
};

export default Index;

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F8FAF5',
    },
    content: {
        flex: 1,
        paddingHorizontal: 24,
        justifyContent: 'space-between',
        paddingTop: 80,
        paddingBottom: 40,
    },
    headerContainer: {
        alignItems: 'flex-start',
    },
    title: {
        fontSize: 28,
        fontWeight: '400',
        color: '#4B5563',
        marginBottom: 4,
    },
    brandTitle: {
        fontSize: 40,
        fontWeight: '800',
        color: '#166534',
        marginBottom: 16,
        letterSpacing: -0.5,
    },
    subtitle: {
        fontSize: 16,
        color: '#6B7280',
        lineHeight: 24,
        paddingRight: 20,
    },
    actionContainer: {
        width: '100%',
    },
    primaryButton: {
        backgroundColor: '#22C55E',
        paddingVertical: 16,
        borderRadius: 16,
        alignItems: 'center',
        shadowColor: '#22C55E',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 4,
    },
    buttonText: {
        color: '#FFFFFF',
        fontSize: 18,
        fontWeight: '700',
    }
});