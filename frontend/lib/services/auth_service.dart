import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:jwt_decoder/jwt_decoder.dart';

class AuthService {
  static const _tokenKey = 'jwt_token';
  final _storage = const FlutterSecureStorage();

  Future<void> saveToken(String token) =>
      _storage.write(key: _tokenKey, value: token);

  Future<String?> readToken() => _storage.read(key: _tokenKey);

  Future<bool> hasValidToken() async {
    final t = await readToken();
    if (t == null) return false;
    return !JwtDecoder.isExpired(t);
  }

  Future<void> logout() => _storage.delete(key: _tokenKey);
}
