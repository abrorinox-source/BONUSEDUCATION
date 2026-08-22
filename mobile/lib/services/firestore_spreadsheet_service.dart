import 'package:cloud_firestore/cloud_firestore.dart';

class FirestoreSpreadsheetService {
  final FirebaseFirestore db;
  FirestoreSpreadsheetService({FirebaseFirestore? firestore}) : db = firestore ?? FirebaseFirestore.instance;

  CollectionReference<Map<String, dynamic>> columns(String groupId) => db.collection('groups').doc(groupId).collection('columns');
  CollectionReference<Map<String, dynamic>> students(String groupId) => db.collection('groups').doc(groupId).collection('students');

  Stream<List<Map<String, dynamic>>> watchColumns(String groupId) => columns(groupId).orderBy('order').snapshots().map((s) => s.docs.map((d) => {'id': d.id, ...d.data()}).toList());
  Stream<List<Map<String, dynamic>>> watchStudents(String groupId) => students(groupId).orderBy('order').snapshots().map((s) => s.docs.map((d) => {'id': d.id, ...d.data()}).toList());

  Future<void> setCell(String groupId, String studentId, String columnId, dynamic value) => students(groupId).doc(studentId).set({'values': {columnId: value}, 'updatedAt': FieldValue.serverTimestamp()}, SetOptions(merge: true));

  Future<void> createColumn(String groupId, String name, String type, {String? formula}) async {
    final snap = await columns(groupId).get();
    await columns(groupId).add({'name': name.trim(), 'type': type, 'order': snap.docs.length, 'editable': type != 'formula', 'formula': formula, 'createdAt': FieldValue.serverTimestamp()});
  }

  Future<void> renameColumn(String groupId, String columnId, String name) => columns(groupId).doc(columnId).update({'name': name.trim()});
  Future<void> deleteColumn(String groupId, String columnId) => columns(groupId).doc(columnId).delete();
}
