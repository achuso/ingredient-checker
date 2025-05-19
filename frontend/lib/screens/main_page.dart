import 'package:flutter/material.dart';
import 'scan_page.dart';
import 'bottom_navbar.dart';
import '../services/prefs_service.dart';
import 'dietary_preferences_screen.dart';

class HistoryPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(child: Text('History Page')),
    );
  }
}

class SettingsPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(child: Text('Settings Page')),
    );
  }
}

class MainPage extends StatefulWidget {
  @override
  _MainPageState createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {
  int _selectedIndex = 1;

  final _prefs = PrefsService();

  @override
  void initState() {
    super.initState();
    _maybeAskDiet();
  }

  void _maybeAskDiet() async {
    if (!await _prefs.isSet()) {
      if (!mounted) return;
      
      await Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => const DietaryPreferencesScreen()));
    }
  }


  final List<Widget> _pages = [
    HistoryPage(),
    ScanPage(),
    SettingsPage(),
  ];

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_selectedIndex],
      bottomNavigationBar: BottomNavBar(
        currentIndex: _selectedIndex,
        onTap: _onItemTapped,
      ),
    );
  }
} 
