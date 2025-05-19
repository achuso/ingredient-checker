import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;

import '../config.dart';
import '../services/prefs_service.dart';

class ScanPage extends StatefulWidget {
  const ScanPage({Key? key}) : super(key: key);

  @override
  State<ScanPage> createState() => _ScanPageState();
}

class _ScanPageState extends State<ScanPage> {
  final _prefs = PrefsService();
  List<String> _restrictions = [];

  File? _selectedImage;
  Map<String, dynamic>? _result;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _loadPrefs();
  }

  Future<void> _loadPrefs() async {
    final r = await _prefs.getRestrictions();
    setState(() => _restrictions = r);
  }

  Future<void> _pickFromGallery() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery);
    if (pickedFile != null) {
      setState(() => _selectedImage = File(pickedFile.path));
    }
  }

  Future<void> _uploadAndAnalyze() async {
    if (_selectedImage == null) return;
    setState(() {
      _loading = true;
      _result = null;
    });

    try {
      // Upload
      final bytes = await _selectedImage!.readAsBytes();
      final upResp = await http.post(
        Uri.parse('$apiBaseUrl/analyze/upload'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'image_base64': base64Encode(bytes)}),
      );
      if (upResp.statusCode != 200) throw Exception('Upload failed');
      final s3Key = jsonDecode(upResp.body)['s3_key'];

      // Process
      final procResp = await http.post(
        Uri.parse('$apiBaseUrl/analyze/process'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          's3_key': s3Key,
          'restriction': _restrictions.length == 1
              ? _restrictions.first
              : _restrictions, // backend accepts list or string
        }),
      );
      if (procResp.statusCode != 200) throw Exception('Process failed');

      setState(() => _result = jsonDecode(procResp.body));
    } 
    catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
      );
    } 
    finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Widget _actionButton(String label, IconData icon, VoidCallback onPressed) {
    return ElevatedButton.icon(
      onPressed: onPressed,
      icon: Icon(icon, size: 20),
      label: Text(label, style: const TextStyle(fontSize: 16)),
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFF1D4ED8),
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
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
              const Text(
                'Take a photo\nor upload from gallery',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w600,
                  color: Colors.black87,
                ),
              ),
              const SizedBox(height: 40),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _actionButton('Gallery', Icons.photo_library, _pickFromGallery),
                ],
              ),
              const SizedBox(height: 40),
              if (_selectedImage != null)
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Image.file(_selectedImage!, height: 220),
                ),
              if (_selectedImage != null && !_loading) ...[
                const SizedBox(height: 24),
                _actionButton(
                    'Upload & analyze', Icons.cloud_upload_outlined, _uploadAndAnalyze),
              ],
              if (_loading) const SizedBox(height: 32),
              if (_loading) const CircularProgressIndicator(),

              if (_result != null) ...[
                const Divider(height: 48),
                Text(
                  'Dietary mode: ${_restrictions.join(", ")}',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                Text(
                  const JsonEncoder.withIndent('  ').convert(_result!['classified']),
                  style: const TextStyle(fontFamily: 'monospace'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
