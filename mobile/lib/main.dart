import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'services/auth_service.dart';
import 'screens/login_screen.dart';
import 'screens/spreadsheet_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  runApp(const BonusEducationApp());
}

class BonusEducationApp extends StatelessWidget {
  const BonusEducationApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'BONUSEDUCATION',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo), useMaterial3: true),
    home: const AuthGate(),
  );
}

class AuthGate extends StatelessWidget {
  const AuthGate({super.key});
  @override
  Widget build(BuildContext context) => StreamBuilder<User?>(
    stream: AuthService().authState,
    builder: (context, auth) {
      if (auth.connectionState == ConnectionState.waiting) {
        return const Scaffold(body: Center(child: CircularProgressIndicator()));
      }
      final user = auth.data;
      if (user == null) return const LoginScreen();
      return StreamBuilder<String>(
        stream: AuthService().roleStream(user.uid),
        builder: (context, role) {
          if (!role.hasData) return const Scaffold(body: Center(child: CircularProgressIndicator()));
          return SpreadsheetScreen(groupId: 'demo');
        },
      );
    },
  );
}
