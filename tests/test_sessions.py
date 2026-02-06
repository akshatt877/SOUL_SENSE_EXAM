"""
Session Management Tests
------------------------
Tests for the session tracking functionality with unique session IDs.

Tests cover:
- Session ID generation on login
- Session storage in database
- Session validation
- Session invalidation on logout
- Session cleanup
- Multiple concurrent sessions
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta, UTC

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.auth import AuthManager
from app.models import User, Session
from app.db import get_session


class TestSessionManagement:
    """Test suite for session management"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.auth_manager = AuthManager()
    
    def test_session_id_generation_on_login(self, temp_db):
        """Test that a unique session ID is generated on successful login"""
        # Register a test user
        success, msg = self.auth_manager.register_user("sessionuser", "password123")
        assert success, "User registration should succeed"
        
        # Login the user
        success, msg = self.auth_manager.login_user("sessionuser", "password123")
        assert success, "Login should succeed"
        
        # Check that a session ID was created
        assert self.auth_manager.current_session_id is not None, "Session ID should be generated"
        assert len(self.auth_manager.current_session_id) > 0, "Session ID should not be empty"
        
        # Verify session ID is in database
        session = get_session()
        try:
            db_session = session.query(Session).filter_by(
                session_id=self.auth_manager.current_session_id
            ).first()
            
            assert db_session is not None, "Session should exist in database"
            assert db_session.username == "sessionuser", "Session should be associated with correct user"
            assert db_session.is_active == True, "Session should be active"
        finally:
            session.close()
    
    def test_unique_session_ids_for_multiple_logins(self, temp_db):
        """Test that each login generates a unique session ID"""
        # Register a user
        self.auth_manager.register_user("multiuser", "password123")
        
        session_ids = []
        
        # Login multiple times
        for i in range(3):
            auth = AuthManager()  # New instance for each login
            success, msg = auth.login_user("multiuser", "password123")
            assert success, f"Login {i+1} should succeed"
            
            session_ids.append(auth.current_session_id)
        
        # Verify all session IDs are unique
        assert len(session_ids) == len(set(session_ids)), "All session IDs should be unique"
    
    def test_session_data_stored_correctly(self, temp_db):
        """Test that session data is stored with user and timestamp"""
        # Register and login
        self.auth_manager.register_user("datauser", "password123")
        success, msg = self.auth_manager.login_user("datauser", "password123")
        assert success
        
        # Get session from database
        session = get_session()
        try:
            db_session = session.query(Session).filter_by(
                session_id=self.auth_manager.current_session_id
            ).first()
            
            # Verify all required data is present
            assert db_session.session_id is not None, "Session ID should be stored"
            assert db_session.user_id is not None, "User ID should be stored"
            assert db_session.username == "datauser", "Username should be stored"
            assert db_session.created_at is not None, "Created timestamp should be stored"
            assert db_session.last_accessed is not None, "Last accessed timestamp should be stored"
            assert db_session.is_active == True, "Session should be active"
            
            # Verify timestamp format
            created_at = datetime.fromisoformat(db_session.created_at)
            assert created_at <= datetime.now(UTC), "Created timestamp should not be in future"
        finally:
            session.close()
    
    def test_session_invalidation_on_logout(self, temp_db):
        """Test that session is invalidated when user logs out"""
        # Register and login
        self.auth_manager.register_user("logoutuser", "password123")
        self.auth_manager.login_user("logoutuser", "password123")
        
        session_id = self.auth_manager.current_session_id
        assert session_id is not None, "Session should exist after login"
        
        # Logout
        success, msg = self.auth_manager.logout_user()
        assert success, "Logout should succeed"
        
        # Verify session is cleared from auth manager
        assert self.auth_manager.current_session_id is None, "Session ID should be cleared"
        assert self.auth_manager.current_user is None, "Current user should be cleared"
        
        # Verify session is invalidated in database
        session = get_session()
        try:
            db_session = session.query(Session).filter_by(session_id=session_id).first()
            
            assert db_session is not None, "Session record should still exist"
            assert db_session.is_active == False, "Session should be marked as inactive"
            assert db_session.logged_out_at is not None, "Logout timestamp should be recorded"
        finally:
            session.close()
    
    def test_no_duplicate_active_sessions_for_same_user(self, temp_db):
        """Test that multiple active sessions can exist for same user"""
        # Register a user
        self.auth_manager.register_user("concurrent", "password123")
        
        # Create multiple sessions
        auth1 = AuthManager()
        auth2 = AuthManager()
        
        auth1.login_user("concurrent", "password123")
        auth2.login_user("concurrent", "password123")
        
        # Both should have different session IDs
        assert auth1.current_session_id != auth2.current_session_id
        
        # Both sessions should be active in database
        session = get_session()
        try:
            active_sessions = session.query(Session).filter_by(
                username="concurrent",
                is_active=True
            ).all()
            
            assert len(active_sessions) == 2, "Both sessions should be active"
        finally:
            session.close()
    
    def test_session_validation(self, temp_db):
        """Test session validation functionality"""
        # Register and login
        self.auth_manager.register_user("validateuser", "password123")
        self.auth_manager.login_user("validateuser", "password123")
        
        session_id = self.auth_manager.current_session_id
        
        # Validate active session
        is_valid, username = self.auth_manager.validate_session(session_id)
        assert is_valid == True, "Active session should be valid"
        assert username == "validateuser", "Should return correct username"
        
        # Logout and validate again
        self.auth_manager.logout_user()
        is_valid, username = self.auth_manager.validate_session(session_id)
        assert is_valid == False, "Logged out session should be invalid"
        assert username is None, "Invalid session should return None"
    
    def test_session_cleanup_old_sessions(self, temp_db):
        """Test cleanup of old sessions"""
        # Register and login
        self.auth_manager.register_user("cleanupuser", "password123")
        self.auth_manager.login_user("cleanupuser", "password123")
        
        session_id = self.auth_manager.current_session_id
        
        # Manually set session to be 25 hours old
        session = get_session()
        try:
            db_session = session.query(Session).filter_by(session_id=session_id).first()
            old_time = datetime.now(UTC) - timedelta(hours=25)
            db_session.created_at = old_time.isoformat()
            session.commit()
        finally:
            session.close()
        
        # Run cleanup (default 24 hours)
        count = self.auth_manager.cleanup_old_sessions()
        assert count >= 1, "Should cleanup at least one old session"
        
        # Verify session is now inactive
        session = get_session()
        try:
            db_session = session.query(Session).filter_by(session_id=session_id).first()
            assert db_session.is_active == False, "Old session should be inactive"
        finally:
            session.close()
    
    def test_get_active_sessions(self, temp_db):
        """Test retrieving active sessions"""
        # Register and create multiple sessions
        self.auth_manager.register_user("activeuser", "password123")
        
        auth1 = AuthManager()
        auth2 = AuthManager()
        auth3 = AuthManager()
        
        auth1.login_user("activeuser", "password123")
        auth2.login_user("activeuser", "password123")
        auth3.login_user("activeuser", "password123")
        
        # Get active sessions
        active = self.auth_manager.get_active_sessions("activeuser")
        assert len(active) == 3, "Should have 3 active sessions"
        
        # Logout one
        auth2.logout_user()
        
        # Check again
        active = self.auth_manager.get_active_sessions("activeuser")
        assert len(active) == 2, "Should have 2 active sessions after logout"
    
    def test_invalidate_all_user_sessions(self, temp_db):
        """Test invalidating all sessions for a user"""
        # Register and create multiple sessions
        self.auth_manager.register_user("bulkuser", "password123")
        
        auth1 = AuthManager()
        auth2 = AuthManager()
        auth3 = AuthManager()
        
        auth1.login_user("bulkuser", "password123")
        auth2.login_user("bulkuser", "password123")
        auth3.login_user("bulkuser", "password123")
        
        # Invalidate all sessions
        count = self.auth_manager.invalidate_user_sessions("bulkuser")
        assert count == 3, "Should invalidate all 3 sessions"
        
        # Verify no active sessions remain
        active = self.auth_manager.get_active_sessions("bulkuser")
        assert len(active) == 0, "Should have no active sessions"
    
    def test_session_last_accessed_update(self, temp_db):
        """Test that last_accessed is updated on validation"""
        # Register and login
        self.auth_manager.register_user("accessuser", "password123")
        self.auth_manager.login_user("accessuser", "password123")
        
        session_id = self.auth_manager.current_session_id
        
        # Get initial last_accessed
        session = get_session()
        try:
            db_session = session.query(Session).filter_by(session_id=session_id).first()
            initial_access = db_session.last_accessed
        finally:
            session.close()
        
        # Wait a bit and validate
        import time
        time.sleep(1)
        self.auth_manager.validate_session(session_id)
        
        # Check last_accessed was updated
        session = get_session()
        try:
            db_session = session.query(Session).filter_by(session_id=session_id).first()
            updated_access = db_session.last_accessed
            assert updated_access > initial_access, "Last accessed should be updated"
        finally:
            session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
