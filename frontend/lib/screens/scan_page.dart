import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;

import '../config.dart';
import '../services/prefs_service.dart';
import 'result_page.dart';

class ScanPage extends StatefulWidget {
  const ScanPage({Key? key}) : super(key: key);

  @override
  State<ScanPage> createState() => _ScanPageState();
}

class _ScanPageState extends State<ScanPage> {
  final _prefs = PrefsService();
  List<String> _restrictions = [];

  File? _selectedImage;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _prefs.getRestrictions().then((r) => setState(() => _restrictions = r));
  }

  Future<void> _pickFromGallery() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery);
    if (picked != null) setState(() => _selectedImage = File(picked.path));
  }

  String _statusOf(dynamic raw) {
    if (raw is String) return raw;
    if (raw is Map && raw['status'] is String) return raw['status'];
    return 'unknown';
  }

  String _humanise(String s) => switch (s) {
        'unsafe' => 'definitely unsafe',
        'maybe' => 'maybe unsafe',
        _ => s,
      };

  Future<void> _uploadAndAnalyze() async {
    if (_selectedImage == null) return;
    setState(() => _loading = true);

    try {
      // Upload
      final img64 = base64Encode(await _selectedImage!.readAsBytes());
      final up = await http.post(Uri.parse('$apiBaseUrl/analyze/upload'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'image_base64': img64}));
      if (up.statusCode != 200) throw Exception('Upload failed');
      final s3 = jsonDecode(up.body)['s3_key'];

      // Process
      final proc = await http.post(Uri.parse('$apiBaseUrl/analyze/process'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            's3_key': s3,
            'restriction':
                _restrictions.length == 1 ? _restrictions.first : _restrictions
          }));
      if (proc.statusCode != 200) throw Exception('Process failed');
      if (!mounted) return;
      setState(() => _loading = false);

      // Parsing response
      final data = jsonDecode(proc.body);
      final classified = (data['classified'] ?? {}) as Map;
      final ingSrc = (classified['ingredients'] ?? {}) as Map<String, dynamic>;
      final trcSrc = (classified['traces'] ?? {}) as Map<String, dynamic>;

      final ingredients = {
        for (final e in ingSrc.entries) e.key: _humanise(_statusOf(e.value))
      };
      final traces = {
        for (final e in trcSrc.entries) e.key: _humanise(_statusOf(e.value))
      };

      // Compute verdict
      String verdict;
      if (ingredients.values.any((s) => s.contains('definitely'))) {
        verdict = 'definitely unsafe';
      } 
      else if (ingredients.values.any((s) => s.contains('maybe'))) {
        verdict = 'maybe unsafe';
      } 
      else if (traces.values.any((s) => !s.contains('safe'))) {
        verdict = 'unsafe traces';
      } 
      else {
        verdict = 'safe';
      }

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ResultPage(
            verdict: verdict,
            ingredients: ingredients,
            traces: traces,
          ),
        ),
      );
    } 
    catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
        );
      }
      setState(() => _loading = false);
    }
  }

  // UI Helpers
  Widget _btn(String txt, IconData ic, VoidCallback tap) => ElevatedButton.icon(
        onPressed: tap,
        icon: Icon(ic, size: 20),
        label: Text(txt),
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF1D4ED8),
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
      );

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: const Color(0xFFFCFAFF),
        body: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.camera_alt_outlined,
                    size: 120, color: Color(0xFF1D4ED8)),
                const SizedBox(height: 32),
                const Text('Take a photo\nor upload from gallery',
                    textAlign: TextAlign.center,
                    style:
                        TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
                const SizedBox(height: 40),
                _btn('Gallery', Icons.photo_library, _pickFromGallery),
                const SizedBox(height: 40),
                if (_selectedImage != null)
                  ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.file(_selectedImage!, height: 220)),
                if (_selectedImage != null && !_loading) ...[
                  const SizedBox(height: 24),
                  _btn('Upload & analyze', Icons.cloud_upload_outlined,
                      _uploadAndAnalyze),
                ],
                if (_loading) ...[
                  const SizedBox(height: 32),
                  const CircularProgressIndicator(),
                ],
              ],
            ),
          ),
        ),
      );
}
