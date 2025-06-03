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

    // ask for dietary restrictions (original behaviour)
    _prefs.isSet().then((dietSet) {
      if (!dietSet && mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const DietaryPreferencesScreen()),
        );
      }
    });

    // ask for analysis method if still unset
    _prefs.isMethodSet().then((mSet) {
      if (!mSet && mounted) {
        showDialog<String>(
          context: context,
          barrierDismissible: false,
          builder: (_) => SimpleDialog(
            title: const Text('Choose analysis method'),
            children: [
              SimpleDialogOption(
                onPressed: () => Navigator.pop(context, 'rule'),
                child: const Text('Rule-based'),
              ),
              SimpleDialogOption(
                onPressed: () => Navigator.pop(context, 'llm'),
                child: const Text('LLM-based'),
              ),
            ],
          ),
        ).then((sel) {
          if (sel != null) _prefs.setMethod(sel);
        });
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
