"""
FSM States for the bot
"""

from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """States for user registration"""
    waiting_for_name = State()
    waiting_for_teacher_code = State()
    waiting_for_contact = State()


class AddPointsStates(StatesGroup):
    """States for adding points"""
    waiting_for_amount = State()
    waiting_for_reason = State()


class SubtractPointsStates(StatesGroup):
    """States for subtracting points"""
    waiting_for_amount = State()
    waiting_for_reason = State()


class TransferStates(StatesGroup):
    """States for points transfer"""
    waiting_for_recipient = State()
    waiting_for_amount = State()


class SettingsStates(StatesGroup):
    """States for settings modification"""
    waiting_for_commission = State()
    waiting_for_rules = State()
    waiting_for_broadcast = State()


class EditRulesStates(StatesGroup):
    """States for editing bot rules"""
    waiting_for_rules = State()


class BroadcastStates(StatesGroup):
    """States for broadcast messages"""
    waiting_for_message = State()


class ExportStates(StatesGroup):
    """States for data export"""
    processing = State()
