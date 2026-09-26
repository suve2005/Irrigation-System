import React, { useState } from 'react';
import {
    StyleSheet,
    Text,
    View,
    TextInput,
    TouchableOpacity,
    KeyboardAvoidingView,
    Platform
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router'; // For navigation later

const AuthScreen = () => {
    const router = useRouter();

    // State to toggle between Login and Register modes
    const [isLogin, setIsLogin] = useState(true);

    // Form state
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleAuthenticate = () => {
        if (isLogin) {
            console.log("Logging in with:", email, password);
            // After successful login, route to dashboard: router.replace('/dashboard')
        } else {
            console.log("Registering:", name, email, password);
            // After successful registration, route to dashboard
        }
    };

    return (
        <SafeAreaView style={styles.container}>
            {/* KeyboardAvoidingView pushes the content up when the keyboard opens */}
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
                        {/* Only show Name field if the user is registering */}
                        {!isLogin && (
                            <View style={styles.inputGroup}>
                                <Text style={styles.inputLabel}>Full Name</Text>
                                <TextInput
                                    style={styles.input}
                                    placeholder="John Doe"
                                    value={name}
                                    onChangeText={setName}
                                    autoCapitalize="words"
                                />
                            </View>
                        )}

                        <View style={styles.inputGroup}>
                            <Text style={styles.inputLabel}>Email Address</Text>
                            <TextInput
                                style={styles.input}
                                placeholder="farmer@smartagri.com"
                                value={email}
                                onChangeText={setEmail}
                                keyboardType="email-address"
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
                                secureTextEntry // Hides the password
                            />
                        </View>

                        {/* Forgot Password Link (Only on Login) */}
                        {isLogin && (
                            <TouchableOpacity style={styles.forgotPassword}>
                                <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
                            </TouchableOpacity>
                        )}
                    </View>

                    {/* Action Section */}
                    <View style={styles.actionContainer}>
                        <TouchableOpacity
                            style={styles.primaryButton}
                            activeOpacity={0.8}
                            onPress={handleAuthenticate}
                        >
                            <Text style={styles.buttonText}>
                                Sign In
                            </Text>
                        </TouchableOpacity>

                        {/* Toggle between Login and Register */}
                        <View style={styles.toggleContainer}>
                            <Text style={styles.toggleText}>
                                Don't have an account?
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
        justifyContent: 'center', // Centers the form on the screen
    },
    headerContainer: {
        marginBottom: 32,
    },
    brandTitle: {
        fontSize: 16,
        fontWeight: '700',
        color: '#22C55E', // Green accent
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