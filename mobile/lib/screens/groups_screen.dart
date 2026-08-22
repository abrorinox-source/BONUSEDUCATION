import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../services/spreadsheet_service.dart';
import 'spreadsheet_screen.dart';

class GroupsScreen extends StatelessWidget {
  final FirebaseFirestore db;
  const GroupsScreen({super.key, FirebaseFirestore? db}) : db = db ?? FirebaseFirestore.instance;

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Guruhlar')),
    body: StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
      stream: db.collection('groups').orderBy('name').snapshots(),
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator());
        if (snap.hasError) return Center(child: Text('Xatolik: ${snap.error}'));
        final docs = snap.data?.docs ?? [];
        if (docs.isEmpty) return const Center(child: Text('Guruhlar hali yaratilmagan'));
        return ListView.builder(
          itemCount: docs.length,
          itemBuilder: (_, i) {
            final d = docs[i]; final data = d.data();
            return ListTile(
              leading: const CircleAvatar(child: Icon(Icons.groups)),
              title: Text(data['name'] as String? ?? d.id),
              subtitle: Text(data['teacherId'] as String? ?? ''),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => SpreadsheetScreen(groupId: d.id))),
            );
          },
        );
      },
    ),
  );
}
