// lib/screens/main_screen.dart

import 'package:flutter/material.dart';
import 'history_page.dart';
import 'scan_page.dart';
import 'settings_page.dart';

/// Bottom‐nav UI that only builds the selected tab on demand:
///   0 → HistoryPage
///   1 → ScanPage
///   2 → SettingsPage
class MainScreen extends StatefulWidget {
  const MainScreen({Key? key}) : super(key: key);

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  // Start on the Scan tab (index = 1)
  int _currentIndex = 1;

  @override
  Widget build(BuildContext context) {
    Widget activeTab;
    switch (_currentIndex) {
      case 0:
        activeTab = const HistoryPage();
        break;
      case 1:
        activeTab = const ScanPage();
        break;
      case 2:
        activeTab = const SettingsPage();
        break;
      default:
        activeTab = const ScanPage();
    }

    return Scaffold(
      body: activeTab,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (int idx) {
          setState(() {
            _currentIndex = idx;
          });
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.history),
            label: 'History',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.camera_alt),
            label: 'Scan',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings),
            label: 'Settings',
          ),
        ],
      ),
    );
  }
}
