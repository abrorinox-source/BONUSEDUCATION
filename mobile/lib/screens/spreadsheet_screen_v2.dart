import 'package:flutter/material.dart';
import '../services/spreadsheet_service.dart';

class SpreadsheetScreenV2 extends StatelessWidget {
  final String groupId;
  const SpreadsheetScreenV2({super.key, required this.groupId});

  @override
  Widget build(BuildContext context) {
    final service = SpreadsheetService();
    return Scaffold(
      appBar: AppBar(title: Text('Spreadsheet • $groupId'), actions: [
        IconButton(onPressed: () {}, icon: const Icon(Icons.filter_alt_outlined)),
        IconButton(onPressed: () {}, icon: const Icon(Icons.sort)),
      ]),
      body: StreamBuilder<List<Map<String,dynamic>>>(
        stream: service.watchColumns(groupId),
        builder: (context, columnsSnap) {
          if (columnsSnap.hasError) return Center(child: Text('Error: ${columnsSnap.error}'));
          if (!columnsSnap.hasData) return const Center(child: CircularProgressIndicator());
          final columns = columnsSnap.data!;
          return StreamBuilder<List<Map<String,dynamic>>>(
            stream: service.watchStudents(groupId),
            builder: (context, studentsSnap) {
              if (!studentsSnap.hasData) return const Center(child: CircularProgressIndicator());
              final students = studentsSnap.data!;
              return InteractiveViewer(
                constrained: false,
                minScale: .5,
                maxScale: 2,
                child: DataTable(
                  columns: [const DataColumn(label: Text('#')), ...columns.map((c) => DataColumn(label: Text('${c['name'] ?? ''}')))],
                  rows: List.generate(students.length, (i) {
                    final s = students[i]; final values = Map<String,dynamic>.from(s['values'] as Map? ?? {});
                    return DataRow(cells: [
                      DataCell(Text('${i + 1}')),
                      ...columns.map((c) => DataCell(
                        TextField(
                          controller: TextEditingController(text: '${values[c['id']] ?? ''}'),
                          decoration: const InputDecoration(border: InputBorder.none),
                          onSubmitted: (v) => service.setCell(groupId: groupId, studentId: s['id'], columnId: c['id'], value: c['type'] == 'number' || c['type'] == 'points' ? num.tryParse(v) ?? 0 : v),
                        ),
                      )),
                    ]);
                  }),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
