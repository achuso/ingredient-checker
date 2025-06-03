import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';

import '../config.dart';
import '../services/auth_service.dart';
import '../services/prefs_service.dart';
import 'result_page.dart';

/// Lists previous scans for the logged-in user (GET /scans).
class HistoryPage extends StatefulWidget {
  const HistoryPage({super.key});

  @override
  State<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends State<HistoryPage> {
  final _auth  = AuthService();
  late Future<List<_Scan>> _future;

  @override
  void initState() {
    super.initState();
    _future = _fetch();
  }

  Future<List<_Scan>> _fetch() async {
    final token = await _auth.readToken();
    if (token == null) throw Exception('Not authenticated');

    final res = await http.get(
      Uri.parse('$apiBaseUrl/scans'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (res.statusCode != 200) {
      throw Exception('Failed (${res.statusCode})');
    }
    final List data = jsonDecode(res.body);
    return data.map((e) => _Scan.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<void> _open(_Scan scan) async {
    final token = await _auth.readToken();
    if (token == null) return;

    final res = await http.get(
      Uri.parse('$apiBaseUrl/scans/${scan.id}'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (res.statusCode != 200) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed (${res.statusCode})')),
        );
      }
      return;
    }

    final detail = jsonDecode(res.body) as Map<String, dynamic>;
    final Map<String, String> ing = {};
    final Map<String, String> trc = {};
    for (final m in (detail['ingredients'] as List)) {
      final n = (m['ingredient'] ?? m['name']) as String;
      final v = m['verdict'] as String;
      if (m['is_trace'] == true) {
        trc[n] = v;
      } else {
        ing[n] = v;
      }
    }

    // ⬇️  use *server-side* restrictions stored with this scan
    final restrictions = List<String>.from(
      detail['restrictions'] ?? detail['restriction_ids'] ?? const [],
    );

    if (!mounted) return;
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ResultPage(
          verdict      : detail['final_verdict'] as String? ?? 'unknown',
          ingredients  : ing,
          traces       : trc,
          restrictions : restrictions,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('History')),
      body: FutureBuilder<List<_Scan>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(child: Text('Error: ${snap.error}'));
          }
          final list = snap.data!;
          if (list.isEmpty) {
            return const Center(child: Text('No scans yet.'));
          }
          return ListView.separated(
            itemCount: list.length,
            separatorBuilder: (_, __) => const Divider(height: 1),
            itemBuilder: (context, i) {
              final s = list[i];
              return ListTile(
                leading : const Icon(Icons.history),        // thumbnail removed
                title   : Text(
                  s.scannedAt != null
                      ? DateFormat('dd.MM.yyyy  HH:mm').format(s.scannedAt!)
                      : 'Unknown',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                subtitle: Text(s.verdict),
                trailing: const Icon(Icons.chevron_right),
                onTap   : () => _open(s),
              );
            },
          );
        },
      ),
    );
  }
}

class _Scan {
  final String id;
  final String verdict;
  final DateTime? scannedAt;
  const _Scan({required this.id, required this.verdict, this.scannedAt});

  factory _Scan.fromJson(Map<String, dynamic> j) => _Scan(
        id        : j['scan_id']       as String,
        verdict   : j['final_verdict'] as String? ?? '',
        scannedAt : j['scanned_at'] != null
            ? DateTime.parse(j['scanned_at'])
            : null,
      );
}
