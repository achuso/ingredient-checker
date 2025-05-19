import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../config.dart';
import '../services/auth_service.dart';
import 'main_page.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _formKey = GlobalKey<FormState>();
  bool _isLogin = true;
  bool _loading = false;
  String _email = '', _password = '', _confirm = '';

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    _formKey.currentState!.save();

    setState(() => _loading = true);

    try {
      final endpoint = _isLogin ? '/auth/login' : '/auth/register';
      final resp = await http.post(
        Uri.parse('$apiBaseUrl$endpoint'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': _email, 'password': _password}),
      );

      if (resp.statusCode != 200 && resp.statusCode != 201) {
        throw Exception(jsonDecode(resp.body)['message'] ?? 'Auth failed');
      }

      final tokenString =
          jsonDecode(resp.body)['access_token'] ?? jsonDecode(resp.body)['token'];
      await AuthService().saveToken(tokenString);

      if (!mounted) return;
      Navigator.pushReplacement(
          context, MaterialPageRoute(builder: (_) => MainPage()));
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(32),
          child: Form(
            key: _formKey,
            child: Column(
              children: [
                Text(_isLogin ? 'Log in' : 'Register',
                    style:
                        const TextStyle(fontSize: 28, fontWeight: FontWeight.w700)),
                const SizedBox(height: 32),
                TextFormField(
                  key: const ValueKey('email'),
                  decoration: const InputDecoration(labelText: 'E-mail'),
                  keyboardType: TextInputType.emailAddress,
                  onSaved: (v) => _email = v!.trim(),
                  validator: (v) =>
                      v != null && v.contains('@') ? null : 'Enter a valid email',
                ),
                const SizedBox(height: 16),
                TextFormField(
                  key: const ValueKey('pw'),
                  decoration: const InputDecoration(labelText: 'Password'),
                  obscureText: true,
                  onSaved: (v) => _password = v!,
                  validator: (v) =>
                      (v != null && v.length >= 6) ? null : 'Min 6 chars',
                ),
                if (!_isLogin) ...[
                  const SizedBox(height: 16),
                  TextFormField(
                    key: const ValueKey('pw2'),
                    decoration:
                        const InputDecoration(labelText: 'Confirm password'),
                    obscureText: true,
                    onSaved: (v) => _confirm = v!,
                    validator: (v) => v == _password ? null : 'Passwords differ',
                  ),
                ],
                const SizedBox(height: 32),
                _loading
                    ? const CircularProgressIndicator()
                    : FilledButton(
                        onPressed: _submit,
                        child: Text(_isLogin ? 'Log in' : 'Create account'),
                      ),
                TextButton(
                  onPressed: () => setState(() => _isLogin = !_isLogin),
                  child: Text(_isLogin
                      ? 'Need an account? Register'
                      : 'Already have an account? Log in'),
                )
              ],
            ),
          ),
        ),
      ),
    );
  }
}
