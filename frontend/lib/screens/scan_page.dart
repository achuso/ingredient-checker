import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;

import '../config.dart';
import '../services/prefs_service.dart';
import '../services/auth_service.dart';          // ← NEW
import 'result_page.dart';

class ScanPage extends StatefulWidget {
  const ScanPage({super.key});

  @override
  State<ScanPage> createState() => _ScanPageState();
}

class _ScanPageState extends State<ScanPage> {
  final _prefs = PrefsService();
  final _auth  = AuthService();                 // ← NEW

  File? _selected;
  bool _busy = false;
  List<String> _restrictions = [];
  String _method = 'rule';                      // "rule" | "llm"

  @override
  void initState() {
    super.initState();
    _prefs.getRestrictions().then((v) => setState(() => _restrictions = v));
    _prefs.getMethod().then((v) => setState(() => _method = v));
  }

  Future<void> _pick(ImageSource src) async {
    final f = await ImagePicker().pickImage(source: src);
    if (f != null) setState(() => _selected = File(f.path));
  }

  /* -------------------- utilities -------------------- */
  String _statusOf(dynamic v) =>
      v is String ? v : (v is Map && v['status'] is String ? v['status'] : 'unknown');

  String _pretty(String raw) => switch (raw) {
        'unsafe'  => 'definitely unsafe',
        'maybe'   => 'maybe unsafe',
        'unknown' => 'unknown',
        'safe'    => 'safe',
        _         => raw
      };

  Map<String, String> _cast(dynamic node) => node is Map
      ? {for (final e in node.entries) e.key as String: _statusOf(e.value)}
      : {};

  /* -------------------- analyze -------------------- */
  Future<void> _analyze() async {
    if (_selected == null) return;
    setState(() => _busy = true);

    try {
      final token = await _auth.readToken();           // ← NEW
      if (token == null) {
        throw Exception('Not authenticated. Please log in again.');
      }

      final img64 = base64Encode(await _selected!.readAsBytes());

      final res = await http.post(
        Uri.parse('$apiBaseUrl/analyze/process'),      // adjust if your path differs
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',           // ← NEW
        },
        body: jsonEncode({
          'image_base64': img64,
          'restriction_ids': _restrictions,
          'method': _method,                           // "rule" | "llm"
        }),
      );

      if (res.statusCode != 200) {
        throw Exception('Upload failed (HTTP ${res.statusCode})');
      }

      final json = jsonDecode(res.body) as Map<String, dynamic>;

      final verdictRaw   = _statusOf(json['final_verdict']);
      final cls          = json['classified'] ?? {};
      final ingredients  = _cast((cls as Map<String, dynamic>)['ingredients']);
      final traces       = _cast(cls['traces']);

      final verdict = verdictRaw.isNotEmpty
          ? _pretty(verdictRaw)
          : ingredients.values.any((v) => v.contains('definitely'))
              ? 'definitely unsafe'
              : ingredients.values.any((v) => v.contains('maybe'))
                  ? 'maybe unsafe'
                  : traces.values.any((v) => !v.contains('safe'))
                      ? 'unsafe traces'
                      : 'safe';

      if (!mounted) return;
      setState(() => _busy = false);

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ResultPage(
            verdict: verdict,
            ingredients: ingredients,
            traces: traces,
            restrictions : _restrictions,
          ),
        ),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
        );
        setState(() => _busy = false);
      }
    }
  }

  /* ---------------------- UI ---------------------- */
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
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
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
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.camera_alt_outlined,
                  size: 120, color: primary.withOpacity(0.7)),
              const SizedBox(height: 24),
              const Text('Snap or pick a product label',
                  style: TextStyle(fontSize: 18)),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _btn('Camera', Icons.camera, () => _pick(ImageSource.camera)),
                  _btn('Gallery', Icons.photo_library,
                      () => _pick(ImageSource.gallery)),
                ],
              ),
              if (_selected != null) ...[
                const SizedBox(height: 32),
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Image.file(_selected!,
                      width: 280, fit: BoxFit.cover),
                ),
                const SizedBox(height: 24),
                _btn('Upload & analyze', Icons.cloud_upload, _analyze),
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
