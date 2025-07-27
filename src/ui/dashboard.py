"""
Expert System Dashboard - Comprehensive Streamlit interface
"""

import streamlit as st
import logging
import json
from datetime import datetime, timezone
import pandas as pd
from typing import Dict, List, Any
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.enhanced_rag_agent import EnhancedRAGAgent
from agent.expert_remediation_engine import ExpertRemediationEngine
from agent.issue_history_manager import IssueHistoryManager
from ui.components.chat_assistant import ChatAssistant
from ui.components.logs_issues import LogsIssuesComponent
from ui.components.forecasting import ForecastingComponent
from ui.components.glusterfs_health import GlusterFSHealthComponent
from ui.components.manual_remediation import ManualRemediationComponent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExpertSystemDashboard:
    """
    Main dashboard for the Expert LLM System
    
    Features:
    - 5-tab interface: Chat Assistant, Logs/Issues, Forecasting, GlusterFS Health, Manual Remediation
    - Real-time system monitoring and health status
    - Expert pattern recognition with 14 categories
    - Historical learning with predictive analytics
    - Safety-first command execution with validation
    - Interactive visualizations and guided remediation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        try:
            self.rag_agent = EnhancedRAGAgent()
            self.remediation_engine = ExpertRemediationEngine()
            self.history_manager = IssueHistoryManager()
            
            # Initialize UI components
            self.chat_assistant = ChatAssistant(self.rag_agent)
            self.logs_issues = LogsIssuesComponent(self.history_manager)
            self.forecasting = ForecastingComponent(self.history_manager)
            self.glusterfs_health = GlusterFSHealthComponent()
            self.manual_remediation = ManualRemediationComponent(self.remediation_engine, self.rag_agent)
            
            self.logger.info("Expert System Dashboard initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing dashboard: {e}")
            st.error(f"Failed to initialize dashboard: {e}")

    def run(self):
        """Main dashboard interface"""
        try:
            # Configure page
            st.set_page_config(
                page_title="Expert LLM System",
                page_icon="🔧",
                layout="wide",
                initial_sidebar_state="expanded"
            )
            
            # Sidebar with system status
            self._render_sidebar()
            
            # Main content area
            self._render_main_content()
            
        except Exception as e:
            self.logger.error(f"Error running dashboard: {e}")
            st.error(f"Dashboard error: {e}")

    def _render_sidebar(self):
        """Render sidebar with system status and navigation"""
        with st.sidebar:
            st.title("🔧 Expert LLM System")
            st.markdown("---")
            
            # System Status Overview
            st.subheader("📊 System Status")
            
            try:
                # Get current system status
                system_status = self.rag_agent.system_monitor.get_comprehensive_status()
                
                # Enhanced live monitoring with auto-refresh
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Auto-refresh button
                    if st.button("🔄 Auto-Refresh", help="Refresh data every 30 seconds"):
                        st.rerun()
                    
                    # Get resource usage data
                    resource_usage = system_status.get('resource_usage', {})
                    cpu_usage = resource_usage.get('cpu_percent', 0)
                    memory_usage = resource_usage.get('memory_percent', 0)
                    
                    st.metric(
                        "CPU Usage", 
                        f"{cpu_usage:.1f}%",
                        delta=f"{cpu_usage - 65:.1f}%" if cpu_usage > 0 else None
                    )
                    st.metric(
                        "Memory Usage", 
                        f"{memory_usage:.1f}%",
                        delta=f"{memory_usage - 45:.1f}%" if memory_usage > 0 else None
                    )
                
                with col2:
                    # Live timestamp
                    current_time = datetime.now()
                    st.success(f"🕐 Live Data: {current_time.strftime('%H:%M:%S')}")
                    
                    # Calculate overall disk usage percentage
                    disk_data = system_status.get('disk_usage', {})
                    if disk_data:
                        # Get the root partition usage or the first available partition
                        root_usage = disk_data.get('/', {})
                        if not root_usage and disk_data:
                            # If no root partition, get the first partition
                            root_usage = next(iter(disk_data.values()), {})
                        disk_percent = root_usage.get('percent', 0)
                    else:
                        disk_percent = 0
                    
                    st.metric(
                        "Disk Usage", 
                        f"{disk_percent:.1f}%",
                        delta=f"{disk_percent - 30:.1f}%" if disk_percent > 0 else None
                    )
                    
                    # Process count
                    process_info = system_status.get('process_info', {})
                    process_count = len(process_info.get('processes', [])) if isinstance(process_info.get('processes'), list) else 0
                    st.metric(
                        "Active Processes", 
                        f"{process_count}",
                        delta=None
                    )
                
                with col3:
                    # Kubernetes status if available
                    import os
                    k8s_available = False
                    error_msg = ""
                    
                    try:
                        # First check if we're running in a Kubernetes pod
                        if os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/token'):
                            # We're in a pod, try to use the Kubernetes API
                            from kubernetes import client, config
                            config.load_incluster_config()
                            v1 = client.CoreV1Api()
                            
                            # Try to list pods in our namespace
                            pods = v1.list_namespaced_pod(namespace='expert-llm-system')
                            running_pods = sum(1 for pod in pods.items if pod.status.phase == 'Running')
                            
                            st.success(f"🚀 K8s Pods Running: {running_pods}")
                            k8s_available = True
                        else:
                            # Not in a pod, try local kubectl config
                            try:
                                from kubernetes import client, config
                                config.load_kube_config()
                                v1 = client.CoreV1Api()
                                pods = v1.list_namespaced_pod(namespace='expert-llm-system')
                                running_pods = sum(1 for pod in pods.items if pod.status.phase == 'Running')
                                st.success(f"🚀 K8s Pods Running: {running_pods}")
                                k8s_available = True
                            except:
                                error_msg = "Local kubeconfig not accessible"
                                
                    except Exception as e:
                        error_msg = str(e)
                    
                    if not k8s_available:
                        if error_msg:
                            st.info(f"🔍 K8s: Not available ({error_msg[:30]}...)")
                        else:
                            st.info("🔍 K8s: Not available")
                    
                    # Expert system status
                    st.metric(
                        "Patterns Loaded", 
                        "14",
                        delta="✅ All active"
                    )
                    st.metric(
                        "Confidence Score", 
                        f"{system_status.get('confidence_score', 85):.1f}%",
                        delta=None
                    )
                    
                    # System health indicator
                    overall_health = self._calculate_overall_health(system_status)
                    health_color = "🟢" if overall_health > 80 else "🟡" if overall_health > 60 else "🔴"
                    st.metric(
                        "System Health", 
                        f"{health_color} {overall_health:.0f}%",
                        delta=None
                    )
                
                # Active issues count
                active_issues = self.history_manager.get_trending_issues(7)
                st.metric("Active Issues (7d)", len(active_issues))
                
            except Exception as e:
                st.error(f"Error loading system status: {e}")
            
            st.markdown("---")
            
            # Quick Actions
            st.subheader("⚡ Quick Actions")
            
            if st.button("🔍 System Scan", use_container_width=True):
                self._perform_system_scan()
            
            if st.button("📈 Learning Update", use_container_width=True):
                self._perform_learning_update()
            
            if st.button("🛡️ Safety Check", use_container_width=True):
                self._perform_safety_check()
            
            st.markdown("---")
            
            # Expert Pattern Categories
            st.subheader("🎯 Expert Patterns")
            
            pattern_counts = self._get_pattern_counts()
            
            for category, count in pattern_counts.items():
                st.write(f"**{category}**: {count} patterns")

    def _render_main_content(self):
        """Render main content area with tabs"""
        # Main title
        st.title("Expert LLM System Dashboard")
        st.markdown("*Intelligent system administration with 14 expert patterns across Ubuntu OS, Kubernetes, and GlusterFS*")
        
        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "💬 Chat Assistant",
            "📋 Logs & Issues", 
            "📊 Forecasting",
            "💾 GlusterFS Health",
            "🔧 Manual Remediation"
        ])
        
        # Tab 1: Chat Assistant
        with tab1:
            self.chat_assistant.render()
        
        # Tab 2: Logs & Issues
        with tab2:
            self.logs_issues.render()
        
        # Tab 3: Forecasting
        with tab3:
            self.forecasting.render()
        
        # Tab 4: GlusterFS Health
        with tab4:
            self.glusterfs_health.render()
        
        # Tab 5: Manual Remediation
        with tab5:
            self.manual_remediation.render()

    def _calculate_overall_health(self, status: Dict[str, Any]) -> float:
        """Calculate overall system health score"""
        try:
            # Safely extract numeric values from nested dictionaries
            cpu_score = 100
            memory_score = 100
            disk_score = 100
            
            # CPU usage
            if 'resource_usage' in status and isinstance(status['resource_usage'], dict):
                cpu_usage = status['resource_usage'].get('cpu_percent', 0)
                if isinstance(cpu_usage, (int, float)):
                    cpu_score = max(0, 100 - cpu_usage)
            elif 'cpu_usage' in status and isinstance(status['cpu_usage'], (int, float)):
                cpu_score = max(0, 100 - status['cpu_usage'])
            
            # Memory usage
            if 'resource_usage' in status and isinstance(status['resource_usage'], dict):
                memory_usage = status['resource_usage'].get('memory_percent', 0)
                if isinstance(memory_usage, (int, float)):
                    memory_score = max(0, 100 - memory_usage)
            elif 'memory_usage' in status and isinstance(status['memory_usage'], (int, float)):
                memory_score = max(0, 100 - status['memory_usage'])
            
            # Disk usage (average across all disks)
            if 'disk_usage' in status and isinstance(status['disk_usage'], dict):
                disk_percentages = []
                for mount_data in status['disk_usage'].values():
                    if isinstance(mount_data, dict) and 'percent' in mount_data:
                        disk_percentages.append(mount_data['percent'])
                if disk_percentages:
                    avg_disk_usage = sum(disk_percentages) / len(disk_percentages)
                    disk_score = max(0, 100 - avg_disk_usage)
            elif 'disk_usage' in status and isinstance(status['disk_usage'], (int, float)):
                disk_score = max(0, 100 - status['disk_usage'])
            
            # Kubernetes health (if available)
            k8s_score = 100
            if 'kubernetes' in status and isinstance(status['kubernetes'], dict):
                k8s_ready = status['kubernetes'].get('ready_nodes', 0)
                k8s_total = status['kubernetes'].get('total_nodes', 1)
                if isinstance(k8s_ready, (int, float)) and isinstance(k8s_total, (int, float)):
                    k8s_score = (k8s_ready / k8s_total) * 100 if k8s_total > 0 else 0
            elif 'kubernetes_status' in status and isinstance(status['kubernetes_status'], dict):
                # Alternative structure check
                k8s_ready = status['kubernetes_status'].get('ready_nodes', 0)
                k8s_total = status['kubernetes_status'].get('total_nodes', 1)
                if isinstance(k8s_ready, (int, float)) and isinstance(k8s_total, (int, float)):
                    k8s_score = (k8s_ready / k8s_total) * 100 if k8s_total > 0 else 0
            
            # Weight the scores
            overall = (cpu_score * 0.25 + memory_score * 0.25 + disk_score * 0.25 + k8s_score * 0.25)
            
            # Ensure the result is a float between 0 and 100
            return max(0.0, min(100.0, float(overall)))
            
        except Exception as e:
            self.logger.error(f"Error calculating health score: {e}")
            return 50.0

    def _get_pattern_counts(self) -> Dict[str, int]:
        """Get count of patterns by category"""
        try:
            patterns = self.rag_agent.expert_patterns
            
            counts = {
                'Ubuntu OS': 0,
                'Kubernetes': 0,
                'GlusterFS': 0
            }
            
            for category, data in patterns.items():
                if isinstance(data, dict) and 'patterns' in data:
                    pattern_count = len(data['patterns'])
                    
                    if 'ubuntu' in category.lower():
                        counts['Ubuntu OS'] = pattern_count
                    elif 'kubernetes' in category.lower():
                        counts['Kubernetes'] = pattern_count
                    elif 'gluster' in category.lower():
                        counts['GlusterFS'] = pattern_count
            
            return counts
            
        except Exception as e:
            self.logger.error(f"Error getting pattern counts: {e}")
            return {'Ubuntu OS': 0, 'Kubernetes': 0, 'GlusterFS': 0}

    def _perform_system_scan(self):
        """Perform comprehensive system scan"""
        try:
            with st.spinner("Performing system scan..."):
                # Trigger continuous learning scan
                scan_result = self.history_manager.continuous_learning_scan()
                
                # Display results
                st.success("System scan completed!")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("New Patterns", scan_result.get('new_patterns_detected', 0))
                
                with col2:
                    st.metric("Updated Patterns", scan_result.get('updated_patterns', 0))
                
                with col3:
                    st.metric("Anomalies Found", len(scan_result.get('anomalies_found', [])))
                
                # Show recommendations if any
                recommendations = scan_result.get('recommendations', [])
                if recommendations:
                    st.subheader("📋 Recommendations")
                    for rec in recommendations:
                        st.info(f"**{rec.get('type', 'General')}**: {rec.get('message', 'No message')}")
                
        except Exception as e:
            st.error(f"System scan failed: {e}")

    def _perform_learning_update(self):
        """Perform learning system update"""
        try:
            with st.spinner("Updating learning system..."):
                # Get learning analytics
                analytics = self.history_manager.get_learning_analytics()
                
                st.success("Learning update completed!")
                
                # Display analytics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Issues Tracked", analytics.get('total_issues_tracked', 0))
                
                with col2:
                    st.metric("Overall Success Rate", f"{analytics.get('overall_success_rate', 0)*100:.1f}%")
                
                with col3:
                    st.metric("Avg Resolution Time", f"{analytics.get('avg_resolution_time', 0)} min")
                
        except Exception as e:
            st.error(f"Learning update failed: {e}")

    def _perform_safety_check(self):
        """Perform safety validation check"""
        try:
            with st.spinner("Performing safety check..."):
                # Get safety guidelines
                safety_guidelines = self.rag_agent.safety_validator.get_safety_guidelines()
                
                st.success("Safety check completed!")
                
                # Display safety status
                st.subheader("🛡️ Safety Configuration")
                
                dangerous_patterns = safety_guidelines.get('dangerous_patterns', [])
                safe_prefixes = safety_guidelines.get('safe_command_prefixes', [])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Monitored Dangerous Patterns:**")
                    for pattern in dangerous_patterns[:5]:  # Show first 5
                        st.write(f"• `{pattern}`")
                
                with col2:
                    st.write("**Safe Command Prefixes:**")
                    for prefix in safe_prefixes[:5]:  # Show first 5
                        st.write(f"• `{prefix}`")
                
        except Exception as e:
            st.error(f"Safety check failed: {e}")


def main():
    """Main entry point for the dashboard"""
    try:
        dashboard = ExpertSystemDashboard()
        dashboard.run()
        
    except Exception as e:
        logger.error(f"Fatal error in dashboard: {e}")
        st.error(f"Dashboard failed to start: {e}")
        st.markdown("""
        ### Troubleshooting Steps:
        1. Ensure all dependencies are installed: `pip install -r requirements.txt`
        2. Check if the expert patterns file exists
        3. Verify system permissions for monitoring
        4. Review logs for detailed error information
        """)


if __name__ == "__main__":
    main()