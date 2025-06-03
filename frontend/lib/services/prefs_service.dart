import 'package:shared_preferences/shared_preferences.dart';

class PrefsService {
  /* ─────────────── dietary restrictions ─────────────── */
  static const _dietKey = 'dietary_restrictions';

  Future<List<String>> getRestrictions() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getStringList(_dietKey) ?? [];
  }

  Future<void> setRestrictions(List<String> values) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_dietKey, values);
  }

  /// **Restores the old helper:** returns `true`
  /// if the user has picked at least one restriction.
  Future<bool> isSet() async {
    final prefs = await SharedPreferences.getInstance();
    return (prefs.getStringList(_dietKey)?.isNotEmpty ?? false);
  }

  /* ─────────────── analysis method pref ─────────────── */
  // "rule"  = rule-based  ·  "llm" = GPT/LLM
  static const _methodKey = 'analysis_method';

  Future<String> getMethod() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_methodKey) ?? 'rule';
  }

  Future<void> setMethod(String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_methodKey, value);
  }
}
