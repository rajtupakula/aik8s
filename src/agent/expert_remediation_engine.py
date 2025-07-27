import yaml
import json
import re
import subprocess
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import os
import sys

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.issue_history_manager import IssueHistoryManager
from agent.utils import SafetyValidator, SystemMonitor

@dataclass
class IssuePattern:
    """Represents an expert issue pattern with all metadata"""
    id: int
    category: str
    name: str
    keywords: List[str]
    regex_patterns: List[str]
    severity: str
    confidence_base: float
    description: str
    symptoms: List[str]
    remediation_steps: List[Dict[str, Any]]

@dataclass
class MatchResult:
    """Represents the result of pattern matching"""
    pattern: IssuePattern
    confidence: float
    matched_keywords: List[str]
    matched_regex: List[str]
    historical_context: Dict[str, Any]
    root_cause_prediction: str

class ExpertRemediationEngine:
    """
    Expert Remediation Engine - The brain of the expert system
    
    Features:
    - 14 expert patterns across Ubuntu OS, Kubernetes, and GlusterFS
    - Historical learning with confidence scoring
    - Safety-first command execution with validation
    - Real-time system health monitoring
    - Root cause prediction based on historical patterns
    """
    
    def __init__(self, patterns_file: str = None, history_file: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize paths
        if patterns_file is None:
            patterns_file = os.path.join(os.path.dirname(__file__), '../data/expert_patterns.yaml')
        if history_file is None:
            history_file = os.path.join(os.path.dirname(__file__), '../data/historical_issues.json')
            
        # Load components
        self.knowledge_base = self.load_knowledge_base(patterns_file)
        self.issue_history = IssueHistoryManager(history_file)
        self.safety_validator = SafetyValidator()
        self.system_monitor = SystemMonitor()
        
        # Configuration
        self.confidence_adjustments = {
            'historical_match': 0.15,
            'system_context': 0.10,
            'pattern_specificity': 0.05
        }
        
        self.logger.info(f"Expert Remediation Engine initialized with {len(self.knowledge_base)} patterns")

    def load_knowledge_base(self, patterns_file: str) -> Dict[str, IssuePattern]:
        """Load expert patterns from YAML file"""
        try:
            with open(patterns_file, 'r') as file:
                data = yaml.safe_load(file)
                
            knowledge_base = {}
            patterns = data.get('patterns', {})
            
            for pattern_id, pattern_data in patterns.items():
                pattern = IssuePattern(
                    id=pattern_data['id'],
                    category=pattern_data['category'],
                    name=pattern_data['name'],
                    keywords=pattern_data['keywords'],
                    regex_patterns=pattern_data['regex_patterns'],
                    severity=pattern_data['severity'],
                    confidence_base=pattern_data['confidence_base'],
                    description=pattern_data['description'],
                    symptoms=pattern_data.get('symptoms', []),
                    remediation_steps=pattern_data['remediation_steps']
                )
                knowledge_base[pattern_id] = pattern
                
            return knowledge_base
            
        except Exception as e:
            self.logger.error(f"Error loading knowledge base: {e}")
            return {}

    def recognize_issue_pattern(self, user_input: str, system_context: Dict = None) -> Optional[MatchResult]:
        """
        Analyze user input and match it against known patterns with historical learning
        
        Args:
            user_input: Natural language description of the issue
            system_context: Current system state information
            
        Returns:
            MatchResult with confidence scoring and historical context
        """
        try:
            user_input_lower = user_input.lower()
            best_match = None
            highest_confidence = 0.0
            
            for pattern_id, pattern in self.knowledge_base.items():
                confidence = self._calculate_confidence(pattern, user_input_lower, system_context)
                
                if confidence > highest_confidence and confidence > 0.5:  # Minimum confidence threshold
                    matched_keywords = [kw for kw in pattern.keywords if kw.lower() in user_input_lower]
                    matched_regex = []
                    
                    # Check regex patterns
                    for regex_pattern in pattern.regex_patterns:
                        if re.search(regex_pattern, user_input_lower, re.IGNORECASE):
                            matched_regex.append(regex_pattern)
                    
                    # Get historical context
                    historical_context = self.issue_history.get_pattern_history(pattern_id)
                    
                    # Predict root cause
                    root_cause_prediction = self._predict_root_cause(pattern_id, historical_context, system_context)
                    
                    best_match = MatchResult(
                        pattern=pattern,
                        confidence=confidence,
                        matched_keywords=matched_keywords,
                        matched_regex=matched_regex,
                        historical_context=historical_context,
                        root_cause_prediction=root_cause_prediction
                    )
                    highest_confidence = confidence
            
            return best_match
            
        except Exception as e:
            self.logger.error(f"Error in pattern recognition: {e}")
            return None

    def _calculate_confidence(self, pattern: IssuePattern, user_input: str, system_context: Dict = None) -> float:
        """Calculate confidence score for pattern match"""
        base_confidence = pattern.confidence_base
        
        # Keyword matching score
        keyword_matches = sum(1 for kw in pattern.keywords if kw.lower() in user_input)
        keyword_score = (keyword_matches / len(pattern.keywords)) * 0.4
        
        # Regex pattern matching score
        regex_matches = sum(1 for regex in pattern.regex_patterns 
                          if re.search(regex, user_input, re.IGNORECASE))
        regex_score = (regex_matches / len(pattern.regex_patterns)) * 0.3
        
        # Historical match adjustment
        historical_boost = 0.0
        pattern_id = f"{pattern.category.lower().replace(' ', '_')}_{pattern.name.lower().replace(' ', '_')}"
        if self.issue_history.has_similar_issue(pattern_id):
            historical_boost = self.confidence_adjustments['historical_match']
        
        # System context adjustment
        context_boost = 0.0
        if system_context:
            context_boost = self._calculate_context_relevance(pattern, system_context)
        
        # Calculate final confidence
        final_confidence = min(1.0, base_confidence + keyword_score + regex_score + historical_boost + context_boost)
        
        return final_confidence

    def _calculate_context_relevance(self, pattern: IssuePattern, system_context: Dict) -> float:
        """Calculate relevance boost based on current system context"""
        relevance = 0.0
        
        # Add context-specific logic based on pattern category
        if pattern.category == "Kubernetes":
            if system_context.get('kubernetes_available', False):
                relevance += 0.05
            if system_context.get('pod_errors', 0) > 0 and 'pod' in pattern.name.lower():
                relevance += 0.05
                
        elif pattern.category == "Ubuntu OS":
            if system_context.get('os_type') == 'ubuntu':
                relevance += 0.05
            if pattern.name == "Disk Space Issues" and system_context.get('disk_usage', 0) > 80:
                relevance += 0.10
                
        elif pattern.category == "GlusterFS":
            if system_context.get('gluster_available', False):
                relevance += 0.05
                
        return min(0.10, relevance)  # Cap at 10% boost

    def _predict_root_cause(self, pattern_id: str, historical_context: Dict, system_context: Dict = None) -> str:
        """Predict root cause based on historical data and current context"""
        if not historical_context.get('patterns'):
            return "No historical data available for prediction"
        
        patterns = historical_context['patterns']
        common_causes = patterns.get('common_causes', [])
        
        if not common_causes:
            return "Historical data insufficient for prediction"
        
        # Use most common cause as primary prediction
        primary_cause = common_causes[0] if common_causes else "Unknown"
        success_rate = patterns.get('success_rate', 0.0)
        
        prediction = f"Most likely cause: {primary_cause.replace('_', ' ').title()}"
        prediction += f" (Historical success rate: {success_rate*100:.1f}%)"
        
        if len(common_causes) > 1:
            prediction += f". Alternative causes: {', '.join(common_causes[1:])}"
        
        return prediction

    def generate_remediation_plan(self, match_result: MatchResult, auto_execute: bool = False) -> Dict[str, Any]:
        """
        Generate step-by-step remediation plan based on the recognized pattern
        
        Args:
            match_result: Result from pattern matching
            auto_execute: Whether to automatically execute safe commands
            
        Returns:
            Comprehensive remediation plan with safety checks
        """
        try:
            pattern = match_result.pattern
            historical_context = match_result.historical_context
            
            # Generate enhanced plan
            plan = {
                'issue_summary': {
                    'pattern_name': pattern.name,
                    'category': pattern.category,
                    'severity': pattern.severity,
                    'confidence': match_result.confidence,
                    'description': pattern.description
                },
                'historical_analysis': {
                    'similar_issues': len(historical_context.get('occurrences', [])),
                    'success_rate': historical_context.get('patterns', {}).get('success_rate', 0.0),
                    'avg_resolution_time': historical_context.get('patterns', {}).get('avg_resolution_time', 0),
                    'root_cause_prediction': match_result.root_cause_prediction
                },
                'remediation_steps': [],
                'safety_assessment': {},
                'execution_results': {}
            }
            
            # Process each remediation step
            for i, step in enumerate(pattern.remediation_steps, 1):
                step_info = {
                    'step_number': i,
                    'action': step['action'],
                    'command': step['command'],
                    'description': step['description'],
                    'safety_level': step['safety_level'],
                    'status': 'pending',
                    'output': None,
                    'execution_time': None
                }
                
                # Perform safety checks
                safety_result = self.safety_validator.validate_command(
                    step['command'], 
                    step['safety_level']
                )
                step_info['safety_check'] = safety_result
                
                # Auto-execute safe commands if requested
                if auto_execute and safety_result['safe'] and step['safety_level'] == 'SAFE':
                    execution_result = self._execute_command_safely(step['command'])
                    step_info.update(execution_result)
                
                plan['remediation_steps'].append(step_info)
            
            # Overall safety assessment
            plan['safety_assessment'] = self._assess_overall_safety(plan['remediation_steps'])
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Error generating remediation plan: {e}")
            return {'error': str(e)}

    def _execute_command_safely(self, command: str) -> Dict[str, Any]:
        """Execute command with safety monitoring and timeout"""
        start_time = datetime.now()
        
        try:
            # Add timeout and safety wrapper
            if command.startswith('sudo'):
                # Skip sudo commands in safe execution
                return {
                    'status': 'skipped',
                    'output': 'Sudo commands require manual execution',
                    'execution_time': 0
                }
            
            # Execute with timeout
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'status': 'completed' if result.returncode == 0 else 'failed',
                'output': result.stdout if result.returncode == 0 else result.stderr,
                'return_code': result.returncode,
                'execution_time': execution_time
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'output': 'Command execution timed out after 30 seconds',
                'execution_time': 30
            }
        except Exception as e:
            return {
                'status': 'error',
                'output': str(e),
                'execution_time': (datetime.now() - start_time).total_seconds()
            }

    def _assess_overall_safety(self, steps: List[Dict]) -> Dict[str, Any]:
        """Assess overall safety of the remediation plan"""
        safe_steps = sum(1 for step in steps if step.get('safety_check', {}).get('safe', False))
        total_steps = len(steps)
        
        high_risk_steps = [step for step in steps if step.get('safety_level') == 'HIGH']
        medium_risk_steps = [step for step in steps if step.get('safety_level') == 'MEDIUM']
        
        return {
            'overall_risk': 'HIGH' if high_risk_steps else ('MEDIUM' if medium_risk_steps else 'LOW'),
            'safe_steps_ratio': safe_steps / total_steps if total_steps > 0 else 0,
            'requires_confirmation': len(medium_risk_steps + high_risk_steps) > 0,
            'auto_executable_steps': safe_steps,
            'manual_steps': len(high_risk_steps + medium_risk_steps)
        }

    def execute_remediation(self, remediation_plan: Dict[str, Any], step_indices: List[int] = None, 
                          force: bool = False) -> Dict[str, Any]:
        """
        Execute the remediation plan with comprehensive safety checks
        
        Args:
            remediation_plan: Generated remediation plan
            step_indices: Specific steps to execute (None for all)
            force: Override safety checks (use with caution)
            
        Returns:
            Execution results with detailed logging
        """
        try:
            if step_indices is None:
                step_indices = list(range(len(remediation_plan['remediation_steps'])))
            
            execution_log = {
                'start_time': datetime.now(timezone.utc).isoformat(),
                'executed_steps': [],
                'overall_success': True,
                'total_execution_time': 0
            }
            
            for idx in step_indices:
                if idx >= len(remediation_plan['remediation_steps']):
                    continue
                
                step = remediation_plan['remediation_steps'][idx]
                
                # Skip if already executed
                if step.get('status') in ['completed', 'skipped']:
                    continue
                
                # Safety check unless forced
                if not force:
                    safety_check = step.get('safety_check', {})
                    if not safety_check.get('safe', False):
                        step['status'] = 'skipped_unsafe'
                        step['output'] = f"Skipped due to safety concerns: {safety_check.get('reason', 'Unknown')}"
                        continue
                
                # Execute the step
                self.logger.info(f"Executing step {idx + 1}: {step['action']}")
                execution_result = self._execute_command_safely(step['command'])
                
                # Update step with results
                step.update(execution_result)
                execution_log['executed_steps'].append({
                    'step_number': idx + 1,
                    'action': step['action'],
                    'status': step['status'],
                    'execution_time': step.get('execution_time', 0)
                })
                
                if step['status'] in ['failed', 'error']:
                    execution_log['overall_success'] = False
                
                execution_log['total_execution_time'] += step.get('execution_time', 0)
            
            execution_log['end_time'] = datetime.now(timezone.utc).isoformat()
            
            # Update learning system
            self._update_learning(remediation_plan, execution_log)
            
            return execution_log
            
        except Exception as e:
            self.logger.error(f"Error executing remediation: {e}")
            return {'error': str(e), 'overall_success': False}

    def _update_learning(self, remediation_plan: Dict, execution_log: Dict) -> None:
        """Update the learning system with execution results"""
        try:
            pattern_name = remediation_plan['issue_summary']['pattern_name']
            pattern_id = pattern_name.lower().replace(' ', '_')
            
            # Prepare learning data
            learning_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'pattern_id': pattern_id,
                'confidence': remediation_plan['issue_summary']['confidence'],
                'success': execution_log['overall_success'],
                'execution_time': execution_log['total_execution_time'],
                'steps_executed': len(execution_log['executed_steps']),
                'category': remediation_plan['issue_summary']['category']
            }
            
            # Update issue history
            self.issue_history.record_resolution(pattern_id, learning_data)
            
        except Exception as e:
            self.logger.error(f"Error updating learning system: {e}")

    def get_system_health_status(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        try:
            return self.system_monitor.get_comprehensive_status()
        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return {'error': str(e)}

    def perform_expert_diagnosis(self) -> Dict[str, Any]:
        """Perform comprehensive expert system diagnosis"""
        try:
            diagnosis = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'system_health': self.get_system_health_status(),
                'detected_issues': [],
                'recommendations': [],
                'confidence_scores': {}
            }
            
            # Get current system context
            system_context = diagnosis['system_health']
            
            # Check for potential issues based on system state
            potential_issues = self._detect_potential_issues(system_context)
            
            for issue in potential_issues:
                match_result = self.recognize_issue_pattern(issue['description'], system_context)
                if match_result:
                    diagnosis['detected_issues'].append({
                        'pattern': match_result.pattern.name,
                        'category': match_result.pattern.category,
                        'confidence': match_result.confidence,
                        'severity': match_result.pattern.severity,
                        'description': match_result.pattern.description,
                        'root_cause_prediction': match_result.root_cause_prediction
                    })
                    
                    diagnosis['confidence_scores'][match_result.pattern.name] = match_result.confidence
            
            # Generate proactive recommendations
            diagnosis['recommendations'] = self._generate_proactive_recommendations(diagnosis)
            
            return diagnosis
            
        except Exception as e:
            self.logger.error(f"Error in expert diagnosis: {e}")
            return {'error': str(e)}

    def _detect_potential_issues(self, system_context: Dict) -> List[Dict[str, str]]:
        """Detect potential issues based on current system state"""
        potential_issues = []
        
        # Check disk usage
        if system_context.get('disk_usage', 0) > 85:
            potential_issues.append({
                'description': 'High disk usage detected, potential disk space issues',
                'category': 'Ubuntu OS'
            })
        
        # Check memory usage
        if system_context.get('memory_usage', 0) > 90:
            potential_issues.append({
                'description': 'High memory usage detected, potential memory pressure',
                'category': 'Ubuntu OS'
            })
        
        # Check for failed pods (if Kubernetes context available)
        if system_context.get('kubernetes_available') and system_context.get('failed_pods', 0) > 0:
            potential_issues.append({
                'description': 'Failed pods detected in Kubernetes cluster',
                'category': 'Kubernetes'
            })
        
        return potential_issues

    def _generate_proactive_recommendations(self, diagnosis: Dict) -> List[str]:
        """Generate proactive recommendations based on diagnosis"""
        recommendations = []
        
        # Based on detected issues
        for issue in diagnosis.get('detected_issues', []):
            if issue['category'] == 'Ubuntu OS':
                if 'disk' in issue['pattern'].lower():
                    recommendations.append("Schedule regular disk cleanup automation")
                elif 'memory' in issue['pattern'].lower():
                    recommendations.append("Implement memory monitoring and alerting")
            
            elif issue['category'] == 'Kubernetes':
                recommendations.append("Set up proactive pod health monitoring")
                recommendations.append("Review resource requests and limits")
            
            elif issue['category'] == 'GlusterFS':
                recommendations.append("Schedule regular GlusterFS health checks")
        
        # General recommendations if no issues found
        if not diagnosis.get('detected_issues'):
            recommendations.extend([
                "System appears healthy - continue regular monitoring",
                "Consider implementing preventive maintenance schedules",
                "Review and update backup strategies"
            ])
        
        return recommendations