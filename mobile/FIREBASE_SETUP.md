# Firebase setup for Android

The source tree intentionally does not contain real Firebase credentials.

1. Create/select the Firebase project.
2. Enable Authentication -> Email/Password.
3. Enable Firestore Database.
4. From Firebase Console, add an Android app using the package name generated for this project (`com.example.bonus_education` unless you change it).
5. Download `google-services.json` into `mobile/android/app/`.
6. Run FlutterFire CLI to generate `mobile/lib/firebase_options.dart`, or configure Firebase initialization for the Android app.
7. Deploy `mobile/firestore.rules` with the Firebase CLI.
8. Create at least one `users/{uid}` document with `role: teacher` or `role: student`.
9. Create groups under `groups/{groupId}` and students under `groups/{groupId}/students/{studentId}`.

Never commit real Firebase credentials or service-account keys to this repository.
