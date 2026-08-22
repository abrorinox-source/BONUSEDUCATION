import 'package:cloud_firestore/cloud_firestore.dart';

class PointsService {
  final FirebaseFirestore db;
  PointsService({FirebaseFirestore? db}) : db = db ?? FirebaseFirestore.instance;
  CollectionReference<Map<String,dynamic>> _students(String g)=>db.collection('groups').doc(g).collection('students');
  Future<void> addPoints({required String groupId,required String studentId,required num amount,required String teacherId,String reason=''})=>_change(groupId,studentId,amount,teacherId,'add',reason);
  Future<void> subtractPoints({required String groupId,required String studentId,required num amount,required String teacherId,String reason=''})=>_change(groupId,studentId,-amount,teacherId,'subtract',reason);
  Future<void> _change(String g,String s,num amount,String actor,String type,String reason) async {
    if(amount<=0&&type=='add'||amount>=0&&type=='subtract')throw ArgumentError('Invalid amount');
    final ref=_students(g).doc(s); final tx=db.collection('transactions').doc();
    await db.runTransaction((t)async{final snap=await t.get(ref);final cur=(snap.data()?['points'] as num?)??0;final next=cur+amount;if(next<0)throw StateError('Insufficient points');t.set(ref,{'points':next,'updatedAt':FieldValue.serverTimestamp()},SetOptions(merge:true));t.set(tx,{'type':type,'groupId':g,'studentId':s,'amount':amount.abs(),'actorId':actor,'reason':reason,'createdAt':FieldValue.serverTimestamp()});});
  }
  Future<void> transfer({required String groupId,required String senderId,required String recipientId,required num amount,num commission=0})async{
    if(amount<=0||senderId==recipientId||commission<0)throw ArgumentError('Invalid transfer');
    final a=_students(groupId).doc(senderId),b=_students(groupId).doc(recipientId),tx=db.collection('transactions').doc();
    await db.runTransaction((t)async{final asnap=await t.get(a),bsnap=await t.get(b);final ab=(asnap.data()?['points'] as num?)??0;final bb=(bsnap.data()?['points'] as num?)??0;final total=amount+commission;if(ab<total)throw StateError('Insufficient points');t.update(a,{'points':ab-total});t.update(b,{'points':bb+amount});t.set(tx,{'type':'transfer','groupId':groupId,'senderId':senderId,'recipientId':recipientId,'amount':amount,'commission':commission,'createdAt':FieldValue.serverTimestamp()});});
  }
  Stream<QuerySnapshot<Map<String,dynamic>>> ranking(String groupId)=>_students(groupId).orderBy('points',descending:true).snapshots();
  Stream<QuerySnapshot<Map<String,dynamic>>> history(String groupId,String studentId)=>db.collection('transactions').where('groupId',isEqualTo:groupId).where('studentId',isEqualTo:studentId).snapshots();
}
