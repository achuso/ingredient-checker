import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;

import '../config.dart';
import '../services/prefs_service.dart';
import 'result_page.dart';

class ScanPage extends StatefulWidget {
  const ScanPage({super.key});

  @override
  State<ScanPage> createState() => _ScanPageState();
}

class _ScanPageState extends State<ScanPage> {
  final _prefs = PrefsService();
  List<String> _restrictions = [];
  File? _selected;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _prefs.getRestrictions().then((v) => setState(() => _restrictions = v));
  }

  Future<void> _pick(ImageSource src) async {
    final f = await ImagePicker().pickImage(source: src);
    if (f != null) setState(() => _selected = File(f.path));
  }

  /* ---------- safe helpers ---------- */
  String _statusOf(dynamic v) {
    if (v is String) return v;
    if (v is Map && v['status'] is String) return v['status'];
    return 'unknown';
  }

  String _pretty(String raw) => switch (raw) {
        'unsafe'  => 'definitely unsafe',
        'maybe'   => 'maybe unsafe',
        'unknown' => 'unknown',
        'safe'    => 'safe',
        _         => raw
      };

  Map<String, String> _cast(dynamic node) {
    if (node is Map) {
      return {
        for (final e in node.entries)
          e.key.toString(): _pretty(_statusOf(e.value))
      };
    }
    return {};
  }

  Future<void> _upload() async {
    if (_selected == null) return;
    setState(() => _busy = true);

    try {
      final img64 = base64Encode(await _selected!.readAsBytes());
      final up = await http.post(Uri.parse('$apiBaseUrl/analyze/upload'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'image_base64': img64}));
      if (up.statusCode != 200) throw Exception('Upload failed');
      final s3 = jsonDecode(up.body)['s3_key'];

      final proc = await http.post(Uri.parse('$apiBaseUrl/analyze/process'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            's3_key': s3,
            'restriction':
                _restrictions.length == 1 ? _restrictions.first : _restrictions
          }));
      if (proc.statusCode != 200) throw Exception('Process failed');
      if (!mounted) return;
      setState(() => _busy = false);

      final json = jsonDecode(proc.body) as Map<String, dynamic>;
      final verdictRaw = _statusOf(json['verdict']);
      final cls = json['classified'] ?? {};
      final ingredients = _cast((cls as Map<String, dynamic>)['ingredients']);
      final traces = _cast(cls['traces']);

      final verdict = verdictRaw != 'unknown'
          ? _pretty(verdictRaw)
          : ingredients.values.any((v) => v.contains('definitely'))
              ? 'definitely unsafe'
              : ingredients.values.any((v) => v.contains('maybe'))
                  ? 'maybe unsafe'
                  : traces.values.any((v) => !v.contains('safe'))
                      ? 'unsafe traces'
                      : 'safe';

      Navigator.push(
          context,
          MaterialPageRoute(
              builder: (_) => ResultPage(
                  verdict: verdict,
                  ingredients: ingredients,
                  traces: traces)));
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(e.toString()), backgroundColor: Colors.red));
      }
      setState(() => _busy = false);
    }
  }

  /* ---------- UI helpers ---------- */
  Widget _btn(String label, IconData icon, VoidCallback tap) {
    final primary = Theme.of(context).colorScheme.primary;
    return ElevatedButton.icon(
      onPressed: tap,
      icon: Icon(icon, size: 20),
      label: Text(label),
      style: ElevatedButton.styleFrom(
        backgroundColor: primary,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
        shape:
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
    );
  }

  @override
  Widget build(BuildContext ctx) {
    final primary = Theme.of(ctx).colorScheme.primary;
    return Scaffold(
      backgroundColor: const Color(0xFFFCFAFF),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            children: [
              Icon(Icons.camera_alt_outlined, size: 120, color: primary),
              const SizedBox(height: 16),
              const Text('Snap or pick a product label',
                  textAlign: TextAlign.center,
                  style:
                      TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
              const SizedBox(height: 28),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _btn('Camera', Icons.camera_alt,
                      () => _pick(ImageSource.camera)),
                  const SizedBox(width: 18),
                  _btn('Gallery', Icons.photo,
                      () => _pick(ImageSource.gallery)),
                ],
              ),
              if (_selected != null) ...[
                const SizedBox(height: 28),
                ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.file(_selected!, height: 220)),
                const SizedBox(height: 24),
                _btn('Upload & analyze', Icons.cloud_upload, _upload),
              ],
              if (_busy) ...[
                const SizedBox(height: 32),
                const CircularProgressIndicator(),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
