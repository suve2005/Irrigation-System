import React, { useState } from 'react';
import {
    StyleSheet,
    Text,
    View,
    TextInput,
    TouchableOpacity,
    KeyboardAvoidingView,
    Platform,
    Alert,
    ActivityIndicator
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { supabase } from '../../lib/supabase'; // Adjust path if necessary based on your folder structure

const AuthScreen = () => {
    const router = useRouter();

    // Form and loading state
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleAuthenticate = async () => {
        if (!username || !password) {
            Alert.alert("Missing Fields", "Please enter your username and password.");
            return;
        }

        setIsLoading(true);

        try {
            // Query the custom 'farmers' table we created earlier
            const { data: farmer, error } = await supabase
                .from('farmers')
                .select('*')
                .eq('username', username.trim().toLowerCase())
                .single(); // .single() expects exactly one row

            if (error || !farmer) {
                // If the user doesn't exist, Supabase will throw a "Row not found" error
                Alert.alert("Login Failed", "Invalid username or password.");
                setIsLoading(false);
                return;
            }

            // Verify password (prototype plain-text check)
            if (farmer.password !== password) {
                Alert.alert("Login Failed", "Invalid username or password.");
                setIsLoading(false);
                return;
            }

            // Success! Save the farmer ID to local storage so they stay logged in
            await AsyncStorage.setItem('farmerId', farmer.id);

            console.log("Logged in successfully!", farmer.username);

            // Navigate to the Dashboard (uncomment when you build the dashboard page)
            router.replace('../Dashboard');

        } catch (error) {
            Alert.alert("Error", "An unexpected error occurred while logging in.");
            console.error("Login Error:", error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <SafeAreaView style={styles.container}>
            <KeyboardAvoidingView
                style={styles.keyboardView}
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            >
                <View style={styles.content}>

                    {/* Header Section */}
                    <View style={styles.headerContainer}>
                        <Text style={styles.brandTitle}>Smart Agri</Text>
                        <Text style={styles.title}>
                            Welcome Back
                        </Text>
                        <Text style={styles.subtitle}>
                            Sign in to monitor your fields and sensor data.
                        </Text>
                    </View>

                    {/* Form Section */}
                    <View style={styles.formContainer}>
                        <View style={styles.inputGroup}>
                            <Text style={styles.inputLabel}>Username</Text>
                            <TextInput
                                style={styles.input}
                                placeholder="farmer_john"
                                value={username}
                                onChangeText={setUsername}
                                autoCapitalize="none"
                                autoCorrect={false}
                            />
                        </View>

                        <View style={styles.inputGroup}>
                            <Text style={styles.inputLabel}>Password</Text>
                            <TextInput
                                style={styles.input}
                                placeholder="••••••••"
                                value={password}
                                onChangeText={setPassword}
                                secureTextEntry // Hides the password
                            />
                        </View>

                        <TouchableOpacity style={styles.forgotPassword}>
                            <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
                        </TouchableOpacity>
                    </View>

                    {/* Action Section */}
                    <View style={styles.actionContainer}>
                        <TouchableOpacity
                            style={styles.primaryButton}
                            activeOpacity={0.8}
                            onPress={handleAuthenticate}
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <ActivityIndicator color="#FFFFFF" />
                            ) : (
                                <Text style={styles.buttonText}>Sign In</Text>
                            )}
                        </TouchableOpacity>

                        {/* Navigation to Registration */}
                        <View style={styles.toggleContainer}>
                            <Text style={styles.toggleText}>
                                Don't have an account?{" "}
                            </Text>
                            <TouchableOpacity onPress={() => router.push('/Register/scan')}>
                                <Text style={styles.toggleLink}>
                                    Sign Up
                                </Text>
                            </TouchableOpacity>
                        </View>
                    </View>

                </View>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
};

export default AuthScreen;

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F8FAF5',
    },
    keyboardView: {
        flex: 1,
    },
    content: {
        flex: 1,
        paddingHorizontal: 24,
        justifyContent: 'center',
    },
    headerContainer: {
        marginBottom: 32,
    },
    brandTitle: {
        fontSize: 16,
        fontWeight: '700',
        color: '#22C55E',
        textTransform: 'uppercase',
        letterSpacing: 1,
        marginBottom: 8,
    },
    title: {
        fontSize: 32,
        fontWeight: '800',
        color: '#166534',
        marginBottom: 8,
    },
    subtitle: {
        fontSize: 16,
        color: '#6B7280',
        lineHeight: 24,
    },
    formContainer: {
        marginBottom: 32,
    },
    inputGroup: {
        marginBottom: 16,
    },
    inputLabel: {
        fontSize: 14,
        fontWeight: '600',
        color: '#4B5563',
        marginBottom: 8,
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
    forgotPassword: {
        alignSelf: 'flex-end',
        marginTop: 4,
    },
    forgotPasswordText: {
        color: '#22C55E',
        fontSize: 14,
        fontWeight: '600',
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
        marginBottom: 24,
        minHeight: 56, // Prevents button from shrinking when loading spinner appears
        justifyContent: 'center',
    },
    buttonText: {
        color: '#FFFFFF',
        fontSize: 18,
        fontWeight: '700',
    },
    toggleContainer: {
        flexDirection: 'row',
        justifyContent: 'center',
    },
    toggleText: {
        color: '#6B7280',
        fontSize: 15,
    },
    toggleLink: {
        color: '#166534',
        fontSize: 15,
        fontWeight: '700',
    }
});