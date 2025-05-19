import 'package:flutter/material.dart';
import '../services/prefs_service.dart';

class DietaryPreferencesScreen extends StatefulWidget {
  const DietaryPreferencesScreen({super.key});

  @override
  State<DietaryPreferencesScreen> createState() =>
      _DietaryPreferencesScreenState();
}

class _DietaryPreferencesScreenState extends State<DietaryPreferencesScreen> {
  final _prefs = PrefsService();
  final _data = [
    ('vegan', Icons.eco_outlined, 'Plant-based only'),
    ('celiac', Icons.no_food, 'Gluten-free'),
    ('nut_allergy', Icons.energy_savings_leaf, 'No nuts / traces'),
  ];
  final Set<String> _sel = {};

  @override
  void initState() {
    super.initState();
    _prefs.getRestrictions().then((r) => setState(() => _sel.addAll(r)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Dietary preferences')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ..._data.map((e) => Card(
                child: CheckboxListTile(
                  value: _sel.contains(e.$1),
                  onChanged: (v) =>
                      setState(() => v! ? _sel.add(e.$1) : _sel.remove(e.$1)),
                  secondary: Icon(e.$2),
                  title: Text(e.$1.replaceAll('_', ' ').toUpperCase()),
                  subtitle: Text(e.$3),
                ),
              )),
          const SizedBox(height: 24),
          FilledButton.icon(
            icon: const Icon(Icons.save),
            label: const Text('Save'),
            onPressed: _sel.isEmpty
                ? null
                : () async {
                    await _prefs.setRestrictions(_sel.toList());
                    if (context.mounted) Navigator.pop(context, _sel);
                  },
          ),
        ],
      ),
    );
  }
}
