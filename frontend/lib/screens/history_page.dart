import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

import '../config.dart';
import '../services/auth_service.dart';
import 'result_page.dart';

class HistoryPage extends StatefulWidget {
  const HistoryPage({super.key});

  @override
  State<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends State<HistoryPage> {
  late Future<List<_Scan>> _future;

  @override
  void initState() {
    super.initState();
    _future = _fetch();
  }

  Future<List<_Scan>> _fetch() async {
    final token = await AuthService().readToken();
    final resp = await http.get(
      Uri.parse('$apiBaseUrl/scans'),
      headers: token != null ? {'Authorization': 'Bearer $token'} : {},
    );

    if (resp.statusCode != 200) {
      final detail = jsonDecode(resp.body)['detail'] ?? resp.reasonPhrase;
      throw Exception('History load failed • ${resp.statusCode}: $detail');
    }

    final list = jsonDecode(resp.body) as List;
    return list.map((e) => _Scan.fromJson(e)).toList();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('History')),
        body: FutureBuilder(
          future: _future,
          builder: (ctx, snap) {
            if (snap.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snap.hasError) {
              return Center(
                  child: Text(snap.error.toString(),
                      style: const TextStyle(color: Colors.red)));
            }
            final scans = snap.data! as List<_Scan>;
            if (scans.isEmpty) {
              return const Center(child: Text('No scans yet.'));
            }
            return ListView.separated(
              itemCount: scans.length,
              separatorBuilder: (_, __) => const Divider(height: 0),
              itemBuilder: (_, i) {
                final s = scans[i];
                IconData icon;
                Color col;
                if (s.verdict.contains('definitely')) {
                  icon = Icons.error;
                  col = Colors.red;
                } else if (s.verdict.contains('maybe')) {
                  icon = Icons.warning;
                  col = Colors.orange;
                } else if (s.verdict.contains('trace')) {
                  icon = Icons.info;
                  col = Colors.amber;
                } else {
                  icon = Icons.check_circle;
                  col = Colors.green;
                }
                return ListTile(
                  leading: Icon(icon, color: col),
                  title: Text(s.product),
                  subtitle: Text(s.created),
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ResultPage(
                        verdict: s.verdict,
                        ingredients: s.ingredients,
                        traces: s.traces,
                      ),
                    ),
                  ),
                );
              },
            );
          },
        ),
      );
}

class _Scan {
  final String id, product, verdict, created;
  final Map<String, String> ingredients, traces;

  _Scan(
      {required this.id,
      required this.product,
      required this.verdict,
      required this.created,
      required this.ingredients,
      required this.traces});

  factory _Scan.fromJson(Map<String, dynamic> j) => _Scan(
        id: j['scan_id'],
        product: j['product_name'] ?? 'scan',
        verdict: j['verdict'],
        created: j['created_at'],
        ingredients: Map<String, String>.from(j['ingredients']),
        traces: Map<String, String>.from(j['traces']),
      );
}
