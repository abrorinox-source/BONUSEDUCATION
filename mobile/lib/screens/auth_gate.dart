import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import 'dashboard_screen.dart';
import 'login_screen.dart';

class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) => StreamBuilder(
    stream: AuthService().authState,
    builder: (context, snapshot) {
      if (snapshot.connectionState == ConnectionState.waiting) {
        return const Scaffold(body: Center(child: CircularProgressIndicator()));
      }
      final user = snapshot.data;
      if (user == null) return const LoginScreen();
      return StreamBuilder<String>(
        stream: AuthService().roleStream(user.uid),
        builder: (context, roleSnapshot) {
          if (!roleSnapshot.hasData) {
            return const Scaffold(body: Center(child: CircularProgressIndicator()));
          }
          return DashboardScreen(role: roleSnapshot.data!);
        },
      );
    },
  );
}
