import 'package:flutter/material.dart';
import 'auth_screen.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final primary = Theme.of(context).colorScheme.primary;

    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text('Ingredient Checker',
                  style: TextStyle(fontSize: 30, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Text('Scan labels • Stay safe',
                  style: TextStyle(
                      fontSize: 18,
                      color: Theme.of(context).colorScheme.outline)),
              const SizedBox(height: 60),
              FilledButton(
                style: FilledButton.styleFrom(backgroundColor: primary),
                onPressed: () => Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const AuthScreen()),
                ),
                child: const Text('Log in'),
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                      builder: (_) => const AuthScreen(startOnRegister: true)),
                ),
                child: const Text("Don't have an account? Register!"),
              )
            ],
          ),
        ),
      ),
    );
  }
}
