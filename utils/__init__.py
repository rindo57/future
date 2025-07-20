from .admin_handlers import register_admin_handlers
from .callback_handlers import register_callback_handlers
from .command_handlers import register_command_handlers
from .message_handlers import register_message_handlers

def register_handlers(app):
    register_admin_handlers(app)
    register_callback_handlers(app)
    register_command_handlers(app)
    register_message_handlers(app)
