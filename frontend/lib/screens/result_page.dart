import 'package:flutter/material.dart';

class ResultPage extends StatelessWidget {
  const ResultPage({
    super.key,
    required this.verdict,
    required this.ingredients,
    required this.traces,
  });

  final String verdict; // safe | definitely unsafe | maybe unsafe | unsafe traces
  final Map<String, String> ingredients;
  final Map<String, String> traces;

  Color _bannerColor() {
    if (verdict.contains('definitely')) return Colors.red;
    if (verdict.contains('maybe'))       return Colors.yellow.shade700;
    if (verdict.contains('safe') && verdict.contains('traces')) return Colors.orange;
    return Colors.green;
  }

  Color _chipColor(String s) {
    if (s.contains('definitely')) return Colors.red;
    if (s.contains('maybe'))       return Colors.yellow.shade700;
    return Colors.green;
  }

  Widget _list(Map<String, String> m) => Column(
        children: m.entries
            .map((e) => Container(
                  margin: const EdgeInsets.symmetric(vertical: 4),
                  decoration: BoxDecoration(
                    border: Border.all(color: _chipColor(e.value), width: 2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: ListTile(
                    title: Text(e.key),
                    trailing: Text(
                      e.value.toUpperCase(),
                      style: TextStyle(
                          color: _chipColor(e.value),
                          fontWeight: FontWeight.bold),
                    ),
                  ),
                ))
            .toList(),
      );

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Scan result')),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Center(
              child: Text(
                verdict.toUpperCase(),
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: _bannerColor(),
                ),
              ),
            ),
            if (verdict == 'unsafe traces')
              const Padding(
                padding: EdgeInsets.only(top: 8),
                child: Text(
                  'Product itself is safe but may contain traces of unsafe ingredients.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.orange),
                ),
              ),
            const SizedBox(height: 24),
            if (ingredients.isNotEmpty) ...[
              const Text('INGREDIENTS',
                  style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              _list(ingredients),
            ],
            if (traces.isNotEmpty) ...[
              const SizedBox(height: 24),
              const Text('TRACES',
                  style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              _list(traces),
            ],
          ],
        ),
      );
}
