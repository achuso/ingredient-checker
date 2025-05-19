import 'package:flutter/material.dart';

import 'history_page.dart';
import 'scan_page.dart';
import 'settings_page.dart';
import 'bottom_navbar.dart';
import 'dietary_preferences_screen.dart';
import '../services/prefs_service.dart';

class MainPage extends StatefulWidget {
  const MainPage({super.key});
  @override
  State<MainPage> createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {
  int _idx = 1;
  final _prefs = PrefsService();

  @override
  void initState() {
    super.initState();
    _prefs.isSet().then((v) {
      if (!v && mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(
              builder: (_) => const DietaryPreferencesScreen()),
        );
      }
    });
  }

  final _pages = const [HistoryPage(), ScanPage(), SettingsPage()];

  @override
  Widget build(BuildContext context) => Scaffold(
        body: _pages[_idx],
        bottomNavigationBar:
            BottomNavBar(currentIndex: _idx, onTap: (i) => setState(() => _idx = i)),
      );
}
