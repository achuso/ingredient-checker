import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';

class ResultPage extends StatelessWidget {
  const ResultPage({
    super.key,
    required this.verdict,
    required this.ingredients,
    required this.traces,
    required this.restrictions,
  });

  final String verdict;
  final Map<String, String> ingredients;
  final Map<String, String> traces;
  final List<String> restrictions;

  // ───────────── colour palette ─────────────
  Color _colorFor(String v) => switch (v.toLowerCase()) {
        'definitely unsafe'  => Colors.red,
        'unsafe'             => Colors.red,
        'maybe unsafe'       => Colors.orange,   // ↓ softer than yellow
        'potentially unsafe' => Colors.orange,
        'maybe'              => Colors.orange,
        'safe'               => Colors.green,
        _                    => Colors.grey,
      };

  // UTF-8 double-decode helper
  String _fix(String s) {
    try {
      return utf8.decode(latin1.encode(s));
    } catch (_) {
      return s;
    }
  }

  // build text for sharing
  String _shareText() {
    final b = StringBuffer();
    if (restrictions.isNotEmpty) {
      b.writeln('Applies to: ${restrictions.join(", ")}\n');
    }
    b.writeln('Verdict: $verdict\n');
    ingredients.forEach((k, v) => b.writeln('- ${_fix(k)} → $v'));
    if (traces.isNotEmpty) {
      b.writeln('\nTraces:');
      traces.forEach((k, v) => b.writeln('- ${_fix(k)} → $v'));
    }
    return b.toString();
  }

  // list tiles
  List<Widget> _rows(Map<String, String> map) => map.entries
      .map(
        (e) => Card(
          margin: const EdgeInsets.symmetric(vertical: 4),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: ListTile(
            title: Text(_fix(e.key)),
            trailing: Text(
              e.value.toUpperCase(),
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: _colorFor(e.value),
              ),
            ),
          ),
        ),
      )
      .toList();

  @override
  Widget build(BuildContext context) => Scaffold(
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
              if (restrictions.isNotEmpty) ...[
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  children:
                      restrictions.map((r) => Chip(label: Text(r))).toList(),
                ),
                const SizedBox(height: 24),
              ],
              if (ingredients.isNotEmpty) ...[
                const Text('INGREDIENTS',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                ..._rows(ingredients),
              ],
              if (traces.isNotEmpty) ...[
                const SizedBox(height: 24),
                const Text('TRACES',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                ..._rows(traces),
              ],
            ],
          ),
        ),
      );
}
