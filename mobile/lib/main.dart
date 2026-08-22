import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  runApp(const BonusEducationApp());
}

class BonusEducationApp extends StatelessWidget {
  const BonusEducationApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BONUSEDUCATION',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      home: const Scaffold(
        body: Center(
          child: Text(
            'BONUSEDUCATION 2.0\nFirebase Edition',
            textAlign: TextAlign.center,
          ),
        ),
      ),
    );
  }
}
