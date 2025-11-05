"""
Load Test Scenarios

Predefined load test scenarios for different use cases.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class LoadTestScenario:
    """Load test scenario configuration."""
    
    name: str
    description: str
    users: int
    spawn_rate: int
    duration_minutes: int
    user_class: str = "ResourceAgentUser"
    
    def to_locust_args(self) -> List[str]:
        """Convert to Locust command line arguments."""
        return [
            "--headless",
            f"--users={self.users}",
            f"--spawn-rate={self.spawn_rate}",
            f"--run-time={self.duration_minutes}m",
        ]
    
    def __str__(self) -> str:
        return (
            f"{self.name}:\n"
            f"  Users: {self.users}\n"
            f"  Spawn Rate: {self.spawn_rate}/sec\n"
            f"  Duration: {self.duration_minutes} min\n"
            f"  Description: {self.description}"
        )


# Predefined scenarios
SCENARIOS = {
    "smoke": LoadTestScenario(
        name="Smoke Test",
        description="Quick validation that endpoints are working",
        users=1,
        spawn_rate=1,
        duration_minutes=1
    ),
    
    "light": LoadTestScenario(
        name="Light Load",
        description="Typical monitoring load",
        users=10,
        spawn_rate=2,
        duration_minutes=5,
        user_class="LightLoadUser"
    ),
    
    "medium": LoadTestScenario(
        name="Medium Load",
        description="Normal production load",
        users=50,
        spawn_rate=5,
        duration_minutes=5
    ),
    
    "heavy": LoadTestScenario(
        name="Heavy Load",
        description="Peak production load",
        users=100,
        spawn_rate=10,
        duration_minutes=3,
        user_class="HeavyLoadUser"
    ),
    
    "stress": LoadTestScenario(
        name="Stress Test",
        description="Find breaking point",
        users=200,
        spawn_rate=20,
        duration_minutes=2
    ),
    
    "spike": LoadTestScenario(
        name="Spike Test",
        description="Sudden traffic spike",
        users=150,
        spawn_rate=50,
        duration_minutes=2
    ),
    
    "endurance": LoadTestScenario(
        name="Endurance Test",
        description="Long-running stability test",
        users=30,
        spawn_rate=3,
        duration_minutes=30
    ),
    
    "baseline": LoadTestScenario(
        name="Baseline",
        description="Establish performance baseline",
        users=20,
        spawn_rate=2,
        duration_minutes=10
    ),
}


def get_scenario(name: str) -> LoadTestScenario:
    """
    Get a predefined scenario by name.
    
    Args:
        name: Scenario name
        
    Returns:
        LoadTestScenario
        
    Raises:
        KeyError: If scenario not found
    """
    return SCENARIOS[name]


def list_scenarios() -> None:
    """Print all available scenarios."""
    print("Available Load Test Scenarios:")
    print("=" * 60)
    for name, scenario in SCENARIOS.items():
        print(f"\n{scenario}")
        print("-" * 60)


if __name__ == "__main__":
    list_scenarios()
