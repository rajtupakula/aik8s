"""
Issue History Manager - Enhanced with continuous learning and predictive analytics
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import os
import subprocess
import re

@dataclass
class IssueOccurrence:
    """Represents a single issue occurrence"""
    timestamp: str
    severity: str
    resolution_time: int
    success: bool
    root_cause: str
    resolution_method: str
    confidence_score: float
    system_context: Dict[str, Any]

@dataclass
class IssuePattern:
    """Represents learned patterns for an issue type"""
    common_causes: List[str]
    success_rate: float
    avg_resolution_time: int
    frequency_trend: str
    seasonal_pattern: str

class IssueHistoryManager:
    """
    Enhanced Issue History Manager with continuous learning and predictive analytics
    
    Features:
    - Tracks last 3 occurrences of each issue type
    - Continuous learning from system logs (Kubernetes, Ubuntu, GlusterFS)
    - Root cause prediction with confidence scoring
    - Pattern recognition across 14 expert issue types
    - Trend analysis and issue frequency tracking
    - Historical success rate tracking for recommendations
    """
    
    def __init__(self, history_file: str = None):
        self.logger = logging.getLogger(__name__)
        
        if history_file is None:
            history_file = os.path.join(os.path.dirname(__file__), '../data/historical_issues.json')
        
        self.history_file = history_file
        self.max_occurrences = 3  # Keep last 3 occurrences per issue type
        self.data = self._load_history()
        
        # Initialize learning weights
        self.learning_weights = {
            'success_rate': 0.4,
            'frequency': 0.3,
            'recency': 0.2,
            'specificity': 0.1
        }
        
        self.logger.info("Issue History Manager initialized with continuous learning")

    def _load_history(self) -> Dict[str, Any]:
        """Load historical issues data"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            else:
                return self._create_default_structure()
        except Exception as e:
            self.logger.error(f"Error loading history: {e}")
            return self._create_default_structure()

    def _create_default_structure(self) -> Dict[str, Any]:
        """Create default data structure"""
        return {
            'issue_history': {},
            'learning_analytics': {
                'total_issues_tracked': 0,
                'overall_success_rate': 0.0,
                'avg_resolution_time': 0,
                'most_common_categories': [],
                'trend_analysis': {
                    'improving_areas': [],
                    'stable_areas': [],
                    'concerning_areas': []
                },
                'predictive_indicators': {
                    'high_risk_periods': [],
                    'early_warning_signals': [],
                    'proactive_recommendations': []
                }
            },
            'system_baselines': {
                'ubuntu_os': {
                    'disk_usage_normal': 75,
                    'memory_usage_normal': 60,
                    'cpu_usage_normal': 40,
                    'service_uptime_target': 99.9
                },
                'kubernetes': {
                    'pod_restart_rate_normal': 0.1,
                    'node_ready_percentage': 100,
                    'resource_utilization_target': 70,
                    'deployment_success_rate': 98
                },
                'glusterfs': {
                    'heal_queue_normal': 0,
                    'peer_connectivity': 100,
                    'volume_uptime_target': 99.95,
                    'split_brain_tolerance': 0
                }
            }
        }

    def _save_history(self) -> None:
        """Save history data to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving history: {e}")

    def track_issue(self, issue_id: str, occurrence_data: Dict[str, Any]) -> None:
        """
        Track a new issue occurrence with enhanced data
        
        Args:
            issue_id: Unique identifier for the issue type
            occurrence_data: Detailed occurrence information
        """
        try:
            if issue_id not in self.data['issue_history']:
                self.data['issue_history'][issue_id] = {
                    'occurrences': [],
                    'patterns': {
                        'common_causes': [],
                        'success_rate': 0.0,
                        'avg_resolution_time': 0,
                        'frequency_trend': 'stable',
                        'seasonal_pattern': 'none'
                    }
                }
            
            issue_history = self.data['issue_history'][issue_id]
            
            # Add new occurrence
            new_occurrence = {
                'timestamp': occurrence_data.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'severity': occurrence_data.get('severity', 'MEDIUM'),
                'resolution_time': occurrence_data.get('resolution_time', 0),
                'success': occurrence_data.get('success', False),
                'root_cause': occurrence_data.get('root_cause', 'Unknown'),
                'resolution_method': occurrence_data.get('resolution_method', 'Manual'),
                'confidence_score': occurrence_data.get('confidence_score', 0.5),
                'system_context': occurrence_data.get('system_context', {})
            }
            
            issue_history['occurrences'].append(new_occurrence)
            
            # Keep only last N occurrences
            if len(issue_history['occurrences']) > self.max_occurrences:
                issue_history['occurrences'] = issue_history['occurrences'][-self.max_occurrences:]
            
            # Update patterns
            self._update_patterns(issue_id)
            
            # Update analytics
            self._update_analytics()
            
            # Save changes
            self._save_history()
            
            self.logger.info(f"Tracked new occurrence for issue: {issue_id}")
            
        except Exception as e:
            self.logger.error(f"Error tracking issue {issue_id}: {e}")

    def get_pattern_history(self, issue_id: str) -> Dict[str, Any]:
        """Get historical pattern data for an issue type"""
        try:
            if issue_id in self.data['issue_history']:
                return self.data['issue_history'][issue_id]
            else:
                return {'occurrences': [], 'patterns': {}}
        except Exception as e:
            self.logger.error(f"Error getting pattern history for {issue_id}: {e}")
            return {'occurrences': [], 'patterns': {}}

    def has_similar_issue(self, issue_id: str) -> bool:
        """Check if similar issue has occurred before"""
        return issue_id in self.data['issue_history'] and len(self.data['issue_history'][issue_id]['occurrences']) > 0

    def record_resolution(self, issue_id: str, resolution_data: Dict[str, Any]) -> None:
        """Record the resolution of an issue for learning"""
        try:
            # Create occurrence data from resolution
            occurrence_data = {
                'timestamp': resolution_data.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'severity': resolution_data.get('severity', 'MEDIUM'),
                'resolution_time': resolution_data.get('execution_time', 0),
                'success': resolution_data.get('success', False),
                'root_cause': resolution_data.get('root_cause', 'System remediation'),
                'resolution_method': resolution_data.get('resolution_method', 'Automated'),
                'confidence_score': resolution_data.get('confidence', 0.5),
                'system_context': resolution_data.get('system_context', {})
            }
            
            self.track_issue(issue_id, occurrence_data)
            
        except Exception as e:
            self.logger.error(f"Error recording resolution for {issue_id}: {e}")

    def _update_patterns(self, issue_id: str) -> None:
        """Update learned patterns for an issue type"""
        try:
            issue_data = self.data['issue_history'][issue_id]
            occurrences = issue_data['occurrences']
            
            if not occurrences:
                return
            
            # Calculate success rate
            successful = sum(1 for occ in occurrences if occ['success'])
            success_rate = successful / len(occurrences)
            
            # Calculate average resolution time
            resolution_times = [occ['resolution_time'] for occ in occurrences if occ['success']]
            avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
            
            # Extract common causes
            causes = [occ['root_cause'] for occ in occurrences if occ['root_cause'] != 'Unknown']
            common_causes = list(set(causes))  # Unique causes
            
            # Determine frequency trend
            if len(occurrences) >= 2:
                recent_timestamps = [datetime.fromisoformat(occ['timestamp'].replace('Z', '+00:00')) 
                                   for occ in occurrences[-2:]]
                time_diff = (recent_timestamps[-1] - recent_timestamps[-2]).days
                
                if time_diff < 7:
                    frequency_trend = "increasing"
                elif time_diff > 30:
                    frequency_trend = "decreasing"
                else:
                    frequency_trend = "stable"
            else:
                frequency_trend = "stable"
            
            # Update patterns
            issue_data['patterns'] = {
                'common_causes': common_causes,
                'success_rate': success_rate,
                'avg_resolution_time': int(avg_resolution_time),
                'frequency_trend': frequency_trend,
                'seasonal_pattern': self._detect_seasonal_pattern(occurrences)
            }
            
        except Exception as e:
            self.logger.error(f"Error updating patterns for {issue_id}: {e}")

    def _detect_seasonal_pattern(self, occurrences: List[Dict]) -> str:
        """Detect seasonal patterns in issue occurrences"""
        try:
            if len(occurrences) < 2:
                return "none"
            
            timestamps = [datetime.fromisoformat(occ['timestamp'].replace('Z', '+00:00')) 
                         for occ in occurrences]
            
            # Simple pattern detection based on time of day/week
            hours = [ts.hour for ts in timestamps]
            weekdays = [ts.weekday() for ts in timestamps]
            
            # Check for business hours pattern (9-17)
            business_hours = sum(1 for h in hours if 9 <= h <= 17)
            if business_hours / len(hours) > 0.7:
                return "business_hours"
            
            # Check for weekend pattern
            weekends = sum(1 for w in weekdays if w >= 5)
            if weekends / len(weekdays) > 0.7:
                return "weekends"
            
            # Check for maintenance windows (typically late night)
            night_hours = sum(1 for h in hours if h >= 22 or h <= 6)
            if night_hours / len(hours) > 0.5:
                return "maintenance_windows"
            
            return "none"
            
        except Exception as e:
            self.logger.error(f"Error detecting seasonal pattern: {e}")
            return "none"

    def _update_analytics(self) -> None:
        """Update overall analytics and insights"""
        try:
            all_issues = self.data['issue_history']
            
            if not all_issues:
                return
            
            # Calculate overall metrics
            total_occurrences = sum(len(issue['occurrences']) for issue in all_issues.values())
            total_successful = sum(sum(1 for occ in issue['occurrences'] if occ['success']) 
                                 for issue in all_issues.values())
            
            overall_success_rate = total_successful / total_occurrences if total_occurrences > 0 else 0
            
            # Calculate average resolution time
            all_resolution_times = []
            for issue in all_issues.values():
                for occ in issue['occurrences']:
                    if occ['success'] and occ['resolution_time'] > 0:
                        all_resolution_times.append(occ['resolution_time'])
            
            avg_resolution_time = sum(all_resolution_times) / len(all_resolution_times) if all_resolution_times else 0
            
            # Determine most common categories
            categories = defaultdict(int)
            for issue_id in all_issues.keys():
                if 'ubuntu' in issue_id:
                    categories['Ubuntu OS'] += 1
                elif 'k8s' in issue_id:
                    categories['Kubernetes'] += 1
                elif 'gluster' in issue_id:
                    categories['GlusterFS'] += 1
            
            most_common_categories = sorted(categories.keys(), key=lambda k: categories[k], reverse=True)
            
            # Update analytics
            self.data['learning_analytics'].update({
                'total_issues_tracked': len(all_issues),
                'overall_success_rate': round(overall_success_rate, 3),
                'avg_resolution_time': int(avg_resolution_time),
                'most_common_categories': most_common_categories[:3]
            })
            
        except Exception as e:
            self.logger.error(f"Error updating analytics: {e}")

    def get_learning_analytics(self) -> Dict[str, Any]:
        """Get comprehensive learning analytics and insights"""
        return self.data.get('learning_analytics', {})

    def predict_root_cause(self, issue_id: str, current_context: Dict[str, Any] = None) -> Tuple[str, float]:
        """
        Predict root cause based on historical patterns
        
        Args:
            issue_id: The issue type to predict for
            current_context: Current system context for enhanced prediction
            
        Returns:
            Tuple of (predicted_cause, confidence_score)
        """
        try:
            if not self.has_similar_issue(issue_id):
                return "No historical data available", 0.1
            
            issue_data = self.data['issue_history'][issue_id]
            occurrences = issue_data['occurrences']
            patterns = issue_data['patterns']
            
            # Get most common successful causes
            successful_occurrences = [occ for occ in occurrences if occ['success']]
            
            if not successful_occurrences:
                return "No successful resolutions in history", 0.2
            
            # Count cause frequencies
            cause_frequency = defaultdict(int)
            cause_success_rate = defaultdict(list)
            
            for occ in successful_occurrences:
                cause = occ['root_cause']
                cause_frequency[cause] += 1
                cause_success_rate[cause].append(occ['confidence_score'])
            
            # Calculate weighted scores for each cause
            cause_scores = {}
            for cause, frequency in cause_frequency.items():
                freq_weight = frequency / len(successful_occurrences)
                confidence_weight = sum(cause_success_rate[cause]) / len(cause_success_rate[cause])
                recency_weight = self._calculate_recency_weight(occurrences, cause)
                
                weighted_score = (
                    freq_weight * self.learning_weights['frequency'] +
                    confidence_weight * self.learning_weights['specificity'] +
                    recency_weight * self.learning_weights['recency'] +
                    patterns['success_rate'] * self.learning_weights['success_rate']
                )
                
                cause_scores[cause] = weighted_score
            
            # Get best prediction
            best_cause = max(cause_scores.keys(), key=lambda k: cause_scores[k])
            confidence = min(cause_scores[best_cause], 0.95)  # Cap at 95%
            
            self.logger.info(f"Predicted root cause for {issue_id}: {best_cause} (confidence: {confidence:.2f})")
            
            return best_cause, confidence
            
        except Exception as e:
            self.logger.error(f"Error predicting root cause for {issue_id}: {e}")
            return "Prediction error", 0.1

    def _calculate_recency_weight(self, occurrences: List[Dict], target_cause: str) -> float:
        """Calculate recency weight for a specific cause"""
        try:
            recent_occurrences = [occ for occ in occurrences[-2:] if occ['root_cause'] == target_cause]
            
            if not recent_occurrences:
                return 0.1
            
            # Higher weight for more recent occurrences
            recent_count = len(recent_occurrences)
            max_recent = min(len(occurrences), 2)
            
            return recent_count / max_recent
            
        except Exception as e:
            self.logger.error(f"Error calculating recency weight: {e}")
            return 0.1

    def get_recommendation_confidence(self, issue_id: str, resolution_method: str) -> float:
        """
        Get confidence score for a specific resolution method based on history
        
        Args:
            issue_id: The issue type
            resolution_method: The proposed resolution method
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        try:
            if not self.has_similar_issue(issue_id):
                return 0.3  # Default confidence for new issues
            
            issue_data = self.data['issue_history'][issue_id]
            occurrences = issue_data['occurrences']
            
            # Find occurrences with similar resolution method
            similar_resolutions = [
                occ for occ in occurrences 
                if resolution_method.lower() in occ['resolution_method'].lower()
            ]
            
            if not similar_resolutions:
                return 0.4  # Moderate confidence for untested methods
            
            # Calculate success rate for this method
            successful = sum(1 for occ in similar_resolutions if occ['success'])
            success_rate = successful / len(similar_resolutions)
            
            # Adjust based on overall pattern success rate
            overall_success_rate = issue_data['patterns']['success_rate']
            adjusted_confidence = (success_rate * 0.7) + (overall_success_rate * 0.3)
            
            return min(adjusted_confidence, 0.95)  # Cap at 95%
            
        except Exception as e:
            self.logger.error(f"Error calculating recommendation confidence: {e}")
            return 0.3

    def get_trending_issues(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get trending issues based on recent activity
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of trending issue data
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            trending_issues = []
            
            for issue_id, issue_data in self.data['issue_history'].items():
                recent_occurrences = [
                    occ for occ in issue_data['occurrences']
                    if datetime.fromisoformat(occ['timestamp'].replace('Z', '+00:00')) > cutoff_date
                ]
                
                if recent_occurrences:
                    severity_scores = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
                    avg_severity = sum(severity_scores.get(occ['severity'], 2) for occ in recent_occurrences) / len(recent_occurrences)
                    
                    trending_data = {
                        'issue_id': issue_id,
                        'frequency': len(recent_occurrences),
                        'avg_severity': avg_severity,
                        'success_rate': sum(1 for occ in recent_occurrences if occ['success']) / len(recent_occurrences),
                        'trend': issue_data['patterns']['frequency_trend'],
                        'last_occurrence': recent_occurrences[-1]['timestamp']
                    }
                    
                    trending_issues.append(trending_data)
            
            # Sort by frequency and severity
            trending_issues.sort(
                key=lambda x: (x['frequency'] * x['avg_severity']), 
                reverse=True
            )
            
            return trending_issues[:10]  # Top 10 trending issues
            
        except Exception as e:
            self.logger.error(f"Error getting trending issues: {e}")
            return []

    def continuous_learning_scan(self) -> Dict[str, Any]:
        """
        Perform continuous learning scan of system logs
        
        Returns:
            Summary of learning updates
        """
        learning_summary = {
            'scan_timestamp': datetime.now(timezone.utc).isoformat(),
            'new_patterns_detected': 0,
            'updated_patterns': 0,
            'anomalies_found': [],
            'recommendations': []
        }
        
        try:
            # Scan system logs for new patterns
            log_patterns = self._scan_system_logs()
            
            for pattern in log_patterns:
                if pattern['confidence'] > 0.7:
                    # Update or create issue pattern
                    issue_id = pattern['issue_id']
                    
                    if issue_id in self.data['issue_history']:
                        learning_summary['updated_patterns'] += 1
                    else:
                        learning_summary['new_patterns_detected'] += 1
                    
                    # Track the pattern
                    self.track_issue(issue_id, pattern['data'])
            
            # Generate proactive recommendations
            learning_summary['recommendations'] = self._generate_proactive_recommendations()
            
            self.logger.info(f"Continuous learning scan completed: {learning_summary}")
            
        except Exception as e:
            self.logger.error(f"Error in continuous learning scan: {e}")
            learning_summary['error'] = str(e)
        
        return learning_summary

    def _scan_system_logs(self) -> List[Dict[str, Any]]:
        """
        Scan system logs for patterns (placeholder implementation)
        
        In a real implementation, this would:
        - Parse Kubernetes logs for pod failures
        - Monitor Ubuntu system logs for service issues
        - Check GlusterFS logs for storage problems
        """
        patterns = []
        
        try:
            # Example: Check for recent systemd service failures
            result = subprocess.run(['journalctl', '--since', '1 hour ago', '--priority=err', '-o', 'json-short'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            log_entry = json.loads(line)
                            if 'failed' in log_entry.get('MESSAGE', '').lower():
                                pattern = {
                                    'issue_id': f"ubuntu_service_failure_{log_entry.get('UNIT', 'unknown')}",
                                    'confidence': 0.8,
                                    'data': {
                                        'timestamp': datetime.now(timezone.utc).isoformat(),
                                        'severity': 'HIGH',
                                        'root_cause': f"Service failure: {log_entry.get('UNIT', 'unknown')}",
                                        'resolution_method': 'Service restart required',
                                        'system_context': log_entry
                                    }
                                }
                                patterns.append(pattern)
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            self.logger.warning(f"Could not scan system logs: {e}")
        
        return patterns

    def _generate_proactive_recommendations(self) -> List[Dict[str, Any]]:
        """Generate proactive recommendations based on patterns"""
        recommendations = []
        
        try:
            # Analyze patterns for proactive insights
            for issue_id, issue_data in self.data['issue_history'].items():
                patterns = issue_data['patterns']
                
                # Check for concerning trends
                if patterns['frequency_trend'] == 'increasing':
                    recommendations.append({
                        'type': 'proactive_monitoring',
                        'issue_id': issue_id,
                        'priority': 'HIGH',
                        'message': f"Increasing frequency detected for {issue_id}. Consider proactive monitoring.",
                        'suggested_actions': [
                            'Increase monitoring frequency',
                            'Review system capacity',
                            'Implement preventive measures'
                        ]
                    })
                
                # Check for low success rates
                if patterns['success_rate'] < 0.5:
                    recommendations.append({
                        'type': 'resolution_improvement',
                        'issue_id': issue_id,
                        'priority': 'MEDIUM',
                        'message': f"Low success rate ({patterns['success_rate']:.1%}) for {issue_id}. Review resolution procedures.",
                        'suggested_actions': [
                            'Review resolution procedures',
                            'Update troubleshooting guides',
                            'Consider automation improvements'
                        ]
                    })
                    
        except Exception as e:
            self.logger.error(f"Error generating proactive recommendations: {e}")
        
        return recommendations

    def get_learning_updates(self):
        return self.learning_updates