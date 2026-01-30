
import logging
from datetime import datetime
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import Base and JournalEntry to setup the DB schema
from app.models import Base, JournalEntry
# Import app.db to patch get_session
import app.db

logging.basicConfig(level=logging.INFO)

# Setup isolated in-memory database for this test file
# This prevents locking the main soul_sense.db file during CI/tests
engine = create_engine("sqlite:///:memory:", echo=False)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine)

@patch('app.db.get_session')
def test_journal_insert(mock_get_session):
    """
    Test journal insertion using a mocked in-memory database.
    This avoids the 'database is locked' errors and hangs in CI.
    """
    print("Testing Journal Entry Insertion (In-Memory)...")
    
    # Create a fresh session for this test
    session = TestingSession()
    # Configure the mock to return this session
    mock_get_session.return_value = session
    
    try:
        # 1. Insert Entry
        entry = JournalEntry(
            username="test_user",
            entry_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            content="This is a test entry from the debug script.",
            sentiment_score=50.0,
            emotional_patterns="Test pattern"
        )
        session.add(entry)
        session.commit()
        print("✅ Successfully inserted journal entry.")
        
        # 2. Verify Inclusion
        saved_entry = session.query(JournalEntry).filter_by(username="test_user").order_by(JournalEntry.id.desc()).first()
        
        if saved_entry is None:
            raise AssertionError("Saved entry not found in database!")
            
        assert saved_entry.content == "This is a test entry from the debug script."
        assert saved_entry.username == "test_user"
        print(f"✅ Verified read back: {saved_entry.content}")
        
    except Exception as e:
        print(f"❌ Failed to insert journal entry: {e}")
        session.rollback()
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    test_journal_insert()
