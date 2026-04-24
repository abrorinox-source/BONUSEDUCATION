"""
Google Sheets Manager
Handles all Google Sheets operations and synchronization
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime, timezone, timedelta
from app import config
from app.database import db
import os
import json
import hashlib


class GoogleSheetsManager:
    """Manages Google Sheets operations"""

    def __init__(self):
        """Initialize Google Sheets API"""
        firebase_creds = os.getenv('FIREBASE_CREDENTIALS')

        if firebase_creds:
            cred_dict = json.loads(firebase_creds)
            self.credentials = service_account.Credentials.from_service_account_info(
                cred_dict,
                scopes=config.GOOGLE_SCOPES
            )
        else:
            self.credentials = service_account.Credentials.from_service_account_file(
                config.FIREBASE_KEY_PATH,
                scopes=config.GOOGLE_SCOPES
            )

        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.sheet_id = config.SHEET_ID
        self.sync_lock = asyncio.Lock()
        self.background_task = None
        self.auto_sync_enabled = True
        self.cache_ttl = timedelta(seconds=30)
        self._sheet_names_cache = None
        self._sheet_names_cached_at = None
        self._sheet_data_cache = {}
        self._sheet_data_cached_at = {}

    def configure_cache_policy(self, enabled: bool, interval_seconds: int):
        """Apply cache on/off and TTL from settings."""
        interval_seconds = max(config.MIN_SYNC_INTERVAL, min(int(interval_seconds), config.MAX_SYNC_INTERVAL))
        policy_changed = self.auto_sync_enabled != bool(enabled) or self.cache_ttl != timedelta(seconds=interval_seconds)
        self.auto_sync_enabled = bool(enabled)
        self.cache_ttl = timedelta(seconds=interval_seconds)
        if policy_changed:
            self._sheet_names_cached_at = None
            self._sheet_data_cached_at.clear()

    def load_cache_policy(self):
        """Load current cache policy from persistent settings."""
        settings = db.get_settings()
        self.configure_cache_policy(
            settings.get('sync_enabled', True),
            settings.get('sync_interval', config.DEFAULT_SYNC_INTERVAL)
        )

    def invalidate_cache(self, sheet_name: str = None):
        """Clear cached Sheets reads after writes or manual refresh."""
        if sheet_name:
            self._sheet_data_cache.pop(sheet_name, None)
            self._sheet_data_cached_at.pop(sheet_name, None)
        else:
            self._sheet_names_cache = None
            self._sheet_names_cached_at = None
            self._sheet_data_cache.clear()
            self._sheet_data_cached_at.clear()

    def _is_cache_fresh(self, cached_at) -> bool:
        return cached_at is not None and datetime.now(timezone.utc) - cached_at < self.cache_ttl

    def _manual_user_id(self, sheet_name: str, row_index: int) -> str:
        """Create a compact synthetic id for rows that do not have Telegram user ids."""
        sheet_hash = hashlib.md5(sheet_name.encode('utf-8')).hexdigest()[:8]
        return f"manual_{sheet_hash}_{row_index}"

    def _matches_identifier(self, user: Dict[str, Any], identifier: str, sheet_name: str, row_index: int) -> bool:
        actual_user_id = str(user.get('user_id', '') or '').strip()
        manual_user_id = self._manual_user_id(sheet_name, row_index)
        return identifier == actual_user_id or identifier == manual_user_id

    # ═══════════════════════════════════════════════════════════════════════════
    # SHEET/TAB MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def get_sheet_names(self, force_refresh: bool = False) -> List[str]:
        """Get all sheet names (tabs) from the spreadsheet."""
        self.load_cache_policy()
        if not force_refresh and self._sheet_names_cache is not None:
            if not self.auto_sync_enabled:
                return list(self._sheet_names_cache)
            if self._is_cache_fresh(self._sheet_names_cached_at):
                return list(self._sheet_names_cache)

        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
            sheets = spreadsheet.get('sheets', [])
            names = [
                sheet['properties']['title']
                for sheet in sheets
                if str(sheet['properties'].get('title', '')).strip() != '1'
            ]
            self._sheet_names_cache = list(names)
            self._sheet_names_cached_at = datetime.now(timezone.utc)
            return list(names)
        except HttpError as e:
            print(f"Error getting sheet names: {e}")
            if self._sheet_names_cache is not None:
                return list(self._sheet_names_cache)
            return []
        except Exception as e:
            print(f"Unexpected error getting sheet names: {e}")
            if self._sheet_names_cache is not None:
                return list(self._sheet_names_cache)
            return []

    def get_user(self, user_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Get a single user from all sheet tabs by user_id."""
        for sheet_name in self.get_sheet_names(force_refresh=force_refresh):
            try:
                for row in self.fetch_all_data(sheet_name=sheet_name, force_refresh=force_refresh):
                    if row.get('user_id') == user_id:
                        row['group_id'] = sheet_name
                        return row
            except Exception as e:
                print(f"Error reading user from {sheet_name}: {e}")
        return None

    def get_all_users(self, group_id: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get users from one sheet or all sheets."""
        users: List[Dict[str, Any]] = []
        sheet_names = [group_id] if group_id else self.get_sheet_names(force_refresh=force_refresh)
        for sheet_name in sheet_names:
            try:
                for row in self.fetch_all_data(sheet_name=sheet_name, force_refresh=force_refresh):
                    row['group_id'] = sheet_name
                    users.append(row)
            except Exception as e:
                print(f"Error reading users from {sheet_name}: {e}")
        return users

    def get_ranking(self, group_id: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Return students ordered by points from Sheets."""
        users = self.get_all_users(group_id=group_id, force_refresh=force_refresh)
        return sorted(users, key=lambda x: x.get('points', 0), reverse=True)

    def get_group(self, group_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Return group metadata from sheet tab name."""
        if not group_id:
            return None
        names = self.get_sheet_names(force_refresh=force_refresh)
        if group_id in names:
            try:
                count = len(self.fetch_all_data(sheet_name=group_id, force_refresh=force_refresh))
            except Exception:
                count = 0
            return {'group_id': group_id, 'name': group_id, 'sheet_name': group_id, 'student_count': count}
        return None

    def get_groups_from_sheets(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get all groups from Google Sheets tabs (auto-detect)

        This replaces Firebase groups - groups are now defined by sheet tabs only.
        Each sheet tab = one group.
        """
        try:
            sheet_names = self.get_sheet_names(force_refresh=force_refresh)
            groups = []

            for sheet_name in sheet_names:
                # Get student count for this sheet
                try:
                    data = self.fetch_all_data(sheet_name=sheet_name, force_refresh=force_refresh)
                    student_count = len(data)
                except:
                    student_count = 0

                groups.append({
                    'group_id': sheet_name,  # Sheet name is now the group ID
                    'name': sheet_name,      # Sheet name is the group name
                    'sheet_name': sheet_name,
                    'student_count': student_count
                })

            return groups
        except Exception as e:
            print(f"Error getting groups from sheets: {e}")
            return []

    def rename_sheet_tab(self, old_name: str, new_name: str) -> bool:
        """Rename a sheet tab in Google Sheets"""
        try:
            # Get spreadsheet metadata to find the sheet ID
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
            sheets = spreadsheet.get('sheets', [])

            # Find the sheet ID by name
            sheet_id = None
            for sheet in sheets:
                if sheet['properties']['title'] == old_name:
                    sheet_id = sheet['properties']['sheetId']
                    break

            if sheet_id is None:
                print(f"❌ Sheet tab '{old_name}' not found")
                return False

            # Rename the sheet
            requests = [{
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': sheet_id,
                        'title': new_name
                    },
                    'fields': 'title'
                }
            }]

            body = {'requests': requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body=body
            ).execute()

            self.invalidate_cache()
            print(f"✅ Renamed sheet tab: '{old_name}' → '{new_name}'")
            return True

        except HttpError as e:
            print(f"❌ Error renaming sheet tab: {e}")
            return False

    def delete_sheet_tab(self, sheet_name: str) -> bool:
        """Delete a sheet tab from Google Sheets."""
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
            sheets = spreadsheet.get('sheets', [])

            sheet_id = None
            for sheet in sheets:
                if sheet['properties']['title'] == sheet_name:
                    sheet_id = sheet['properties']['sheetId']
                    break

            if sheet_id is None:
                return False

            request = {
                'deleteSheet': {
                    'sheetId': sheet_id
                }
            }
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body={'requests': [request]}
            ).execute()
            self.invalidate_cache()
            return True
        except HttpError as e:
            print(f"Error deleting sheet tab: {e}")
            return False

    def create_sheet_tab(self, sheet_name: str) -> bool:
        """Create a new sheet tab with header row"""
        try:
            # Check if sheet already exists
            existing_sheets = self.get_sheet_names()
            if sheet_name in existing_sheets:
                print(f"Sheet '{sheet_name}' already exists")
                return True

            # Create new sheet
            request = {
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }

            body = {'requests': [request]}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body=body
            ).execute()

            self.invalidate_cache()
            # Add header row
            header_values = [['User ID', 'Full Name', 'Phone', 'Username', 'Points', 'Last Updated']]
            header_body = {'values': header_values}

            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=f'{sheet_name}!A1:F1',
                valueInputOption='RAW',
                body=header_body
            ).execute()

            self.invalidate_cache(sheet_name)
            print(f"✅ Created new sheet tab: {sheet_name}")
            return True

        except HttpError as e:
            print(f"Error creating sheet tab: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # READ OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def fetch_all_data(self, sheet_name: str = 'Sheet1', force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Fetch all data from Google Sheets (specific sheet/tab)."""
        self.load_cache_policy()
        if not force_refresh and sheet_name in self._sheet_data_cache:
            if not self.auto_sync_enabled:
                return [dict(row) for row in self._sheet_data_cache[sheet_name]]
            if self._is_cache_fresh(self._sheet_data_cached_at.get(sheet_name)):
                return [dict(row) for row in self._sheet_data_cache[sheet_name]]

        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f'{sheet_name}!A2:F'
            ).execute()

            rows = result.get('values', [])
            users = []

            for idx, row in enumerate(rows, start=2):
                if len(row) < 2:
                    continue

                try:
                    if not row[1] or not row[1].strip():
                        continue

                    points_value = 0
                    if len(row) > 4 and row[4] and row[4].strip():
                        try:
                            points_value = int(row[4])
                        except ValueError:
                            print(f"Warning: Invalid points value '{row[4]}' for user {row[0]}, defaulting to 0")
                            points_value = 0

                    actual_user_id = str(row[0]).strip() if len(row) > 0 and row[0] else ''
                    user_data = {
                        'user_id': actual_user_id or self._manual_user_id(sheet_name, idx),
                        'full_name': row[1].strip(),
                        'phone': row[2].strip() if len(row) > 2 and row[2] else '',
                        'username': row[3].strip() if len(row) > 3 and row[3] else '',
                        'points': points_value,
                        'last_updated': row[5].strip() if len(row) > 5 and row[5] else '',
                        'role': 'student',
                        'status': 'active',
                        'is_manual': not bool(actual_user_id),
                        'sheet_row_index': idx
                    }
                    users.append(user_data)
                except (ValueError, IndexError) as e:
                    print(f"Error parsing row: {row}, Error: {e}")
                    continue

            self._sheet_data_cache[sheet_name] = [dict(user) for user in users]
            self._sheet_data_cached_at[sheet_name] = datetime.now(timezone.utc)
            return users

        except HttpError as e:
            print(f"Google Sheets API error: {e}")
            return []

    def update_row(self, user_id: str, points: int, sheet_name: str = 'Sheet1') -> bool:
        """Update specific user's points in Sheets"""
        try:
            # Find the row for this user
            all_data = self.fetch_all_data(sheet_name=sheet_name)
            row_index = None

            for idx, user in enumerate(all_data, start=2):
                if self._matches_identifier(user, user_id, sheet_name, idx):
                    row_index = idx
                    break

            if row_index is None:
                print(f"User {user_id} not found in Sheets")
                return False

            # Update the points column (E) and last_updated (F)
            range_name = f'{sheet_name}!E{row_index}:F{row_index}'
            values = [[points, datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')]]

            body = {'values': values}

            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()

            self.invalidate_cache(sheet_name)
            return True

        except HttpError as e:
            print(f"Error updating Sheets: {e}")
            return False

    def update_user_row(self, user_id: str, user_data: Dict[str, Any], sheet_name: str = 'Sheet1') -> bool:
        """Replace a user's row in Sheets with merged user data."""
        try:
            if sheet_name not in self.get_sheet_names():
                if not self.create_sheet_tab(sheet_name):
                    return False

            all_data = self.fetch_all_data(sheet_name=sheet_name)
            row_index = None

            for idx, user in enumerate(all_data, start=2):
                if self._matches_identifier(user, user_id, sheet_name, idx):
                    row_index = idx
                    break

            if row_index is None:
                return False

            values = [[
                '' if user_data.get('is_manual') else user_data.get('user_id', user_id),
                user_data.get('full_name', ''),
                user_data.get('phone', ''),
                user_data.get('username', ''),
                user_data.get('points', 0),
                datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            ]]

            range_name = f'{sheet_name}!A{row_index}:F{row_index}'
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': values}
            ).execute()
            self.invalidate_cache(sheet_name)
            return True
        except HttpError as e:
            print(f"Error updating user row in Sheets: {e}")
            return False

    def add_user(self, user_data: Dict[str, Any], sheet_name: str = 'Sheet1') -> bool:
        """Add new user into the first row where both ID and Name cells are empty."""
        try:
            if sheet_name not in self.get_sheet_names():
                if not self.create_sheet_tab(sheet_name):
                    return False

            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f'{sheet_name}!A2:B'
            ).execute()

            rows = result.get('values', [])

            # Fill the first gap only when both ID and Name are empty.
            target_row = 2
            for idx, row in enumerate(rows):
                user_id_cell = str(row[0]).strip() if len(row) > 0 and row[0] else ''
                full_name_cell = str(row[1]).strip() if len(row) > 1 and row[1] else ''
                if not user_id_cell and not full_name_cell:
                    target_row = idx + 2
                    break
                target_row = idx + 3

            # Prepare data
            values = [[
                '' if user_data.get('is_manual') else user_data.get('user_id', ''),
                user_data.get('full_name', ''),
                user_data.get('phone', ''),
                user_data.get('username', ''),
                user_data.get('points', 0),
                datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            ]]

            body = {'values': values}

            # Insert at specific row
            range_name = f'{sheet_name}!A{target_row}:F{target_row}'
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()

            self.invalidate_cache(sheet_name)
            print(f"✅ Added user to {sheet_name} row {target_row}: {user_data.get('full_name', 'Unknown')}")
            return True

        except HttpError as e:
            print(f"Error adding user to Sheets: {e}")
            return False

    def delete_user(self, user_id: str) -> bool:
        """Delete user from Google Sheets"""
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
            sheets = spreadsheet.get('sheets', [])

            for sheet_name in self.get_sheet_names():
                all_data = self.fetch_all_data(sheet_name=sheet_name)
                row_index = None

                for idx, user in enumerate(all_data, start=2):
                    if self._matches_identifier(user, user_id, sheet_name, idx):
                        row_index = idx - 1  # convert to zero-based row index after header
                        break

                if row_index is None:
                    continue

                sheet_id = None
                for sheet in sheets:
                    if sheet['properties']['title'] == sheet_name:
                        sheet_id = sheet['properties']['sheetId']
                        break

                if sheet_id is None:
                    continue

                request = {
                    'deleteDimension': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'ROWS',
                            'startIndex': row_index,
                            'endIndex': row_index + 1
                        }
                    }
                }

                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.sheet_id,
                    body={'requests': [request]}
                ).execute()

                self.invalidate_cache(sheet_name)
                return True

            return False

        except HttpError as e:
            print(f"Error deleting from Sheets: {e}")
            return False

    def bulk_update(self, updates: List[Dict[str, Any]]) -> bool:
        """Bulk update multiple rows"""
        try:
            data = []
            for update in updates:
                row_index = update['row_index']
                values = [
                    update['user_id'],
                    update['full_name'],
                    update['phone'],
                    update['username'],
                    update['points'],
                    datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                ]

                data.append({
                    'range': f'Sheet1!A{row_index}:F{row_index}',
                    'values': [values]
                })

            body = {
                'valueInputOption': 'RAW',
                'data': data
            }

            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=self.sheet_id,
                body=body
            ).execute()

            self.invalidate_cache()
            return True

        except HttpError as e:
            print(f"Error bulk updating Sheets: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════════════════════════
    # SMART DELTA SYNC - DISABLED IN SHEETS-ONLY MODE
    # ═══════════════════════════════════════════════════════════════════════════

    async def smart_delta_sync(self) -> Dict[str, int]:
        """No-op in Sheets-only mode."""
        return {'added': 0, 'updated': 0, 'deleted': 0, 'moved': 0, 'synced': 0, 'recovered': 0}

    async def background_sync_loop(self):
        """Refresh sheet metadata and rows on a fixed interval."""
        try:
            while True:
                self.load_cache_policy()
                if not self.auto_sync_enabled:
                    await asyncio.sleep(1)
                    continue

                interval_seconds = max(
                    config.MIN_SYNC_INTERVAL,
                    min(int(self.cache_ttl.total_seconds()), config.MAX_SYNC_INTERVAL)
                )

                try:
                    async with self.sync_lock:
                        sheet_names = await asyncio.to_thread(self.get_sheet_names, True)
                        for sheet_name in sheet_names:
                            await asyncio.to_thread(self.fetch_all_data, sheet_name, True)
                except Exception as e:
                    print(f"Background cache sync error: {e}")

                await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            print("Background cache sync stopped")
            raise

    def start_background_sync(self):
        """Start periodic background cache refresh."""
        if self.background_task and not self.background_task.done():
            return False
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return False
        self.background_task = loop.create_task(self.background_sync_loop())
        return True

    def stop_background_sync(self):
        """Stop periodic background cache refresh."""
        if self.background_task and not self.background_task.done():
            self.background_task.cancel()
            return True
        return False

    def is_sync_running(self):
        """Return whether background cache refresh task is running."""
        return bool(self.background_task and not self.background_task.done())

# Global sheets manager instance
sheets_manager = GoogleSheetsManager()
