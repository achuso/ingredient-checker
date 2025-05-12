import 'package:flutter/material.dart';
import 'screens/welcome_screen.dart';
import 'screens/auth_screen.dart';

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
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: const WelcomeScreen(),
      routes: {
        '/auth': (context) => const AuthScreen(),
      },
    );
  }
}
