import 'package:flutter/material.dart';

import '../services/prefs_service.dart';
import '../services/auth_service.dart';
import 'dietary_preferences_screen.dart';
import 'welcome_screen.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  final _prefs = PrefsService();

  Future<void> _openDietPrefs() async {
    await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const DietaryPreferencesScreen()),
    );
    if (!mounted) return;
    final list = await _prefs.getRestrictions();
    final txt = list.isEmpty ? 'None' : list.join(', ');
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Saved: $txt')),
    );
  }

  Future<void> _logout() async {
    await AuthService().logout();
    if (!mounted) return;
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const WelcomeScreen()),
      (_) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          ListTile(
            leading: const Icon(Icons.restaurant_menu_outlined),
            title: const Text('Dietary preference'),
            subtitle: const Text('Vegan, celiac, nut allergy …'),
            onTap: _openDietPrefs,
          ),
          const Divider(height: 0),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Log out'),
            onTap: _logout,
          ),
        ],
      ),
    );
  }
}
