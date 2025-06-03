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
  String _method = 'rule';                     // rule | llm

  @override
  void initState() {
    super.initState();
    _prefs.getMethod().then((v) => setState(() => _method = v));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          ListTile(
            leading: const Icon(Icons.restaurant_menu_outlined),
            title : const Text('Dietary preference'),
            subtitle: const Text('Vegan, celiac, nut allergy …'),
            onTap : _openDietPrefs,
          ),
          const Divider(height: 0),
          ListTile(
            leading : const Icon(Icons.memory),
            title   : const Text('Analysis method'),
            subtitle: Text(_method == 'llm' ? 'LLM-based' : 'Rule-based'),
            onTap   : _chooseMethod,
          ),
          const Divider(height: 0),
          ListTile(
            leading: const Icon(Icons.logout),
            title : const Text('Log out'),
            onTap : _logout,
          ),
        ],
      ),
    );
  }

  /* ───────────── helpers ───────────── */
  void _openDietPrefs() => Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => const DietaryPreferencesScreen()),
      );

  Future<void> _chooseMethod() async {
    final sel = await showDialog<String>(
      context: context,
      builder: (_) => SimpleDialog(
        title: const Text('Choose analysis method'),
        children: [
          RadioListTile(
            title: const Text('Rule-based'),
            value: 'rule',
            groupValue: _method,
            onChanged: (v) => Navigator.pop(context, v),
          ),
          RadioListTile(
            title: const Text('LLM-based'),
            value: 'llm',
            groupValue: _method,
            onChanged: (v) => Navigator.pop(context, v),
          ),
        ],
      ),
    );
    if (sel != null && sel != _method) {
      await _prefs.setMethod(sel);
      setState(() => _method = sel);
    }
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
}
