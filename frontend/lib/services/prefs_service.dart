import 'package:shared_preferences/shared_preferences.dart';

class PrefsService {
  static const _dietKey = 'dietary_restrictions';

  Future<List<String>> getRestrictions() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getStringList(_dietKey) ?? [];
  }

  Future<void> setRestrictions(List<String> values) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_dietKey, values);
  }

  Future<bool> isSet() async => (await getRestrictions()).isNotEmpty;
}
