"""
Database access layer for Sheets data and Firestore transaction logs.
"""

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import SERVER_TIMESTAMP
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app import config
import os
import json
import threading


class FirebaseDB:
    """Database access layer."""

    def __init__(self):
        """Initialize Firebase connection"""
        if not firebase_admin._apps:
            firebase_creds = os.getenv('FIREBASE_CREDENTIALS')

            if firebase_creds:
                cred_dict = json.loads(firebase_creds)
                cred = credentials.Certificate(cred_dict)
            else:
                cred = credentials.Certificate(config.FIREBASE_KEY_PATH)

            firebase_admin.initialize_app(cred)

        self.db = firestore.client()
        self.users_ref = self.db.collection(config.COLLECTIONS['USERS'])
        self.settings_ref = self.db.collection(config.COLLECTIONS['SETTINGS'])
        self.logs_ref = self.db.collection(config.COLLECTIONS['TRANSACTION_LOGS'])
        self.transfer_limit_usage_ref = self.db.collection(config.COLLECTIONS['TRANSFER_LIMIT_USAGE'])
        self.transfer_limit_overrides_ref = self.db.collection(config.COLLECTIONS['TRANSFER_LIMIT_OVERRIDES'])
        self._settings_cache = None
        self._points_lock = threading.RLock()

    # ═══════════════════════════════════════════════════════════════════════════
    # USER OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_user(self, user_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Get user by ID from Firestore or Google Sheets."""
        try:
            doc = self.users_ref.document(user_id).get()
            if doc.exists:
                data = doc.to_dict() or {}
                data['user_id'] = user_id
                if data.get('role') == 'teacher' or data.get('status') in {'pending', 'pending_restore', 'approved_pending_group'}:
                    return data
        except Exception:
            pass
        from app.sheets_manager import sheets_manager
        try:
            sheet_user = sheets_manager.get_user(user_id, force_refresh=force_refresh)
        except Exception as e:
            print(f"Error getting user from Sheets: {e}")
            sheet_user = None
        if sheet_user:
            return sheet_user
        try:
            doc = self.users_ref.document(user_id).get()
            if doc.exists:
                data = doc.to_dict() or {}
                data['user_id'] = user_id
                return data
        except Exception:
            pass
        return None


    def create_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Create user in Firestore for teachers/pending users or Sheets for active students."""
        from app.sheets_manager import sheets_manager
        role = user_data.get('role', 'student')
        status = user_data.get('status', 'pending')

        if role == 'teacher' or status in {'pending', 'pending_restore', 'approved_pending_group'}:
            payload = dict(user_data)
            payload['user_id'] = user_id
            self.users_ref.document(user_id).set(payload, merge=True)
            return True

        sheet_name = user_data.get('group_id') or 'Sheet1'
        payload = {
            'user_id': user_id,
            'full_name': user_data.get('full_name', ''),
            'phone': user_data.get('phone', ''),
            'username': user_data.get('username', ''),
            'points': user_data.get('points', 0),
            'role': role,
            'status': 'active'
        }
        return sheets_manager.add_user(payload, sheet_name=sheet_name)


    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update Firestore user state or Sheets student row."""
        try:
            doc = self.users_ref.document(user_id).get()
            if doc.exists:
                current = doc.to_dict() or {}
                if current.get('role') == 'teacher' or current.get('status') in {'pending', 'pending_restore', 'approved_pending_group'}:
                    current.update(updates)
                    self.users_ref.document(user_id).set(current, merge=True)
                    return True
        except Exception:
            pass

        from app.sheets_manager import sheets_manager
        user = sheets_manager.get_user(user_id, force_refresh=True)
        if not user:
            return False
        sheet_name = user.get('group_id', 'Sheet1')
        if set(updates.keys()) <= {'points'}:
            return sheets_manager.update_row(user_id, updates['points'], sheet_name=sheet_name)
        merged = {**user, **updates}
        return sheets_manager.update_user_row(user_id, merged, sheet_name=sheet_name)


    def delete_user(self, user_id: str) -> bool:
        """Delete user from Firestore or Google Sheets."""
        try:
            doc = self.users_ref.document(user_id).get()
            if doc.exists:
                current = doc.to_dict() or {}
                if current.get('role') == 'teacher' or current.get('status') in {'pending', 'pending_group', 'pending_restore', 'approved_pending_group'}:
                    self.users_ref.document(user_id).delete()
                    return True
        except Exception:
            pass

        from app.sheets_manager import sheets_manager
        return sheets_manager.delete_user(user_id)


    def hard_delete_user(self, user_id: str) -> bool:
        """Permanently delete user from Google Sheets."""
        return self.delete_user(user_id)


    def get_all_users(self, role: Optional[str] = None, status: Optional[str] = None, group_id: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get all users from Firestore and Google Sheets."""
        users: List[Dict[str, Any]] = []

        try:
            for doc in self.users_ref.stream():
                data = doc.to_dict() or {}
                data['user_id'] = doc.id
                users.append(data)
        except Exception:
            pass

        from app.sheets_manager import sheets_manager
        users.extend(sheets_manager.get_all_users(group_id=group_id, force_refresh=force_refresh))
        if role:
            users = [u for u in users if u.get('role') == role]
        if status:
            users = [u for u in users if u.get('status') == status]
        if group_id:
            users = [u for u in users if u.get('group_id') == group_id]
        return users


    def get_ranking(self, group_id: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get all active students sorted by points from Google Sheets."""
        from app.sheets_manager import sheets_manager
        return sheets_manager.get_ranking(group_id=group_id, force_refresh=force_refresh)


    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Return pending student registrations and restorations from Firestore."""
        pending: List[Dict[str, Any]] = []
        try:
            for doc in self.users_ref.stream():
                data = doc.to_dict() or {}
                if data.get('status') in ('pending', 'pending_restore'):
                    data['user_id'] = doc.id
                    pending.append(data)
        except Exception:
            pass
        return pending

    def _default_settings(self) -> Dict[str, Any]:
        """Return default bot settings for Sheets-only mode."""
        return {
            'commission_rate': config.DEFAULT_COMMISSION_RATE,
            'commission_pool': 0,
            'daily_transfer_count_limit': 0,
            'weekly_transfer_count_limit': 0,
            'daily_transfer_points_limit': 0,
            'weekly_transfer_points_limit': 0,
            'bot_status': 'public',
            'maintenance': False,
            'sync_enabled': True,
            'sync_interval': config.DEFAULT_SYNC_INTERVAL,
            'sync_direction': 'sheets_only',
            'sync_statistics': {
                'total_syncs': 0,
                'successful_syncs': 0,
                'failed_syncs': 0,
                'last_error': None
            },
            'rules_text': (
                "Bot Rules:\n\n"
                "1. Be respectful to all users\n"
                "2. No spam or inappropriate content\n"
                "3. Points are for academic purposes only\n"
            )
        }

    def get_settings(self) -> Dict[str, Any]:
        """Get bot settings from Firestore, falling back to defaults."""
        defaults = self._default_settings()
        try:
            doc = self.settings_ref.document('bot_config').get()
            if doc.exists:
                settings = {**defaults, **(doc.to_dict() or {})}
            else:
                self.settings_ref.document('bot_config').set(defaults)
                settings = defaults
            self._settings_cache = settings
            return settings
        except Exception as e:
            print(f"Error getting settings: {e}")
            return self._settings_cache or defaults

    def update_settings(self, updates: Dict[str, Any]) -> bool:
        """Persist bot settings."""
        try:
            self.settings_ref.document('bot_config').set(updates, merge=True)
            current = self._settings_cache or self._default_settings()
            self._settings_cache = {**current, **updates}
            return True
        except Exception as e:
            print(f"Error updating settings: {e}")
            return False

    def get_transfer_limit_settings(self) -> Dict[str, int]:
        """Return transfer limit settings as integers; 0 means unlimited."""
        settings = self.get_settings()
        return {
            'daily_transfer_count_limit': int(settings.get('daily_transfer_count_limit', 0) or 0),
            'weekly_transfer_count_limit': int(settings.get('weekly_transfer_count_limit', 0) or 0),
            'daily_transfer_points_limit': int(settings.get('daily_transfer_points_limit', 0) or 0),
            'weekly_transfer_points_limit': int(settings.get('weekly_transfer_points_limit', 0) or 0),
        }

    def get_transfer_limit_override(self, user_id: str) -> Dict[str, int]:
        """Return per-user transfer limit overrides; 0 means fall back to global."""
        defaults = {
            'daily_transfer_count_limit': 0,
            'weekly_transfer_count_limit': 0,
            'daily_transfer_points_limit': 0,
            'weekly_transfer_points_limit': 0,
        }
        if not str(user_id).isdigit():
            return defaults
        try:
            doc = self.transfer_limit_overrides_ref.document(str(user_id)).get()
            if doc.exists:
                data = doc.to_dict() or {}
                return {
                    key: int(data.get(key, 0) or 0)
                    for key in defaults
                }
        except Exception as e:
            print(f"Error getting transfer limit override: {e}")
        return defaults

    def get_effective_transfer_limits(self, user_id: str) -> Dict[str, int]:
        """Return effective transfer limits after applying per-user overrides."""
        settings = self.get_transfer_limit_settings()
        overrides = self.get_transfer_limit_override(user_id)
        effective = {}
        for key, value in settings.items():
            override_value = int(overrides.get(key, 0) or 0)
            effective[key] = override_value if override_value > 0 else value
        return effective

    def update_transfer_limit_override(self, user_id: str, updates: Dict[str, int]) -> bool:
        """Persist per-user transfer limit overrides."""
        if not str(user_id).isdigit():
            return False
        payload = {key: int(value) for key, value in updates.items()}
        try:
            self.transfer_limit_overrides_ref.document(str(user_id)).set(payload, merge=True)
            return True
        except Exception as e:
            print(f"Error updating transfer limit override: {e}")
            return False

    def reset_transfer_limit_override(self, user_id: str) -> bool:
        """Remove per-user transfer limit overrides."""
        if not str(user_id).isdigit():
            return False
        try:
            self.transfer_limit_overrides_ref.document(str(user_id)).delete()
            return True
        except Exception as e:
            print(f"Error resetting transfer limit override: {e}")
            return False

    def _current_transfer_windows(self) -> Dict[str, str]:
        """Return current daily and weekly window markers."""
        now = datetime.utcnow()
        day_start = now.date()
        week_start = day_start - timedelta(days=day_start.weekday())
        return {
            'daily_window_start': day_start.isoformat(),
            'weekly_window_start': week_start.isoformat(),
        }

    def get_transfer_usage(self, user_id: str) -> Dict[str, Any]:
        """Get per-user transfer usage with automatic day/week rollover."""
        windows = self._current_transfer_windows()
        usage = {
            'daily_count': 0,
            'daily_points': 0,
            'weekly_count': 0,
            'weekly_points': 0,
            **windows,
        }

        if not str(user_id).isdigit():
            return usage

        try:
            doc = self.transfer_limit_usage_ref.document(str(user_id)).get()
            if doc.exists:
                usage.update(doc.to_dict() or {})
        except Exception as e:
            print(f"Error getting transfer usage: {e}")

        if usage.get('daily_window_start') != windows['daily_window_start']:
            usage['daily_count'] = 0
            usage['daily_points'] = 0
            usage['daily_window_start'] = windows['daily_window_start']

        if usage.get('weekly_window_start') != windows['weekly_window_start']:
            usage['weekly_count'] = 0
            usage['weekly_points'] = 0
            usage['weekly_window_start'] = windows['weekly_window_start']

        usage['daily_count'] = int(usage.get('daily_count', 0) or 0)
        usage['daily_points'] = int(usage.get('daily_points', 0) or 0)
        usage['weekly_count'] = int(usage.get('weekly_count', 0) or 0)
        usage['weekly_points'] = int(usage.get('weekly_points', 0) or 0)
        return usage

    def check_transfer_limits(self, user_id: str, amount: int) -> Dict[str, Any]:
        """Check whether a transfer fits the configured per-user limits."""
        amount = int(amount)
        settings = self.get_effective_transfer_limits(user_id)
        usage = self.get_transfer_usage(user_id)

        violations = []
        if settings['daily_transfer_count_limit'] > 0 and usage['daily_count'] + 1 > settings['daily_transfer_count_limit']:
            violations.append(f"Daily transfer count limit reached ({settings['daily_transfer_count_limit']})")
        if settings['weekly_transfer_count_limit'] > 0 and usage['weekly_count'] + 1 > settings['weekly_transfer_count_limit']:
            violations.append(f"Weekly transfer count limit reached ({settings['weekly_transfer_count_limit']})")
        if settings['daily_transfer_points_limit'] > 0 and usage['daily_points'] + amount > settings['daily_transfer_points_limit']:
            violations.append(f"Daily transfer points limit exceeded ({settings['daily_transfer_points_limit']} pts)")
        if settings['weekly_transfer_points_limit'] > 0 and usage['weekly_points'] + amount > settings['weekly_transfer_points_limit']:
            violations.append(f"Weekly transfer points limit exceeded ({settings['weekly_transfer_points_limit']} pts)")

        return {
            'allowed': not violations,
            'error': "\n".join(violations),
            'usage': usage,
            'settings': settings,
        }

    def record_transfer_usage(self, user_id: str, amount: int, usage: Optional[Dict[str, Any]] = None) -> bool:
        """Increment per-user transfer usage counters."""
        if not str(user_id).isdigit():
            return True

        usage = dict(usage or self.get_transfer_usage(user_id))
        usage['daily_count'] = int(usage.get('daily_count', 0) or 0) + 1
        usage['daily_points'] = int(usage.get('daily_points', 0) or 0) + int(amount)
        usage['weekly_count'] = int(usage.get('weekly_count', 0) or 0) + 1
        usage['weekly_points'] = int(usage.get('weekly_points', 0) or 0) + int(amount)

        try:
            self.transfer_limit_usage_ref.document(str(user_id)).set(usage, merge=True)
            return True
        except Exception as e:
            print(f"Error recording transfer usage: {e}")
            return False

    def reset_all_transfer_usage(self) -> bool:
        """Clear all stored per-user transfer usage counters."""
        try:
            for doc in self.transfer_limit_usage_ref.stream():
                doc.reference.delete()
            return True
        except Exception as e:
            print(f"Error resetting transfer usage: {e}")
            return False

    def add_points(self, user_id: str, amount: int) -> Dict[str, Any]:
        """Add points to an active user stored in Sheets."""
        try:
            amount = int(amount)
            with self._points_lock:
                user = self.get_user(user_id)
                if not user:
                    return {'success': False, 'error': 'User not found'}
                if user.get('status') != 'active':
                    return {'success': False, 'error': 'User account is not active'}

                new_balance = int(user.get('points', 0)) + amount
                if new_balance < 0:
                    return {'success': False, 'error': 'Insufficient balance'}

                if not self.update_user(user_id, {'points': new_balance}):
                    return {'success': False, 'error': 'Failed to update user balance'}

                return {'success': True, 'new_balance': new_balance}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def subtract_points(self, user_id: str, amount: int) -> Dict[str, Any]:
        """Subtract points from an active user stored in Sheets."""
        try:
            amount = int(amount)
            if amount <= 0:
                return {'success': False, 'error': 'Amount must be positive'}
            return self.add_points(user_id, -amount)
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def transfer_points(self, sender_id: str, recipient_id: str, amount: int, commission: int) -> Dict[str, Any]:
        """Transfer points between active Sheets users."""
        try:
            amount = int(amount)
            commission = int(commission)
            if sender_id == recipient_id:
                return {'success': False, 'error': 'Cannot transfer to yourself'}
            if amount <= 0:
                return {'success': False, 'error': 'Amount must be positive'}
            if commission < 0:
                return {'success': False, 'error': 'Commission cannot be negative'}

            with self._points_lock:
                sender = self.get_user(sender_id)
                recipient = self.get_user(recipient_id)

                if not sender or not recipient:
                    return {'success': False, 'error': 'User not found'}
                if sender.get('status') != 'active':
                    return {'success': False, 'error': 'Sender account is not active'}
                if recipient.get('status') != 'active':
                    return {'success': False, 'error': 'Recipient account is not active'}

                limit_check = self.check_transfer_limits(sender_id, amount)
                if not limit_check['allowed']:
                    return {'success': False, 'error': limit_check['error']}

                sender_balance = int(sender.get('points', 0))
                recipient_balance = int(recipient.get('points', 0))
                total_cost = amount + commission

                if sender_balance < total_cost:
                    return {'success': False, 'error': f'Insufficient balance: {sender_balance} < {total_cost}'}

                new_sender_balance = sender_balance - total_cost
                new_recipient_balance = recipient_balance + amount

                if not self.update_user(sender_id, {'points': new_sender_balance}):
                    return {'success': False, 'error': 'Failed to update sender balance'}

                if not self.update_user(recipient_id, {'points': new_recipient_balance}):
                    self.update_user(sender_id, {'points': sender_balance})
                    return {'success': False, 'error': 'Failed to update recipient balance'}

                current_pool = int(self.get_settings().get('commission_pool', 0) or 0)
                if commission > 0:
                    if not self.update_settings({'commission_pool': current_pool + commission}):
                        self.update_user(sender_id, {'points': sender_balance})
                        self.update_user(recipient_id, {'points': recipient_balance})
                        return {'success': False, 'error': 'Failed to update commission pool'}

                if not self.record_transfer_usage(sender_id, amount, usage=limit_check['usage']):
                    self.update_user(sender_id, {'points': sender_balance})
                    self.update_user(recipient_id, {'points': recipient_balance})
                    if commission > 0:
                        self.update_settings({'commission_pool': current_pool})
                    return {'success': False, 'error': 'Failed to update transfer limit usage'}

                return {
                    'success': True,
                    'sender_balance': new_sender_balance,
                    'recipient_balance': new_recipient_balance
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_commission_rate(self) -> float:
        """Get current commission rate"""
        settings = self.get_settings()
        return settings.get('commission_rate', config.DEFAULT_COMMISSION_RATE)

    def get_commission_pool(self) -> int:
        """Get accumulated commission pool."""
        settings = self.get_settings()
        return int(settings.get('commission_pool', 0) or 0)

    def is_maintenance_mode(self) -> bool:
        """Check if bot is in maintenance mode"""
        settings = self.get_settings()
        return settings.get('maintenance', False)

    def is_sync_enabled(self) -> bool:
        """Check whether Sheets cache sync is enabled."""
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
                    sender_name: str, recipient_name: str,
                    sender_old_balance: int = None, sender_new_balance: int = None,
                    recipient_old_balance: int = None, recipient_new_balance: int = None) -> bool:
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
            'sender_old_balance': sender_old_balance,
            'sender_new_balance': sender_new_balance,
            'recipient_old_balance': recipient_old_balance,
            'recipient_new_balance': recipient_new_balance,
            'status': 'completed'
        })

    def log_add_points(self, teacher_id: str, student_id: str, amount: int,
                      student_name: str,
                      old_balance: int = None, new_balance: int = None) -> bool:
        """Log teacher adding points"""
        return self.log_transaction({
            'type': 'add_points',
            'teacher_id': teacher_id,
            'student_id': student_id,
            'student_name': student_name,
            'amount': amount,
            'old_balance': old_balance,
            'new_balance': new_balance,
            'status': 'completed'
        })

    def log_subtract_points(self, teacher_id: str, student_id: str, amount: int,
                           student_name: str,
                           old_balance: int = None, new_balance: int = None) -> bool:
        """Log teacher removing points"""
        return self.log_transaction({
            'type': 'subtract_points',
            'teacher_id': teacher_id,
            'student_id': student_id,
            'student_name': student_name,
            'amount': amount,
            'old_balance': old_balance,
            'new_balance': new_balance,
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
        """Create a new group as a sheet tab."""
        from app.sheets_manager import sheets_manager
        sheet_name = group_data.get("sheet_name") or group_data.get("name") or group_data.get("group_id")
        if not sheet_name:
            return None
        created = sheets_manager.create_sheet_tab(sheet_name)
        return sheet_name if created else None

    def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get group metadata from Google Sheets."""
        from app.sheets_manager import sheets_manager
        return sheets_manager.get_group(group_id)

    def get_all_groups(self, status: str = 'active') -> List[Dict[str, Any]]:
        """Get all groups from Google Sheets."""
        from app.sheets_manager import sheets_manager
        return sheets_manager.get_groups_from_sheets()

    def update_group(self, group_id: str, updates: Dict[str, Any]) -> bool:
        """Update group metadata in Sheets-only mode."""
        return True

    def delete_group(self, group_id: str) -> bool:
        """Delete group in Sheets-only mode."""
        from app.sheets_manager import sheets_manager
        return sheets_manager.delete_sheet_tab(group_id)

    def get_orphaned_students(self) -> List[Dict[str, Any]]:
        """No orphaned students concept in Sheets-only mode."""
        return []

    def cleanup_deleted_students(self, sheets_user_ids: List[str], group_id: Optional[str] = None) -> int:
        """No Firebase cleanup needed in Sheets-only mode."""
        return 0

    def update_students_group_id(self, old_group_id: str, new_group_id: str) -> int:
        """Student group ids are derived from sheet tabs in Sheets-only mode."""
        return 0

    def sync_new_groups_to_firebase(self, groups: List[Dict[str, Any]]) -> int:
        """No Firebase group sync in Sheets-only mode."""
        return 0


    def refresh_groups_cache(self) -> List[Dict[str, Any]]:
        """Refresh groups directly from Google Sheets."""
        from app.sheets_manager import sheets_manager
        return sheets_manager.get_groups_from_sheets(force_refresh=True)


    def get_teacher_groups(self, teacher_id: str = None, force_refresh: bool = False, include_hidden: bool = False) -> List[Dict[str, Any]]:
        """Get all groups directly from Google Sheets, cached by default."""
        from app.sheets_manager import sheets_manager
        return sheets_manager.get_groups_from_sheets(force_refresh=force_refresh)


# Global database instance
db = FirebaseDB()
