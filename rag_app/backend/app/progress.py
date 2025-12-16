import asyncio
import json
from typing import Dict, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ProgressTracker:
    def __init__(self):
        self.progress_data: Dict[str, List[Dict]] = {}
        self.active_sessions: Dict[str, bool] = {}
    
    def start_session(self, session_id: str):
        """Start a new progress tracking session"""
        self.progress_data[session_id] = []
        self.active_sessions[session_id] = True
        logger.info(f"Started progress session: {session_id}")
    
    def add_step(self, session_id: str, step: str, status: str = "info", details: str = ""):
        """Add a progress step to the session"""
        if session_id not in self.progress_data:
            self.start_session(session_id)
        
        step_data = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "status": status,  # info, success, error, warning
            "details": details
        }
        
        self.progress_data[session_id].append(step_data)
        logger.info(f"Progress [{session_id}]: {step} - {status}")
    
    def get_progress(self, session_id: str) -> List[Dict]:
        """Get all progress steps for a session"""
        return self.progress_data.get(session_id, [])
    
    def end_session(self, session_id: str):
        """End a progress tracking session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id] = False
        logger.info(f"Ended progress session: {session_id}")
    
    def cleanup_old_sessions(self, max_sessions: int = 100):
        """Clean up old sessions to prevent memory leaks"""
        if len(self.progress_data) > max_sessions:
            # Keep only the most recent sessions
            sessions = list(self.progress_data.keys())
            for session_id in sessions[:-max_sessions]:
                del self.progress_data[session_id]
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]

# Global progress tracker instance
progress_tracker = ProgressTracker()