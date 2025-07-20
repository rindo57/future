import pymongo
from datetime import datetime, timedelta
import string
import secrets
from typing import Optional, Dict, List, Tuple

# Database Connection
class Database:
    def __init__(self, connection_string: str, db_name: str = "tokyo"):
        """Initialize MongoDB connection and collections"""
        self.client = pymongo.MongoClient(connection_string)
        self.db = self.client[db_name]
        
        # Collections
        self.anicomments = self.db['anicomments']
        self.epcomments = self.db['epcomments']
        self.users = self.db['users']
        self.used_tokens = self.db['used_tokens']
        self.verification_tokens = self.db['verification_tokens']

# Initialize database connection
db = Database("mongodb+srv://anidl:encodes@cluster0.oobfx33.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# ======================
#  TOKEN SYSTEM
# ======================
class TokenManager:
    @staticmethod
    def generate_verification_token(length: int = 16) -> str:
        """Generate a random alphanumeric verification token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def add_verification_token(user_id: int) -> Tuple[str, bool, bool]:
        """
        Add or retrieve an existing verification token for a user
        Returns: (token, ouo_status, nano_status)
        """
        # Check for existing valid token
        user_token = db.verification_tokens.find_one({
            'user_id': user_id,
            'used': False,
            'created_at': {'$gte': datetime.utcnow() - timedelta(hours=24)}
        })
        
        if user_token:
            return user_token['token'], user_token.get('ouo', False), user_token.get('nano', False)
        
        # Create new token
        token = TokenManager.generate_verification_token()
        db.verification_tokens.insert_one({
            'user_id': user_id,
            'token': token,
            'created_at': datetime.utcnow(),
            'used': False
        })
        return token, False, False

    @staticmethod
    def add_short_url(user_id: int, token: str, ouo: str, nano: str) -> None:
        """Update token with short URL information"""
        db.verification_tokens.update_one(
            {
                "user_id": user_id,
                "token": token,
                'created_at': {'$gte': datetime.utcnow() - timedelta(hours=24)}
            },
            {"$set": {"ouo": ouo, "nano": nano}},
            upsert=True,
        )

    @staticmethod
    def is_valid_verification_token(user_id: int, token: str) -> bool:
        """Check if token exists, is unused, and not expired"""
        return bool(db.verification_tokens.find_one({
            'user_id': user_id,
            'token': token,
            'used': False,
            'created_at': {'$gte': datetime.utcnow() - timedelta(hours=24)}
        }))

    @staticmethod
    def mark_token_used(token: str) -> None:
        """Mark a token as used with timestamp"""
        db.verification_tokens.update_one(
            {'token': token},
            {'$set': {'used': True, 'used_at': datetime.utcnow()}}
        )

    @staticmethod
    def cleanup_expired_tokens() -> None:
        """Remove tokens older than 1 hour"""
        db.verification_tokens.delete_many({
            'created_at': {'$lt': datetime.utcnow() - timedelta(hours=1)}
        })

    @staticmethod
    async def add_used_token(token: str, user_id: int) -> None:
        """Record a used token"""
        db.used_tokens.insert_one({
            'token': token,
            'user_id': user_id,
            'used_at': datetime.utcnow()
        })

    @staticmethod
    async def is_token_used(token: str) -> bool:
        """Check if token has been used"""
        return bool(db.used_tokens.find_one({'token': token}))

# ======================
#  COMMENT SYSTEM
# ======================
class CommentManager:
    @staticmethod
    def save_anicomment(msg_id: int, title: str) -> None:
        """Save anime comment metadata"""
        db.anicomments.insert_one({
            'msg_id': msg_id,
            'title': title,
            'created_at': datetime.utcnow()
        })

    @staticmethod
    def get_anicomment(title: str) -> Optional[int]:
        """Retrieve anime comment message ID"""
        comment = db.anicomments.find_one({'title': title})
        return comment['msg_id'] if comment else None

    @staticmethod
    def save_epcomment(msg_id: int, title: str) -> None:
        """Save episode comment metadata"""
        db.epcomments.insert_one({
            'msg_id': msg_id,
            'title': title,
            'created_at': datetime.utcnow()
        })

    @staticmethod
    def get_epcomment(title: str) -> Optional[int]:
        """Retrieve episode comment message ID"""
        comment = db.epcomments.find_one({'title': title})
        return comment['msg_id'] if comment else None

# ======================
#  USER MANAGEMENT
# ======================
class UserManager:
    @staticmethod
    async def user_exists(user_id: int) -> bool:
        """Check if user exists in database"""
        return bool(db.users.find_one({'_id': user_id}))

    @staticmethod
    async def add_user(user_id: int, username: str) -> None:
        """Add new user with default values"""
        db.users.insert_one({
            '_id': user_id,
            'username': username,
            'search_count': 0,
            'last_reset': datetime.utcnow(),
            'verified': False,
            'banned': False,
            'created_at': datetime.utcnow()
        })

    @staticmethod
    async def get_all_user_ids() -> List[int]:
        """Get list of all user IDs"""
        return [doc['_id'] for doc in db.users.find()]

    @staticmethod
    async def delete_user(user_id: int) -> None:
        """Remove user from database"""
        db.users.delete_one({'_id': user_id})

    @staticmethod
    async def get_user(user_id: int) -> Optional[Dict]:
        """Get complete user document"""
        return db.users.find_one({'_id': user_id})

    @staticmethod
    async def update_search_count(user_id: int, count: int, last_reset: datetime = None) -> None:
        """Update user's search count and optional reset time"""
        update_data = {'$set': {'search_count': count}}
        
        if last_reset:
            update_data['$set']['last_reset'] = last_reset
        
        db.users.update_one(
            {'_id': user_id},
            update_data,
            upsert=True
        )

    @staticmethod
    async def mark_verified(user_id: int) -> None:
        """Mark user as verified"""
        db.users.update_one(
            {'_id': user_id},
            {'$set': {'verified': True}},
            upsert=True
        )

# ======================
#  BAN SYSTEM
# ======================
class BanManager:
    @staticmethod
    async def ban_user(user_id: int) -> None:
        """Ban a user (creates record if doesn't exist)"""
        db.users.update_one(
            {'_id': user_id},
            {'$set': {'banned': True}},
            upsert=True
        )

    @staticmethod
    async def unban_user(user_id: int) -> None:
        """Unban a user"""
        db.users.update_one(
            {'_id': user_id},
            {'$set': {'banned': False}},
            upsert=True
        )

    @staticmethod
    async def is_banned(user_id: int) -> bool:
        """Check if user is banned"""
        user = await UserManager.get_user(user_id)
        return user.get('banned', False) if user else False

# ======================
#  LEGACY FUNCTIONS (for backward compatibility)
# ======================
# These wrap the new class methods for easy migration

async def present_user(user_id: int) -> bool:
    return await UserManager.user_exists(user_id)

async def add_user(user_id: int, username: str) -> None:
    await UserManager.add_user(user_id, username)

async def full_userbase() -> List[int]:
    return await UserManager.get_all_user_ids()

async def del_user(user_id: int) -> None:
    await UserManager.delete_user(user_id)

async def get_user_data(user_id: int) -> Optional[Dict]:
    return await UserManager.get_user(user_id)

async def update_user_search_count(user_id: int, count: int, last_reset=None) -> None:
    await UserManager.update_search_count(user_id, count, last_reset)

def mark_user_verified(user_id: int) -> None:
    UserManager.mark_verified(user_id)

async def ban_user(user_id: int) -> None:
    await BanManager.ban_user(user_id)

async def unban_user(user_id: int) -> None:
    await BanManager.unban_user(user_id)

async def is_banned(user_id: int) -> bool:
    return await BanManager.is_banned(user_id)

def save_anicomments(msg_id: int, title: str) -> None:
    CommentManager.save_anicomment(msg_id, title)

def get_anicomments(title: str) -> Optional[int]:
    return CommentManager.get_anicomment(title)

def save_epcomments(msg_id: int, title: str) -> None:
    CommentManager.save_epcomment(msg_id, title)

def get_epcomments(title: str) -> Optional[int]:
    return CommentManager.get_epcomment(title)
