import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'screens/auth_gate.dart';
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
    theme: ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
      useMaterial3: true,
    ),
    routes: {
      '/spreadsheet': (_) => const SpreadsheetScreen(groupId: 'demo'),
    },
    home: const AuthGate(),
  );
}
