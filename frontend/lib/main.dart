import 'package:flutter/material.dart';

import 'screens/welcome_screen.dart';
import 'screens/auth_screen.dart';
import 'screens/main_page.dart';
import 'services/auth_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const IngredientCheckerApp());
}

class IngredientCheckerApp extends StatelessWidget {
  const IngredientCheckerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Ingredient Checker',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: Colors.indigo,
        useMaterial3: true,
      ),
      home: const _SplashDecider(),
      routes: {
        '/welcome': (context) => const WelcomeScreen(),
        '/auth': (context) => const AuthScreen(),
        '/main': (context) => MainPage(),
      },
    );
  }
}

// Checks where to land based on whether the user is logged in (has valid JWT) or not
class _SplashDecider extends StatelessWidget {
  const _SplashDecider();

  Future<bool> _hasValidToken() => AuthService().hasValidToken();

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<bool>(
      future: _hasValidToken(),
      builder: (ctx, snap) {
        if (!snap.hasData) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        return snap.data! ? MainPage() : const WelcomeScreen();
      },
    );
  }
}
