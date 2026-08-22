import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';

class AuthService {
  final FirebaseAuth auth;
  final FirebaseFirestore db;
  AuthService({FirebaseAuth? auth, FirebaseFirestore? db})
      : auth = auth ?? FirebaseAuth.instance,
        db = db ?? FirebaseFirestore.instance;

  Stream<User?> get authState => auth.authStateChanges();

  Future<UserCredential> signIn(String email, String password) =>
      auth.signInWithEmailAndPassword(email: email.trim(), password: password);

  Future<UserCredential> register({required String email, required String password, required String name}) async {
    final credential = await auth.createUserWithEmailAndPassword(
      email: email.trim(), password: password);
    final uid = credential.user!.uid;
    await db.collection('users').doc(uid).set({
      'name': name.trim(), 'email': email.trim(), 'role': 'student',
      'status': 'active', 'createdAt': FieldValue.serverTimestamp(),
    });
    return credential;
  }

  Stream<String> roleStream(String uid) => db.collection('users').doc(uid).snapshots().map(
        (doc) => (doc.data()?['role'] as String?) ?? 'student',
      );

  Future<void> signOut() => auth.signOut();
}
