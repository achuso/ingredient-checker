import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../config.dart';
import '../services/auth_service.dart';
import 'main_page.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key, this.startOnRegister = false});
  final bool startOnRegister;

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _pw1 = TextEditingController();
  final _pw2 = TextEditingController();

  bool _isLogin = true;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _isLogin = !widget.startOnRegister;
  }

  @override
  void dispose() {
    _email.dispose();
    _pw1.dispose();
    _pw2.dispose();
    super.dispose();
  }

  String? _pwVal(String? v) =>
      v != null && v.length >= 6 ? null : 'Min 6 chars';
  String? _pw2Val(String? v) => v == _pw1.text ? null : 'Passwords differ';

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    setState(() => _busy = true);

    try {
      final email = _email.text.trim();
      final pw = _pw1.text;

      if (_isLogin) {
        await _login(email, pw);
        if (!mounted) return;
        Navigator.pushReplacement(
            context, MaterialPageRoute(builder: (_) => const MainPage()));
      } else {
        await _register(email, pw);
        if (!mounted) return;
        setState(() => _isLogin = true);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Registration successful – please log in.')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _register(String email, String pw) async {
    final r = await http.post(Uri.parse('$apiBaseUrl/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': pw}));
    if (r.statusCode != 200 && r.statusCode != 201) {
      throw Exception(jsonDecode(r.body)['detail'] ?? 'Register failed');
    }
  }

  Future<void> _login(String email, String pw) async {
    final r = await http.post(Uri.parse('$apiBaseUrl/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': pw}));
    if (r.statusCode != 200) {
      throw Exception(jsonDecode(r.body)['detail'] ?? 'Login failed');
    }
    await AuthService().saveToken(jsonDecode(r.body)['access_token']);
  }

  @override
  Widget build(BuildContext c) {
    final primary = Theme.of(c).colorScheme.primary;
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(32),
          child: Form(
            key: _form,
            child: Column(
              children: [
                Text(_isLogin ? 'Log in' : 'Register',
                    style: Theme.of(c).textTheme.headlineMedium),
                const SizedBox(height: 32),
                TextFormField(
                  controller: _email,
                  decoration: const InputDecoration(labelText: 'E-mail'),
                  keyboardType: TextInputType.emailAddress,
                  validator: (v) =>
                      v != null && v.contains('@') ? null : 'Invalid e-mail',
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _pw1,
                  decoration: const InputDecoration(labelText: 'Password'),
                  obscureText: true,
                  validator: _pwVal,
                ),
                if (!_isLogin) ...[
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _pw2,
                    decoration:
                        const InputDecoration(labelText: 'Confirm password'),
                    obscureText: true,
                    validator: _pw2Val,
                  ),
                ],
                const SizedBox(height: 32),
                _busy
                    ? const CircularProgressIndicator()
                    : FilledButton(
                        style:
                            FilledButton.styleFrom(backgroundColor: primary),
                        onPressed: _submit,
                        child: Text(_isLogin ? 'Log in' : 'Create account'),
                      ),
                TextButton(
                  onPressed: () => setState(() => _isLogin = !_isLogin),
                  child: Text(_isLogin
                      ? 'Need an account? Register'
                      : 'Already have an account? Log in',
                      style: TextStyle(color: primary)),
                )
              ],
            ),
          ),
        ),
      ),
    );
  }
}
