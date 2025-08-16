#!/usr/bin/env python3
"""
Team Orchestration Manager
High-level interface that integrates all chaos prevention mechanisms
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from logging_config import setup_logging
from multi_team_coordinator import get_coordinator, TeamStatus
from chaos_prevention import get_chaos_manager, chaos_protected
from context_manager import get_context_manager

logger = setup_logging(__name__)


@dataclass
class TeamOrchestrationConfig:
    """Configuration for team orchestration"""
    max_teams: int = 5
    heartbeat_interval: int = 30
    context_sync_interval: int = 60
    cleanup_interval: int = 300
    enable_auto_isolation: bool = True
    enable_resource_limits: bool = True


class TeamOrchestrationManager:
    """
    High-level manager that coordinates multiple AI teams safely
    Prevents chaos through systematic resource management and monitoring
    """
    
    def __init__(self, config: Optional[TeamOrchestrationConfig] = None):
        self.config = config or TeamOrchestrationConfig()
        self.coordinator = get_coordinator()
        self.chaos_manager = get_chaos_manager()
        self.context_manager = get_context_manager()
        
        # Start coordination services
        self.coordinator.start_coordination_services()
        logger.info("Team orchestration manager initialized")
    
    @chaos_protected("team_creation")
    def create_team(self, team_name: str, agents: List[str], 
                   session_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new AI team with full chaos protection
        
        Returns:
            Dict with team_id, session_name, and status
        """
        try:
            # Check team limits
            if len(self.coordinator.teams) >= self.config.max_teams:
                raise Exception(f"Maximum teams ({self.config.max_teams}) reached")
            
            # Generate session name if not provided
            if not session_name:
                session_name = f"ai-team-{team_name}-{int(time.time())}"
            
            team_id = f"team_{team_name}_{int(time.time())}"
            
            # Register team with coordinator
            success = self.coordinator.register_team(team_id, session_name, agents)
            if not success:
                raise Exception("Failed to register team with coordinator")
            
            # Create tmux session with protection
            from create_ai_team import AITeamOrchestrator
            orchestrator = AITeamOrchestrator(non_interactive=True)
            orchestrator.session_name = session_name
            
            # Protected tmux operations
            creation_success = self._protected_tmux_creation(orchestrator)
            if not creation_success:
                # Cleanup on failure
                self.coordinator.unregister_team(team_id, cleanup=True)
                raise Exception("Failed to create tmux session")
            
            logger.info(f"Successfully created team {team_id} with session {session_name}")
            
            return {
                "team_id": team_id,
                "session_name": session_name,
                "agents": agents,
                "status": "created",
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Team creation failed: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    @chaos_protected("team_destruction")
    def destroy_team(self, team_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Safely destroy a team and cleanup all resources
        """
        try:
            if team_id not in self.coordinator.teams:
                raise Exception(f"Team {team_id} not found")
            
            team_info = self.coordinator.teams[team_id]
            
            # Graceful shutdown unless forced
            if not force:
                # Send shutdown message to team
                self.coordinator.send_inter_team_message(
                    "system", team_id, "shutdown_request", 
                    {"reason": "Team destruction requested"}
                )
                
                # Wait for graceful shutdown
                time.sleep(5)
            
            # Destroy tmux session
            session_name = team_info.session_name
            self._protected_tmux_destruction(session_name)
            
            # Unregister from coordinator
            self.coordinator.unregister_team(team_id, cleanup=True)
            
            logger.info(f"Successfully destroyed team {team_id}")
            
            return {
                "team_id": team_id,
                "status": "destroyed",
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Team destruction failed: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def get_team_status(self, team_id: str) -> Dict[str, Any]:
        """Get comprehensive status for a team"""
        try:
            if team_id not in self.coordinator.teams:
                return {"error": "Team not found"}
            
            team_info = self.coordinator.teams[team_id]
            
            # Get health status
            health = self.coordinator.get_system_health()
            team_health = health["teams"].get(team_id, {})
            
            # Get context status
            context_status = self.context_manager.check_health()
            
            # Get chaos protection status
            chaos_status = self.chaos_manager.get_system_status()
            
            return {
                "team_id": team_id,
                "session_name": team_info.session_name,
                "status": team_info.status.value,
                "agents": team_info.agents,
                "resources": list(team_info.resources),
                "error_count": team_info.error_count,
                "health": team_health,
                "context_health": context_status["healthy"],
                "protection_status": {
                    "circuit_breakers": len(chaos_status["circuit_breakers"]),
                    "active_bulkheads": sum(
                        b["active_operations"] 
                        for b in chaos_status["bulkheads"].values()
                    )
                },
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to get team status: {e}")
            return {"error": str(e)}
    
    def list_teams(self) -> Dict[str, Any]:
        """List all teams with their current status"""
        try:
            teams = {}
            for team_id in self.coordinator.teams:
                teams[team_id] = self.get_team_status(team_id)
            
            return {
                "teams": teams,
                "total_count": len(teams),
                "system_health": self.coordinator.get_system_health(),
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to list teams: {e}")
            return {"error": str(e)}
    
    @chaos_protected("context_sync")
    def synchronize_team_context(self, team_id: str, context_data: Dict) -> Dict[str, Any]:
        """Synchronize context for a team across the system"""
        try:
            if team_id not in self.coordinator.teams:
                raise Exception(f"Team {team_id} not found")
            
            # Sync with coordinator
            sync_result = self.coordinator.synchronize_context(team_id, context_data)
            
            # Update context manager
            self.context_manager.dump_context(
                f"team_{team_id}", 0, 
                json.dumps(context_data), 
                {"sync_type": "inter_team"}
            )
            
            return {
                "team_id": team_id,
                "sync_result": sync_result,
                "status": "synchronized",
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Context sync failed for team {team_id}: {e}")
            return {"error": str(e)}
    
    def send_team_message(self, from_team: str, to_team: str, 
                         message_type: str, payload: Dict) -> Dict[str, Any]:
        """Send message between teams with chaos protection"""
        try:
            # Rate limiting check
            if not self.chaos_manager.rate_limiters["team_messages"].allow_request():
                raise Exception("Team message rate limit exceeded")
            
            message_id = self.coordinator.send_inter_team_message(
                from_team, to_team, message_type, payload, requires_ack=True
            )
            
            if not message_id:
                raise Exception("Failed to send message")
            
            return {
                "message_id": message_id,
                "from_team": from_team,
                "to_team": to_team,
                "status": "sent",
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to send team message: {e}")
            return {"error": str(e)}
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview"""
        try:
            coordinator_health = self.coordinator.get_system_health()
            chaos_status = self.chaos_manager.get_system_status()
            context_health = self.context_manager.check_health()
            
            return {
                "timestamp": time.time(),
                "total_teams": coordinator_health["total_teams"],
                "team_health": {
                    "healthy": coordinator_health["healthy_teams"],
                    "degraded": coordinator_health["degraded_teams"],
                    "failing": coordinator_health["failing_teams"],
                    "isolated": coordinator_health["isolated_teams"]
                },
                "resource_usage": {
                    "conflicts": coordinator_health["resource_conflicts"],
                    "active_reservations": len(self.coordinator.resources)
                },
                "chaos_protection": {
                    "circuit_breakers": len(chaos_status["circuit_breakers"]),
                    "open_circuits": sum(
                        1 for cb in chaos_status["circuit_breakers"].values()
                        if cb["state"] == "open"
                    ),
                    "bulkhead_utilization": {
                        name: f"{bh['active_operations']}/{bh['max_concurrent']}"
                        for name, bh in chaos_status["bulkheads"].items()
                    }
                },
                "context_system": {
                    "healthy": context_health["healthy"],
                    "issues": context_health.get("issues", [])
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system overview: {e}")
            return {"error": str(e)}
    
    def emergency_shutdown(self, reason: str = "Emergency shutdown") -> Dict[str, Any]:
        """Emergency shutdown of all teams"""
        logger.warning(f"Emergency shutdown initiated: {reason}")
        
        shutdown_results = {}
        team_ids = list(self.coordinator.teams.keys())
        
        for team_id in team_ids:
            try:
                result = self.destroy_team(team_id, force=True)
                shutdown_results[team_id] = result
            except Exception as e:
                shutdown_results[team_id] = {"error": str(e)}
        
        # Stop coordination services
        self.coordinator.stop_coordination_services()
        self.chaos_manager.stop_monitoring()
        
        return {
            "shutdown_reason": reason,
            "teams_shutdown": shutdown_results,
            "timestamp": time.time()
        }
    
    # Protected tmux operations
    
    def _protected_tmux_creation(self, orchestrator) -> bool:
        """Create tmux session with bulkhead protection"""
        try:
            return self.chaos_manager.bulkheads["tmux_operations"].execute(
                orchestrator.create_team
            )
        except Exception as e:
            logger.error(f"Protected tmux creation failed: {e}")
            return False
    
    def _protected_tmux_destruction(self, session_name: str) -> bool:
        """Destroy tmux session with protection"""
        def destroy_session():
            import subprocess
            try:
                subprocess.run([
                    "tmux", "kill-session", "-t", session_name
                ], check=True, timeout=10)
                return True
            except subprocess.CalledProcessError as e:
                if "session not found" in str(e):
                    return True  # Already gone
                raise
        
        try:
            return self.chaos_manager.bulkheads["tmux_operations"].execute(destroy_session)
        except Exception as e:
            logger.error(f"Protected tmux destruction failed: {e}")
            return False


# Singleton manager
_orchestration_manager: Optional[TeamOrchestrationManager] = None

def get_orchestration_manager() -> TeamOrchestrationManager:
    """Get the global team orchestration manager"""
    global _orchestration_manager
    if _orchestration_manager is None:
        _orchestration_manager = TeamOrchestrationManager()
    return _orchestration_manager


if __name__ == "__main__":
    # Demo the orchestration system
    manager = get_orchestration_manager()
    
    print("🚀 Multi-Team Orchestration Demo")
    print("=" * 50)
    
    # Create a test team
    result = manager.create_team("demo", ["alex", "morgan", "sam"])
    print(f"Team creation: {result}")
    
    if "team_id" in result:
        team_id = result["team_id"]
        
        # Check status
        status = manager.get_team_status(team_id)
        print(f"Team status: {status}")
        
        # Get system overview
        overview = manager.get_system_overview()
        print(f"System overview: {json.dumps(overview, indent=2)}")
        
        # Cleanup
        destroy_result = manager.destroy_team(team_id)
        print(f"Team destruction: {destroy_result}")
    
    print("\n✅ Demo complete!")