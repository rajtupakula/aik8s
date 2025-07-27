from typing import Dict, Any, List

# Exporting various types and interfaces used throughout the project

# Type definitions for expert patterns
ExpertPattern = Dict[str, Any]

# Type definitions for historical issues
HistoricalIssue = Dict[str, Any]

# Type definitions for system health metrics
HealthMetrics = Dict[str, float]

# Type definitions for user queries
UserQuery = Dict[str, str]

# Type definitions for remediation actions
RemediationAction = Dict[str, Any]

# Type definitions for model configurations
ModelConfig = Dict[str, Any]

# Type definitions for logging information
LogEntry = Dict[str, Any]

# Type definitions for system status
SystemStatus = Dict[str, Any]

# List of expert patterns
ExpertPatternsList = List[ExpertPattern]

# List of historical issues
HistoricalIssuesList = List[HistoricalIssue]