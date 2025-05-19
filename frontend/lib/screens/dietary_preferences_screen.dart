import 'package:flutter/material.dart';
import '../services/prefs_service.dart';

class DietaryPreferencesScreen extends StatefulWidget {
  const DietaryPreferencesScreen({Key? key}) : super(key: key);

  @override
  State<DietaryPreferencesScreen> createState() =>
      _DietaryPreferencesScreenState();
}

class _DietaryPreferencesScreenState extends State<DietaryPreferencesScreen> {
  final _prefs = PrefsService();
  final _options = {'vegan', 'celiac', 'nut_allergy'};
  final Set<String> _selected = {};

  @override
  void initState() {
    super.initState();
    _prefs.getRestrictions().then((vals) => setState(() => _selected.addAll(vals)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Your dietary preference')),
      body: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Wrap(
            spacing: 12,
            children: _options
                .map((o) => FilterChip(
                      label: Text(o),
                      selected: _selected.contains(o),
                      onSelected: (sel) =>
                          setState(() => sel ? _selected.add(o) : _selected.remove(o)),
                    ))
                .toList(),
          ),
          const SizedBox(height: 32),
          ElevatedButton(
            onPressed: _selected.isEmpty
                ? null
                : () async {
                    await _prefs.setRestrictions(_selected.toList());
                    if (!context.mounted) return;
                    Navigator.pop(context, _selected);
                  },
            child: const Text('Save & continue'),
          )
        ],
      ),
    );
  }
}
