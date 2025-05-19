import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../config.dart';
import 'main_page.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  bool isLogin = true;
  bool isButtonEnabled = false;
  bool isLoading = false;

  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  final confirmPasswordController = TextEditingController();

  @override
  void initState() {
    super.initState();
    emailController.addListener(_validateForm);
    passwordController.addListener(_validateForm);
    confirmPasswordController.addListener(_validateForm);
  }

  void _validateForm() {
    final email = emailController.text.trim();
    final password = passwordController.text.trim();
    final confirm = confirmPasswordController.text.trim();

    setState(() {
      isButtonEnabled = isLogin
          ? email.isNotEmpty && password.isNotEmpty
          : email.isNotEmpty && password.isNotEmpty && confirm.isNotEmpty;
    });
  }

  Future<void> _loginUser() async {
    final email = emailController.text.trim();
    final password = passwordController.text.trim();
    
    final loginUrl = isLogin ? '$apiBaseUrl/auth/login' : '$apiBaseUrl/auth/register';


    setState(() => isLoading = true);

    await Future.delayed(Duration.zero);

    try {
      final response = await http.post(
        Uri.parse(loginUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password}),
      );

      if (response.statusCode == 200) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => MainPage()),
        );
      } else {
        final errMsg = jsonDecode(response.body)['message'] ?? 'Login failed';
        _showError(errMsg);
      }
    } catch (e) {
      _showError('Network error. Please try again.');
    } finally {
      setState(() => isLoading = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFCFAFF),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        foregroundColor: Colors.black,
        elevation: 0,
        title: Text(isLogin ? 'Log In' : 'Register'),
        centerTitle: true,
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _buildInputField(emailController, 'Email'),
              const SizedBox(height: 16),
              _buildInputField(passwordController, 'Password', obscure: true),
              if (!isLogin) ...[
                const SizedBox(height: 16),
                _buildInputField(confirmPasswordController, 'Confirm password', obscure: true),
              ],
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                child: TextButton(
                  onPressed: isButtonEnabled && !isLoading
                      ? () {
                          if (isLogin) {
                            _loginUser();
                          }
                        }
                      : null,
                  style: TextButton.styleFrom(
                    backgroundColor: isButtonEnabled
                        ? const Color(0xFF1D4ED8)
                        : const Color(0xFFE0E0E0),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  child: isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : Text(
                          isLogin ? 'Log in' : 'Register',
                          style: TextStyle(
                            fontSize: 16,
                            color: isButtonEnabled ? Colors.white : Colors.grey.shade600,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                ),
              ),
              TextButton(
                onPressed: () {
                  setState(() {
                    isLogin = !isLogin;
                    _validateForm();
                  });
                },
                child: Text(
                  isLogin
                      ? "Don't have an account? Register"
                      : "Already have an account? Log in",
                  style: const TextStyle(color: Color(0xFF1D4ED8)),
                ),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInputField(TextEditingController controller, String label,
      {bool obscure = false}) {
    return TextField(
      controller: controller,
      obscureText: obscure,
      decoration: InputDecoration(
        labelText: label,
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(vertical: 18, horizontal: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
        ),
      ),
    );
  }
}

