import random
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        self.sessions = {}
    
    def create_session(self, thread_id: str):
        """Create a new session with initial state"""
        otp = random.randint(100000, 999999)
        self.sessions[thread_id] = {
            "otp": otp,
            "verification_started": False,
            "is_verified": False,
            "session_active": True,
            "user_email": None
        }
        logger.info(f"Created new session {thread_id} with OTP {otp}")
        return self.sessions[thread_id]
    
    def get_session(self, thread_id: str):
        """Get session by thread_id"""
        return self.sessions.get(thread_id)
    
    def update_session(self, thread_id: str, updates: dict):
        """Update session state"""
        if thread_id in self.sessions:
            self.sessions[thread_id].update(updates)
            logger.info(f"Updated session {thread_id}: {updates}")
    
    def terminate_session(self, thread_id: str):
        """Terminate a session"""
        if thread_id in self.sessions:
            self.sessions[thread_id]["session_active"] = False
            logger.info(f"Terminated session {thread_id}")
    
    def cleanup_session(self, thread_id: str):
        """Remove session from memory"""
        if thread_id in self.sessions:
            del self.sessions[thread_id]
            logger.info(f"Cleaned up session {thread_id}")