import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';

class ResultPage extends StatelessWidget {
  const ResultPage({
    super.key,
    required this.verdict,
    required this.ingredients,
    required this.traces,
  });

  final String verdict;
  final Map<String, String> ingredients;
  final Map<String, String> traces;

  Color _colorFor(String v) {
    final t = v.toLowerCase();
    if (t.contains('definitely') || t.contains('unsafe')) return Colors.red;
    if (t.contains('maybe')) return Colors.orange;
    return Colors.green;
  }

  String _shareText() {
    final buf = StringBuffer()
      ..writeln('Scan result')
      ..writeln('Verdict: $verdict')
      ..writeln('');
    if (ingredients.isNotEmpty) {
      buf.writeln('Ingredients:');
      ingredients.forEach((k, v) => buf.writeln('- $k → $v'));
    }
    if (traces.isNotEmpty) {
      buf.writeln('\nTraces:');
      traces.forEach((k, v) => buf.writeln('- $k → $v'));
    }
    return buf.toString();
  }

  List<Widget> _rows(Map<String, String> map) => map.entries
      .map((e) => Card(
            margin: const EdgeInsets.symmetric(vertical: 4),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: ListTile(
              title: Text(e.key),
              trailing: Text(
                e.value.toUpperCase(),
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: _colorFor(e.value),
                ),
              ),
            ),
          ))
      .toList();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan result'),
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            onPressed: () => Share.share(_shareText()),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            Center(
              child: Text(
                verdict.toUpperCase(),
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: _colorFor(verdict),
                      fontWeight: FontWeight.bold,
                    ),
              ),
            ),
            const SizedBox(height: 24),
            if (ingredients.isNotEmpty) ...[
              const Text('INGREDIENTS', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              ..._rows(ingredients),
            ],
            if (traces.isNotEmpty) ...[
              const SizedBox(height: 24),
              const Text('TRACES', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              ..._rows(traces),
            ],
          ],
        ),
      ),
    );
  }
}
