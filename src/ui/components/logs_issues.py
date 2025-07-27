"""
Logs and Issues Component - Monitor and analyze system logs and tracked issues
"""

import streamlit as st
import logging
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

class LogsIssuesComponent:
    """
    Logs and Issues monitoring component
    
    Features:
    - Real-time log monitoring
    - Issue tracking and analysis
    - Historical issue trends
    - Pattern recognition insights
    """
    
    def __init__(self, history_manager):
        self.logger = logging.getLogger(__name__)
        self.history_manager = history_manager
        # Legacy compatibility
        self.logs = []
        self.issues = []

    def render(self):
        """Render the logs and issues interface"""
        st.header("📋 Logs & Issues Monitor")
        st.markdown("*Monitor system logs, track issues, and analyze patterns*")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Active Issues", "📈 Historical Trends", "🔍 Log Analysis"])
        
        with tab1:
            self._render_active_issues()
        
        with tab2:
            self._render_historical_trends()
        
        with tab3:
            self._render_log_analysis()

    def _render_active_issues(self):
        """Render active issues monitoring"""
        st.subheader("🚨 Active Issues (Last 7 Days)")
        
        try:
            # Get trending issues
            trending_issues = self.history_manager.get_trending_issues(7)
            
            if not trending_issues:
                st.info("No active issues found in the last 7 days.")
                return
            
            # Display issues in a table
            issues_data = []
            for issue in trending_issues:
                issues_data.append({
                    'Issue ID': issue['issue_id'],
                    'Frequency': issue['frequency'],
                    'Severity': issue['avg_severity'],
                    'Success Rate': f"{issue['success_rate']*100:.1f}%",
                    'Trend': issue['trend'],
                    'Last Occurrence': issue['last_occurrence']
                })
            
            df = pd.DataFrame(issues_data)
            st.dataframe(df, use_container_width=True)
            
            # Issue details selection
            selected_issue = st.selectbox("Select issue for details:", [""] + [issue['issue_id'] for issue in trending_issues])
            if selected_issue:
                self._show_issue_details(selected_issue)
                    
        except Exception as e:
            st.error(f"Error loading active issues: {e}")

    def _render_historical_trends(self):
        """Render historical trends analysis"""
        st.subheader("📈 Historical Issue Trends")
        
        try:
            # Get learning analytics
            analytics = self.history_manager.get_learning_analytics()
            
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Issues Tracked", analytics.get('total_issues_tracked', 0))
            
            with col2:
                st.metric("Overall Success Rate", f"{analytics.get('overall_success_rate', 0)*100:.1f}%")
            
            with col3:
                st.metric("Avg Resolution Time", f"{analytics.get('avg_resolution_time', 0)} min")
            
            with col4:
                most_common = analytics.get('most_common_categories', [])
                st.metric("Top Category", most_common[0] if most_common else "None")
            
            # Trend analysis
            if 'trend_analysis' in analytics:
                st.subheader("🔍 Trend Analysis")
                
                trend_data = analytics['trend_analysis']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**🟢 Improving Areas:**")
                    for area in trend_data.get('improving_areas', []):
                        st.write(f"• {area}")
                
                with col2:
                    st.write("**🟡 Stable Areas:**")
                    for area in trend_data.get('stable_areas', []):
                        st.write(f"• {area}")
                
                with col3:
                    st.write("**🔴 Concerning Areas:**")
                    for area in trend_data.get('concerning_areas', []):
                        st.write(f"• {area}")
                        
        except Exception as e:
            st.error(f"Error loading historical trends: {e}")

    def _render_log_analysis(self):
        """Render log analysis interface"""
        st.subheader("🔍 Log Analysis")
        
        # Log analysis controls
        col1, col2 = st.columns(2)
        
        with col1:
            log_source = st.selectbox("Log Source", ["System", "Kubernetes", "GlusterFS", "Application"])
            time_range = st.selectbox("Time Range", ["Last Hour", "Last 24 Hours", "Last Week"])
        
        with col2:
            log_level = st.selectbox("Log Level", ["All", "Error", "Warning", "Info", "Debug"])
            search_term = st.text_input("Search Term", placeholder="Enter search term...")
        
        if st.button("🔍 Analyze Logs"):
            self._perform_log_analysis(log_source, time_range, log_level, search_term)

    def _show_issue_details(self, issue_id: str):
        """Show detailed information about a specific issue"""
        try:
            issue_history = self.history_manager.get_pattern_history(issue_id)
            
            st.subheader(f"📋 Issue Details: {issue_id}")
            
            if not issue_history or not issue_history.get('occurrences'):
                st.warning("No detailed history available for this issue.")
                return
            
            # Show patterns
            patterns = issue_history.get('patterns', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**📊 Pattern Summary:**")
                st.write(f"• Success Rate: {patterns.get('success_rate', 0)*100:.1f}%")
                st.write(f"• Avg Resolution Time: {patterns.get('avg_resolution_time', 0)} min")
                st.write(f"• Frequency Trend: {patterns.get('frequency_trend', 'Unknown')}")
            
            with col2:
                st.write("**🎯 Common Causes:**")
                for cause in patterns.get('common_causes', []):
                    st.write(f"• {cause}")
            
            # Show recent occurrences
            st.write("**🕐 Recent Occurrences:**")
            
            occurrences = issue_history['occurrences']
            for i, occurrence in enumerate(occurrences[-3:], 1):  # Last 3
                with st.expander(f"Occurrence {i} - {occurrence.get('timestamp', 'Unknown time')}"):
                    st.write(f"**Severity:** {occurrence.get('severity', 'Unknown')}")
                    st.write(f"**Root Cause:** {occurrence.get('root_cause', 'Unknown')}")
                    st.write(f"**Resolution Method:** {occurrence.get('resolution_method', 'Unknown')}")
                    st.write(f"**Success:** {'✅' if occurrence.get('success') else '❌'}")
                    st.write(f"**Resolution Time:** {occurrence.get('resolution_time', 0)} minutes")
                    
        except Exception as e:
            st.error(f"Error showing issue details: {e}")

    def _perform_log_analysis(self, source: str, time_range: str, level: str, search_term: str):
        """Perform log analysis based on parameters"""
        try:
            with st.spinner("Analyzing logs..."):
                # Simulate log analysis (in real implementation, this would parse actual logs)
                st.success("Log analysis completed!")
                
                # Mock results
                st.subheader("📊 Analysis Results")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Log Entries Found", "1,247")
                
                with col2:
                    st.metric("Error Entries", "23")
                
                with col3:
                    st.metric("Patterns Detected", "3")
                
                # Mock log entries
                st.subheader("📝 Sample Log Entries")
                
                sample_logs = [
                    {"timestamp": "2024-01-15 14:30:15", "level": "ERROR", "message": "Pod restart due to memory limit exceeded"},
                    {"timestamp": "2024-01-15 14:28:42", "level": "WARNING", "message": "High disk usage detected on node worker-1"},
                    {"timestamp": "2024-01-15 14:25:33", "level": "INFO", "message": "GlusterFS volume heal completed successfully"}
                ]
                
                for log in sample_logs:
                    if search_term and search_term.lower() not in log['message'].lower():
                        continue
                    
                    level_color = {"ERROR": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(log['level'], "⚪")
                    st.write(f"{level_color} **{log['timestamp']}** [{log['level']}] {log['message']}")
                    
        except Exception as e:
            st.error(f"Log analysis failed: {e}")

    # Legacy methods for compatibility
    def add_log(self, log_entry):
        """Legacy method - logs are now managed by history manager"""
        self.logs.append(log_entry)

    def add_issue(self, issue):
        """Legacy method - issues are now tracked via history manager"""
        self.issues.append(issue)

    def get_logs(self):
        """Legacy method"""
        return self.logs

    def get_issues(self):
        """Legacy method"""
        return self.issues

    def clear_logs(self):
        """Legacy method"""
        self.logs = []

    def clear_issues(self):
        """Legacy method"""
        self.issues = []

    def display(self):
        """Legacy method for compatibility"""
        self.render()

# Legacy alias for compatibility
LogsIssues = LogsIssuesComponent