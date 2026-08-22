import 'package:flutter/material.dart';
import '../services/auth_service.dart';

class DashboardScreen extends StatelessWidget {
  final String role;
  const DashboardScreen({super.key, required this.role});

  @override
  Widget build(BuildContext context) {
    final teacher = role == 'teacher' || role == 'admin';
    return Scaffold(
      appBar: AppBar(
        title: Text(teacher ? 'Teacher Dashboard' : 'Student Dashboard'),
        actions: [
          IconButton(icon: const Icon(Icons.logout), onPressed: () => AuthService().signOut()),
        ],
      ),
      body: GridView.count(
        padding: const EdgeInsets.all(16),
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        children: teacher ? [
          _tile(context, Icons.table_chart, 'Spreadsheet', '/spreadsheet'),
          _tile(context, Icons.people, 'Students', null),
          _tile(context, Icons.groups, 'Groups', null),
          _tile(context, Icons.add_circle, 'Add / Remove Points', null),
          _tile(context, Icons.swap_horiz, 'Transfers', null),
          _tile(context, Icons.settings, 'Settings', null),
        ] : [
          _tile(context, Icons.stars, 'My Points', null),
          _tile(context, Icons.emoji_events, 'Ranking', null),
          _tile(context, Icons.swap_horiz, 'Transfer', null),
          _tile(context, Icons.history, 'History', null),
          _tile(context, Icons.menu_book, 'Rules', null),
          _tile(context, Icons.support_agent, 'Support', null),
        ],
      ),
    );
  }

  Widget _tile(BuildContext context, IconData icon, String title, String? route) => Card(
    child: InkWell(
      onTap: route == null ? null : () => Navigator.pushNamed(context, route),
      borderRadius: BorderRadius.circular(12),
      child: Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 38),
        const SizedBox(height: 10),
        Text(title, textAlign: TextAlign.center),
      ])),
    ),
  );
}
