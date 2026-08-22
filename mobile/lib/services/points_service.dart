import 'package:cloud_firestore/cloud_firestore.dart';

class PointsService {
  final FirebaseFirestore db;
  PointsService({FirebaseFirestore? db}) : db = db ?? FirebaseFirestore.instance;

  Future<void> addPoints({required String groupId, required String studentId, required num amount, required String teacherId, String reason = ''}) async {
    if (amount <= 0) throw ArgumentError('Amount must be positive');
    final ref = db.collection('groups').doc(groupId).collection('students').doc(studentId);
    final tx = db.collection('transactions').doc();
    await db.runTransaction((t) async {
      final snap = await t.get(ref);
      final current = (snap.data()?['points'] as num?) ?? 0;
      final next = current + amount;
      t.set(ref, {'points': next, 'updatedAt': FieldValue.serverTimestamp()}, SetOptions(merge: true));
      t.set(tx, {'type': 'add', 'groupId': groupId, 'studentId': studentId, 'amount': amount, 'teacherId': teacherId, 'reason': reason, 'createdAt': FieldValue.serverTimestamp()});
    });
  }

  Future<void> subtractPoints({required String groupId, required String studentId, required num amount, required String teacherId, String reason = ''}) async {
    if (amount <= 0) throw ArgumentError('Amount must be positive');
    final ref = db.collection('groups').doc(groupId).collection('students').doc(studentId);
    final tx = db.collection('transactions').doc();
    await db.runTransaction((t) async {
      final snap = await t.get(ref);
      final current = (snap.data()?['points'] as num?) ?? 0;
      final next = current - amount;
      if (next < 0) throw StateError('Insufficient points');
      t.set(ref, {'points': next, 'updatedAt': FieldValue.serverTimestamp()}, SetOptions(merge: true));
      t.set(tx, {'type': 'subtract', 'groupId': groupId, 'studentId': studentId, 'amount': amount, 'teacherId': teacherId, 'reason': reason, 'createdAt': FieldValue.serverTimestamp()});
    });
  }
}
