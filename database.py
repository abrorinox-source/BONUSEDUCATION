"""
Firebase Firestore Database Manager
Handles all database operations
"""

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import SERVER_TIMESTAMP
from datetime import datetime
from typing import Optional, List, Dict, Any
import config
import os
import json


class FirebaseDB:
    """Firebase Firestore database manager"""
    
    def __init__(self):
        """Initialize Firebase connection"""
        if not firebase_admin._apps:
            # Try to get credentials from environment variable first (for Render)
            firebase_creds = os.getenv('FIREBASE_CREDENTIALS')
            
            if firebase_creds:
                # Use credentials from environment variable
                cred_dict = json.loads(firebase_creds)
                cred = credentials.Certificate(cred_dict)
            else:
                # Use credentials from file (for local development)
                cred = credentials.Certificate(config.FIREBASE_KEY_PATH)
            
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        self.users_ref = self.db.collection(config.COLLECTIONS['USERS'])
        self.settings_ref = self.db.collection(config.COLLECTIONS['SETTINGS'])
        self.logs_ref = self.db.collection(config.COLLECTIONS['TRANSACTION_LOGS'])
        self.groups_ref = self.db.collection(config.COLLECTIONS['GROUPS'])
    
    # ═══════════════════════════════════════════════════════════════════════════
    # USER OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        doc = self.users_ref.document(user_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['user_id'] = user_id
            return data
        return None
    
    def create_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Create new user"""
        try:
            user_data['created_at'] = SERVER_TIMESTAMP
            user_data['last_updated'] = SERVER_TIMESTAMP
            user_data['points'] = user_data.get('points', 0)
            user_data['last_synced_points'] = user_data.get('points', 0)
            
            self.users_ref.document(user_id).set(user_data)
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            updates['last_updated'] = SERVER_TIMESTAMP
            self.users_ref.document(user_id).update(updates)
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Soft delete user (mark as deleted)"""
        try:
            self.users_ref.document(user_id).update({
                'status': 'deleted',
                'deleted_at': SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def hard_delete_user(self, user_id: str) -> bool:
        """Permanently delete user from Firebase (hard delete)"""
        try:
            self.users_ref.document(user_id).delete()
            print(f"🗑️ Permanently deleted user: {user_id}")
            return True
        except Exception as e:
            print(f"Error hard deleting user: {e}")
            return False
    
    def get_all_users(self, role: Optional[str] = None, status: Optional[str] = None, group_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all users with optional filters"""
        query = self.users_ref
        
        if role:
            query = query.where('role', '==', role)
        if status:
            query = query.where('status', '==', status)
        if group_id:
            query = query.where('group_id', '==', group_id)
        
        users = []
        for doc in query.stream():
            user_data = doc.to_dict()
            user_data['user_id'] = doc.id
            users.append(user_data)
        
        return users
    
    def get_ranking(self, group_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active students sorted by points (optionally filtered by group)"""
        users = self.get_all_users(role='student', status='active', group_id=group_id)
        return sorted(users, key=lambda x: x.get('points', 0), reverse=True)
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get users awaiting approval (new registrations + restore requests)"""
        pending_new = self.get_all_users(status='pending')
        pending_restore = self.get_all_users(status='pending_restore')
        return pending_new + pending_restore
    
    # ═══════════════════════════════════════════════════════════════════════════
    # POINTS OPERATIONS (WITH TRANSACTIONS)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def transfer_points(self, sender_id: str, recipient_id: str, amount: int, commission: int) -> Dict[str, Any]:
        """Execute atomic points transfer"""
        try:
            sender_ref = self.users_ref.document(sender_id)
            recipient_ref = self.users_ref.document(recipient_id)
            
            # Create transaction and run the transactional function
            transaction = self.db.transaction()
            
            @firestore.transactional
            def do_transfer(transaction):
                # Read phase
                sender_doc = sender_ref.get(transaction=transaction)
                recipient_doc = recipient_ref.get(transaction=transaction)
                
                if not sender_doc.exists or not recipient_doc.exists:
                    raise ValueError("User not found")
                
                sender_data = sender_doc.to_dict()
                recipient_data = recipient_doc.to_dict()
                
                # Validate
                if sender_data.get('status') != 'active':
                    raise ValueError("Sender account is not active")
                if recipient_data.get('status') != 'active':
                    raise ValueError("Recipient account is not active")
                
                sender_balance = sender_data.get('points', 0)
                total_cost = amount + commission
                
                if sender_balance < total_cost:
                    raise ValueError(f"Insufficient balance: {sender_balance} < {total_cost}")
                
                # Write phase (atomic!)
                new_sender_balance = sender_balance - total_cost
                new_recipient_balance = recipient_data.get('points', 0) + amount
                
                transaction.update(sender_ref, {
                    'points': new_sender_balance,
                    'last_updated': SERVER_TIMESTAMP
                })
                
                transaction.update(recipient_ref, {
                    'points': new_recipient_balance,
                    'last_updated': SERVER_TIMESTAMP
                })
                
                return {
                    'sender_balance': new_sender_balance,
                    'recipient_balance': new_recipient_balance
                }
            
            result = do_transfer(transaction)
            
            return {
                'success': True,
                'sender_balance': result['sender_balance'],
                'recipient_balance': result['recipient_balance']
            }
        except ValueError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': f'Transaction failed: {str(e)}'}
    
    def add_points(self, user_id: str, amount: int) -> Dict[str, Any]:
        """Add points to user (atomic)"""
        try:
            user_ref = self.users_ref.document(user_id)
            
            # Create transaction and run the transactional function
            transaction = self.db.transaction()
            
            @firestore.transactional
            def do_add_points(transaction):
                user_doc = user_ref.get(transaction=transaction)
                
                if not user_doc.exists:
                    raise ValueError("User not found")
                
                current_points = user_doc.to_dict().get('points', 0)
                new_points = current_points + amount
                
                transaction.update(user_ref, {
                    'points': new_points,
                    'last_updated': SERVER_TIMESTAMP
                })
                
                return new_points
            
            new_balance = do_add_points(transaction)
            
            return {'success': True, 'new_balance': new_balance}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def subtract_points(self, user_id: str, amount: int) -> Dict[str, Any]:
        """Subtract points from user (atomic)"""
        return self.add_points(user_id, -amount)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SETTINGS OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_settings(self) -> Dict[str, Any]:
        """Get bot settings"""
        doc = self.settings_ref.document('bot_config').get()
        if doc.exists:
            return doc.to_dict()
        
        # Default settings
        default_settings = {
            'commission_rate': config.DEFAULT_COMMISSION_RATE,
            'bot_status': 'public',
            'maintenance': False,
            'sync_enabled': True,
            'sync_interval': config.DEFAULT_SYNC_INTERVAL,
            'sync_direction': 'bidirectional',
            'sync_statistics': {
                'total_syncs': 0,
                'successful_syncs': 0,
                'failed_syncs': 0,
                'last_error': None
            },
            'rules_text': (
                "📖 Bot Rules:\n\n"
                "1️⃣ Be respectful to all users\n"
                "2️⃣ No spam or inappropriate content\n"
                "3️⃣ Points are for academic purposes only\n"
                "4️⃣ Report any issues to teachers\n"
                "5️⃣ Follow school guidelines\n\n"
                "Violation of rules may result in point deduction or account suspension."
            )
        }
        self.settings_ref.document('bot_config').set(default_settings)
        return default_settings
    
    def update_settings(self, updates: Dict[str, Any]) -> bool:
        """Update bot settings"""
        try:
            # Use set with merge=True to create document if it doesn't exist
            self.settings_ref.document('bot_config').set(updates, merge=True)
            return True
        except Exception as e:
            print(f"❌ Error updating settings: {e}")
            return False
    
    def get_commission_rate(self) -> float:
        """Get current commission rate"""
        settings = self.get_settings()
        return settings.get('commission_rate', config.DEFAULT_COMMISSION_RATE)
    
    def is_maintenance_mode(self) -> bool:
        """Check if bot is in maintenance mode"""
        settings = self.get_settings()
        return settings.get('maintenance', False)
    
    def is_sync_enabled(self) -> bool:
        """Check if auto-sync is enabled"""
        settings = self.get_settings()
        return settings.get('sync_enabled', True)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TRANSACTION LOGGING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def log_transaction(self, log_data: Dict[str, Any]) -> bool:
        """Log a transaction"""
        try:
            log_data['timestamp'] = SERVER_TIMESTAMP
            self.logs_ref.add(log_data)
            return True
        except Exception as e:
            print(f"Error logging transaction: {e}")
            return False
    
    def log_transfer(self, sender_id: str, recipient_id: str, amount: int, commission: int,
                    sender_name: str, recipient_name: str) -> bool:
        """Log points transfer"""
        return self.log_transaction({
            'type': 'transfer',
            'sender_id': sender_id,
            'sender_name': sender_name,
            'recipient_id': recipient_id,
            'recipient_name': recipient_name,
            'amount': amount,
            'commission': commission,
            'total_deducted': amount + commission,
            'status': 'completed'
        })
    
    def log_add_points(self, teacher_id: str, student_id: str, amount: int,
                      student_name: str, reason: str = None) -> bool:
        """Log teacher adding points"""
        return self.log_transaction({
            'type': 'add_points',
            'teacher_id': teacher_id,
            'student_id': student_id,
            'student_name': student_name,
            'amount': amount,
            'reason': reason or 'No reason provided',
            'status': 'completed'
        })
    
    def log_subtract_points(self, teacher_id: str, student_id: str, amount: int,
                           student_name: str, reason: str = None) -> bool:
        """Log teacher removing points"""
        return self.log_transaction({
            'type': 'subtract_points',
            'teacher_id': teacher_id,
            'student_id': student_id,
            'student_name': student_name,
            'amount': amount,
            'reason': reason or 'No reason provided',
            'status': 'completed'
        })
    
    def log_manual_edit(self, user_id: str, user_name: str, old_points: int, new_points: int) -> bool:
        """Log manual edit from Google Sheets"""
        return self.log_transaction({
            'type': 'manual_edit',
            'user_id': user_id,
            'user_name': user_name,
            'old_points': old_points,
            'new_points': new_points,
            'delta': new_points - old_points,
            'source': 'google_sheets',
            'status': 'completed'
        })
    
    def clear_all_transaction_logs(self, progress_callback=None) -> int:
        """Delete all transaction logs from Firebase with progress tracking
        
        Args:
            progress_callback: Optional async function to call with progress updates
            
        Returns:
            Number of logs deleted
        """
        try:
            # First, get all logs to know total count
            logs_list = list(self.logs_ref.stream())
            total = len(logs_list)
            deleted_count = 0
            
            if total == 0:
                return 0
            
            print(f"🗑️ Starting to delete {total} transaction logs...")
            
            for log in logs_list:
                log.reference.delete()
                deleted_count += 1
                
                # Report progress every 10% or every 5 items (whichever is smaller)
                if progress_callback and (deleted_count % max(1, total // 10) == 0 or deleted_count == total):
                    import asyncio
                    progress = int((deleted_count / total) * 100)
                    asyncio.create_task(progress_callback(deleted_count, total, progress))
            
            print(f"🗑️ Cleared {deleted_count} transaction logs")
            return deleted_count
        except Exception as e:
            print(f"Error clearing transaction logs: {e}")
            return 0
    
    def get_transaction_logs(self, limit: int = 50, transaction_type: str = None) -> List[Dict[str, Any]]:
        """Get recent transaction logs"""
        try:
            if transaction_type:
                # Filter by type first, then sort client-side to avoid index requirement
                query = self.logs_ref.where('type', '==', transaction_type).limit(limit * 2)
                
                logs = []
                for doc in query.stream():
                    log = doc.to_dict()
                    log['id'] = doc.id
                    logs.append(log)
                
                # Sort by timestamp client-side
                logs.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
                return logs[:limit]
            else:
                # No filter, just order by timestamp
                query = self.logs_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
                
                logs = []
                for doc in query.stream():
                    log = doc.to_dict()
                    log['id'] = doc.id
                    logs.append(log)
                
                return logs
        
        except Exception as e:
            print(f"Error getting transaction logs: {e}")
            return []
    
    def get_user_history(self, user_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Get transaction history for specific user"""
        logs = []
        
        # Get logs where user is involved
        queries = [
            self.logs_ref.where('sender_id', '==', user_id).limit(limit),
            self.logs_ref.where('recipient_id', '==', user_id).limit(limit),
            self.logs_ref.where('student_id', '==', user_id).limit(limit)
        ]
        
        for query in queries:
            for doc in query.stream():
                log = doc.to_dict()
                log['id'] = doc.id
                logs.append(log)
        
        # Remove duplicates and sort
        unique_logs = {log['id']: log for log in logs}.values()
        sorted_logs = sorted(unique_logs, 
                           key=lambda x: x.get('timestamp', datetime.min), 
                           reverse=True)
        
        return list(sorted_logs)[:limit]
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GROUP OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def create_group(self, group_data: Dict[str, Any]) -> str:
        """Create a new group and return its ID"""
        try:
            group_data['created_at'] = SERVER_TIMESTAMP
            group_data['status'] = 'active'
            doc_ref = self.groups_ref.add(group_data)
            return doc_ref[1].id
        except Exception as e:
            print(f"Error creating group: {e}")
            return None
    
    def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get group by ID from Firebase
        
        Args:
            group_id: Can be either Firebase document ID or sheet_name
        
        Returns:
            Group data dict with group_id, name, and sheet_name
        """
        try:
            # First, try to get by document ID
            doc = self.groups_ref.document(group_id).get()
            if doc.exists:
                group_data = doc.to_dict()
                group_data['group_id'] = doc.id
                return group_data
            
            # If not found, search by sheet_name field
            query = self.groups_ref.where('sheet_name', '==', group_id).limit(1)
            docs = list(query.stream())
            if docs:
                group_data = docs[0].to_dict()
                group_data['group_id'] = docs[0].id
                return group_data
            
            # If still not found, assume group_id is the sheet_name
            # Return a minimal group object (for auto-detected sheets)
            print(f"⚠️ Group '{group_id}' not in Firebase, treating as sheet name")
            return {
                'group_id': group_id,
                'name': group_id,
                'sheet_name': group_id
            }
        except Exception as e:
            print(f"❌ Error getting group '{group_id}': {e}")
            return None
    
    def get_all_groups(self, status: str = 'active') -> List[Dict[str, Any]]:
        """Get all groups"""
        try:
            query = self.groups_ref.where('status', '==', status)
            groups = []
            for doc in query.stream():
                group_data = doc.to_dict()
                group_data['group_id'] = doc.id
                groups.append(group_data)
            return groups
        except Exception as e:
            print(f"Error getting groups: {e}")
            return []
    
    def update_group(self, group_id: str, updates: Dict[str, Any]) -> bool:
        """Update group data (or create if doesn't exist)"""
        try:
            doc_ref = self.groups_ref.document(group_id)
            doc = doc_ref.get()
            
            if doc.exists:
                # Document exists, update it
                doc_ref.update(updates)
                print(f"✅ Updated group '{group_id}' in Firebase")
            else:
                # Document doesn't exist, create it
                updates['created_at'] = SERVER_TIMESTAMP
                updates['status'] = 'active'
                doc_ref.set(updates)
                print(f"✅ Created group '{group_id}' in Firebase (didn't exist before)")
            
            return True
        except Exception as e:
            print(f"⚠️ Error updating/creating group: {e}")
            # Don't fail the whole operation if Firebase group update fails
            # Students' group_id is the critical part
            return True  # Return True anyway since students were updated
    
    def delete_group(self, group_id: str) -> bool:
        """Soft delete group"""
        try:
            self.groups_ref.document(group_id).update({
                'status': 'deleted',
                'deleted_at': SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"Error deleting group: {e}")
            return False
    
    def get_orphaned_students(self) -> List[Dict[str, Any]]:
        """Get students whose group no longer exists
        
        Returns:
            List of student dicts with non-existent group_id
        """
        orphaned = []
        try:
            # Get current valid group IDs from cache
            cache_doc = self.settings_ref.document('groups_cache').get()
            if cache_doc.exists:
                groups = cache_doc.to_dict().get('groups', [])
                valid_group_ids = {g['group_id'] for g in groups}
            else:
                valid_group_ids = set()
            
            # Get all active students
            students = self.get_all_users(role='student', status='active')
            
            # Find orphaned students (group doesn't exist)
            for student in students:
                student_group_id = student.get('group_id')
                if student_group_id and student_group_id not in valid_group_ids:
                    orphaned.append(student)
            
            print(f"🔍 Found {len(orphaned)} orphaned students")
            return orphaned
        except Exception as e:
            print(f"❌ Error getting orphaned students: {e}")
            return []
    
    def cleanup_deleted_students(self, sheets_user_ids: List[str], group_id: Optional[str] = None) -> int:
        """Delete students from Firebase if they don't exist in Google Sheets
        
        Args:
            sheets_user_ids: List of user_ids currently in Google Sheets
            group_id: Only cleanup students from this specific group (important for multi-group!)
            
        Returns:
            Number of students deleted from Firebase
        """
        deleted_count = 0
        try:
            # Get active students from Firebase (filtered by group if provided)
            # CRITICAL: Only check students from the specific group!
            students = self.get_all_users(role='student', status='active', group_id=group_id)
            
            # Convert sheets_user_ids to set for faster lookup
            sheets_ids_set = set(sheets_user_ids)
            
            for student in students:
                user_id = student.get('user_id')
                
                # If student exists in Firebase but NOT in Sheets, delete from Firebase
                if user_id and user_id not in sheets_ids_set:
                    # Delete from Firebase
                    self.users_ref.document(user_id).delete()
                    deleted_count += 1
                    print(f"  🗑️ Deleted {student.get('full_name', user_id)} (not in Sheets)")
            
            if deleted_count > 0:
                print(f"✅ Cleaned up {deleted_count} deleted students from Firebase")
            
            return deleted_count
            
        except Exception as e:
            print(f"⚠️ Error cleaning up deleted students: {e}")
            return 0
    
    def update_students_group_id(self, old_group_id: str, new_group_id: str) -> int:
        """Update all students' group_id when a sheet is renamed
        
        Args:
            old_group_id: Old sheet name (group ID)
            new_group_id: New sheet name (group ID)
        Returns:
            Number of students updated
        """
        updated_count = 0
        try:
            # Get all students with the old group_id
            students = self.get_all_users(role='student', group_id=old_group_id)
            
            print(f"📝 Updating group_id for {len(students)} students: '{old_group_id}' → '{new_group_id}'")
            
            for student in students:
                self.update_user(student['user_id'], {'group_id': new_group_id})
                updated_count += 1
                print(f"  ✅ {student.get('full_name')} → {new_group_id}")
            
            if updated_count > 0:
                print(f"✅ Updated {updated_count} students' group_id successfully")
            return updated_count
        except Exception as e:
            print(f"⚠️ Error updating student group_id: {e}")
            return 0
    
    def sync_new_groups_to_firebase(self, groups: List[Dict[str, Any]]) -> int:
        """Sync new groups from Google Sheets to Firebase groups collection
        
        Args:
            groups: List of groups from Google Sheets
            
        Returns:
            Number of new groups added to Firebase
        """
        new_groups_count = 0
        try:
            for group in groups:
                sheet_name = group.get('sheet_name')
                if not sheet_name:
                    continue
                
                # Check if group already exists in Firebase (by sheet_name)
                query = self.groups_ref.where('sheet_name', '==', sheet_name).limit(1)
                existing = list(query.stream())
                
                if not existing:
                    # New group - add to Firebase
                    # Use sheet_name as document ID for consistency
                    doc_id = sheet_name.lower().replace(' ', '_')
                    
                    group_data = {
                        'name': group.get('name', sheet_name),
                        'sheet_name': sheet_name,
                        'status': 'active',
                        'hidden': False,  # ⭐ Set to True in Firebase to hide group from bot UI
                        'created_at': SERVER_TIMESTAMP,
                        'auto_created': True  # Mark as auto-created from Sheets
                    }
                    
                    self.groups_ref.document(doc_id).set(group_data)
                    new_groups_count += 1
                    print(f"  ➕ Added new group to Firebase: '{sheet_name}' (ID: {doc_id})")
            
            if new_groups_count > 0:
                print(f"✅ Synced {new_groups_count} new group(s) to Firebase")
            
            return new_groups_count
            
        except Exception as e:
            print(f"⚠️ Error syncing groups to Firebase: {e}")
            return 0
    
    def refresh_groups_cache(self) -> List[Dict[str, Any]]:
        """Refresh groups cache from Google Sheets"""
        from sheets_manager import sheets_manager
        groups = sheets_manager.get_groups_from_sheets()
        
        # ⭐ NEW: Sync new groups to Firebase groups collection
        print("🔍 Checking for new groups to add to Firebase...")
        self.sync_new_groups_to_firebase(groups)
        
        # Get old cache for comparison (to detect renames)
        old_groups = []
        try:
            cache_doc = self.settings_ref.document('groups_cache').get()
            if cache_doc.exists:
                old_groups = cache_doc.to_dict().get('groups', [])
        except:
            pass
        
        # ⭐⭐⭐ CRITICAL: Check for renamed sheets FIRST, before cleanup
        # This prevents accidentally deleting students when a group was just renamed
        renamed_groups = set()  # Track which groups were renamed
        
        if old_groups:
            old_names = {g['group_id'] for g in old_groups}
            new_names = {g['group_id'] for g in groups}
            
            # Detect sheet renames by comparing old and new lists
            print("🔍 Checking for renamed sheets...")
            
            # Simple detection: if a sheet disappeared and a new one appeared, might be renamed
            removed = old_names - new_names
            added = new_names - old_names
            
            if removed and added and len(removed) == len(added) == 1:
                old_name = list(removed)[0]
                new_name = list(added)[0]
                print(f"  🔄 Detected rename: '{old_name}' → '{new_name}'")
                
                # Update students' group_id
                self.update_students_group_id(old_name, new_name)
                
                # ⭐ Update Firebase groups collection
                # Delete old document and create new one with correct ID
                try:
                    # Find old document
                    query = self.groups_ref.where('sheet_name', '==', old_name).limit(1).stream()
                    docs = list(query)
                    
                    if docs:
                        old_doc = docs[0]
                        old_doc_data = old_doc.to_dict()
                        old_doc_id = old_doc.id
                        
                        # Create new document with new sheet_name as ID
                        new_doc_id = new_name.lower().replace(' ', '_')
                        new_doc_data = old_doc_data.copy()
                        new_doc_data['name'] = new_name
                        new_doc_data['sheet_name'] = new_name
                        
                        # Create new document
                        self.groups_ref.document(new_doc_id).set(new_doc_data)
                        
                        # Delete old document
                        old_doc.reference.delete()
                        
                        print(f"  ✅ Renamed Firebase group: '{old_doc_id}' → '{new_doc_id}'")
                    else:
                        print(f"  ⚠️ Old group document not found in Firebase")
                        
                except Exception as e:
                    print(f"  ⚠️ Error renaming Firebase group: {e}")
                renamed_groups.add(old_name)  # Mark this group as renamed, not deleted
            
            # ⭐ DELETE truly deleted groups from Firebase (not renamed ones)
            else:
                # No rename detected - check for deleted groups
                if removed:
                    print(f"  🔍 Detected deleted groups: {removed}")
                    for deleted_group_name in removed:
                        try:
                            # Find and delete the Firebase group document
                            query = self.groups_ref.where('sheet_name', '==', deleted_group_name).limit(1).stream()
                            docs = list(query)
                            if docs:
                                doc = docs[0]
                                doc_id = doc.id
                                doc.reference.delete()
                                print(f"  🗑️ Deleted Firebase group: '{deleted_group_name}' (ID: {doc_id})")
                            else:
                                print(f"  ⚠️ Group '{deleted_group_name}' not found in Firebase")
                        except Exception as e:
                            print(f"  ⚠️ Error deleting Firebase group '{deleted_group_name}': {e}")
        
        # Save to settings as cache
        try:
            from google.cloud.firestore import SERVER_TIMESTAMP
            self.settings_ref.document('groups_cache').set({
                'groups': groups,
                'last_updated': SERVER_TIMESTAMP
            })
            print(f"✅ Cached {len(groups)} groups")
        except Exception as e:
            print(f"⚠️ Failed to cache groups: {e}")
        
        return groups
    
    def get_teacher_groups(self, teacher_id: str = None, force_refresh: bool = False, include_hidden: bool = False) -> List[Dict[str, Any]]:
        """Get all groups (from cache or refresh from Sheets)
        
        Args:
            teacher_id: Not used, kept for compatibility
            force_refresh: If True, bypass cache and fetch from Sheets
            include_hidden: If False (default), filter out groups with hidden=True
        
        Returns cached groups for speed, unless force_refresh=True
        """
        if force_refresh:
            groups = self.refresh_groups_cache()
        else:
            # Try to get from cache first
            try:
                cache_doc = self.settings_ref.document('groups_cache').get()
                if cache_doc.exists:
                    cached_data = cache_doc.to_dict()
                    groups = cached_data.get('groups', [])
                    if groups:
                        print(f"✅ Using cached groups ({len(groups)} groups)")
                    else:
                        # No cache, refresh from Sheets
                        print("📊 No cache found, fetching from Sheets...")
                        groups = self.refresh_groups_cache()
                else:
                    # No cache, refresh from Sheets
                    print("📊 No cache found, fetching from Sheets...")
                    groups = self.refresh_groups_cache()
            except Exception as e:
                print(f"⚠️ Cache read failed: {e}")
                # No cache, refresh from Sheets
                print("📊 No cache found, fetching from Sheets...")
                groups = self.refresh_groups_cache()
        
        # ⭐ Filter out hidden groups (unless include_hidden=True)
        if not include_hidden:
            visible_groups = []
            for group in groups:
                # Check if group is hidden in Firebase
                group_id = group.get('group_id')
                firebase_group = self.get_group(group_id)
                
                # If hidden field exists and is True, skip this group
                if firebase_group and firebase_group.get('hidden', False):
                    print(f"  🙈 Hiding group: {group.get('name', group_id)}")
                    continue
                
                visible_groups.append(group)
            
            if len(visible_groups) < len(groups):
                print(f"✅ Filtered out {len(groups) - len(visible_groups)} hidden group(s)")
            
            return visible_groups
        
        return groups


# Global database instance
db = FirebaseDB()
