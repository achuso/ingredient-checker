import 'package:flutter/material.dart';

import 'scan_page.dart';
import 'settings_page.dart';           // ← new detailed settings screen
import 'bottom_navbar.dart';
import 'dietary_preferences_screen.dart';
import '../services/prefs_service.dart';

/// Stub until there's a history page
class HistoryPage extends StatelessWidget {
  const HistoryPage({super.key});

  @override
  Widget build(BuildContext context) =>
      const Scaffold(body: Center(child: Text('History Page')));
}

class MainPage extends StatefulWidget {
  const MainPage({super.key});

  @override
  State<MainPage> createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {
  int _selectedIndex = 1;            // start on Scan
  final _prefs = PrefsService();

  @override
  void initState() {
    super.initState();
    _maybeAskDiet();
  }

  Future<void> _maybeAskDiet() async {
    if (!await _prefs.isSet()) {
      if (!mounted) return;
      await Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => const DietaryPreferencesScreen()),
      );
    }
  }

  final List<Widget> _pages = const [
    HistoryPage(),
    ScanPage(),
    SettingsPage(),
  ];

  void _onItemTapped(int idx) => setState(() => _selectedIndex = idx);

  @override
  Widget build(BuildContext context) => Scaffold(
        body: _pages[_selectedIndex],
        bottomNavigationBar: BottomNavBar(
          currentIndex: _selectedIndex,
          onTap: _onItemTapped,
        ),
      );
}
