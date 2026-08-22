import 'package:cloud_firestore/cloud_firestore.dart';

import '../models/spreadsheet.dart';

class SpreadsheetService {
  SpreadsheetService({FirebaseFirestore? firestore})
      : _firestore = firestore ?? FirebaseFirestore.instance;

  final FirebaseFirestore _firestore;

  CollectionReference<Map<String, dynamic>> _columns(String groupId) =>
      _firestore.collection('groups').doc(groupId).collection('columns');

  CollectionReference<Map<String, dynamic>> _students(String groupId) =>
      _firestore.collection('groups').doc(groupId).collection('students');

  Stream<List<SpreadsheetColumn>> watchColumns(String groupId) {
    return _columns(groupId).orderBy('order').snapshots().map(
          (snapshot) => snapshot.docs
              .map((doc) => SpreadsheetColumn.fromMap(doc.id, doc.data()))
              .toList(),
        );
  }

  Future<DocumentReference<Map<String, dynamic>>> createColumn({
    required String groupId,
    required String name,
    required ColumnType type,
    String? formula,
  }) async {
    final existing = await _columns(groupId).get();
    final ref = _columns(groupId).doc();
    await ref.set({
      'name': name.trim(),
      'type': type.name,
      'order': existing.docs.length,
      'editable': true,
      'formula': formula,
      'createdAt': FieldValue.serverTimestamp(),
      'updatedAt': FieldValue.serverTimestamp(),
    });
    return ref;
  }

  Future<void> updateColumn({
    required String groupId,
    required String columnId,
    required Map<String, dynamic> changes,
  }) {
    return _columns(groupId).doc(columnId).update({
      ...changes,
      'updatedAt': FieldValue.serverTimestamp(),
    });
  }

  Future<void> deleteColumn(String groupId, String columnId) {
    return _columns(groupId).doc(columnId).delete();
  }

  Stream<QuerySnapshot<Map<String, dynamic>>> watchStudents(String groupId) {
    return _students(groupId).orderBy('fullName').snapshots();
  }

  Future<void> setCell({
    required String groupId,
    required String studentId,
    required String columnId,
    required dynamic value,
  }) {
    return _students(groupId).doc(studentId).set({
      'values': {columnId: value},
      'updatedAt': FieldValue.serverTimestamp(),
    }, SetOptions(merge: true));
  }
}
