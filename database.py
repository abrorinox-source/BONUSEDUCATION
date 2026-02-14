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
        """Get group by sheet name (group_id is now sheet_name)
        
        Since groups are auto-detected from sheets, just return sheet info.
        """
        # group_id is now sheet_name - return simple dict
        return {
            'group_id': group_id,
            'name': group_id,
            'sheet_name': group_id
        }
    
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
        """Update group data"""
        try:
            self.groups_ref.document(group_id).update(updates)
            return True
        except Exception as e:
            print(f"Error updating group: {e}")
            return False
    
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
    
    def get_teacher_groups(self, teacher_id: str = None) -> List[Dict[str, Any]]:
        """Get all groups from Google Sheets tabs (auto-detect)
        
        Now reads directly from Google Sheets tabs instead of Firebase.
        teacher_id kept for compatibility but not used - all teachers see all sheets.
        """
        from sheets_manager import sheets_manager
        return sheets_manager.get_groups_from_sheets()


# Global database instance
db = FirebaseDB()
