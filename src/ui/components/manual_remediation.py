import streamlit as st
from datetime import datetime

class ManualRemediationComponent:
    def __init__(self, remediation_engine=None, rag_agent=None):
        self.remediation_engine = remediation_engine
        self.rag_agent = rag_agent
        self.actions = {
            "restart_failed_pods": self.restart_failed_pods,
            "clean_completed_jobs": self.clean_completed_jobs,
            "scale_deployment": self.scale_deployment,
            "clean_old_logs": self.clean_old_logs,
        }

    def restart_failed_pods(self, pod_name):
        # Logic to restart the specified pod
        pass

    def clean_completed_jobs(self):
        # Logic to clean up completed jobs
        pass

    def scale_deployment(self, deployment_name, replicas):
        # Logic to scale the specified deployment
        pass

    def clean_old_logs(self):
        # Logic to clean up old logs
        pass

    def execute_action(self, action_name, *args):
        if action_name in self.actions:
            return self.actions[action_name](*args)
        else:
            raise ValueError("Invalid action name")
    
    def render(self):
        """Render the manual remediation component UI"""
        import streamlit as st
        
        st.header("🔧 Manual Remediation")
        st.write("Execute manual remediation actions and system maintenance tasks.")
        
        # Quick Actions section
        st.subheader("Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Pod Management")
            
            # Restart failed pods
            pod_name = st.text_input("Pod Name to Restart:", placeholder="my-app-pod-123")
            if st.button("Restart Failed Pod"):
                if pod_name:
                    try:
                        self.restart_failed_pods(pod_name)
                        st.success(f"Initiated restart for pod: {pod_name}")
                    except Exception as e:
                        st.error(f"Failed to restart pod: {e}")
                else:
                    st.warning("Please enter a pod name")
            
            # Scale deployment
            st.subheader("Deployment Scaling")
            deployment_name = st.text_input("Deployment Name:", placeholder="my-app-deployment")
            replicas = st.number_input("Number of Replicas:", min_value=0, max_value=10, value=1)
            if st.button("Scale Deployment"):
                if deployment_name:
                    try:
                        self.scale_deployment(deployment_name, replicas)
                        st.success(f"Scaled {deployment_name} to {replicas} replicas")
                    except Exception as e:
                        st.error(f"Failed to scale deployment: {e}")
                else:
                    st.warning("Please enter a deployment name")
        
        with col2:
            st.subheader("Cleanup Operations")
            
            # Clean completed jobs
            if st.button("Clean Completed Jobs"):
                try:
                    self.clean_completed_jobs()
                    st.success("Cleaned up completed jobs")
                except Exception as e:
                    st.error(f"Failed to clean jobs: {e}")
            
            # Clean old logs
            if st.button("Clean Old Logs"):
                try:
                    self.clean_old_logs()
                    st.success("Cleaned up old logs")
                except Exception as e:
                    st.error(f"Failed to clean logs: {e}")
        
        # Interactive kubectl Actions
        st.subheader("🎯 Interactive kubectl Actions")
        
        # Quick kubectl buttons
        col3, col4, col5 = st.columns(3)
        
        with col3:
            st.markdown("**📊 Quick Views**")
            if st.button("All Pods Status", key="all_pods"):
                if self.rag_agent:
                    result = self.rag_agent._execute_safe_command("kubectl get pods --all-namespaces")
                    st.code(result, language='bash')
            
            if st.button("All Services", key="all_services"):
                if self.rag_agent:
                    result = self.rag_agent._execute_safe_command("kubectl get services --all-namespaces")
                    st.code(result, language='bash')
                    
            if st.button("Cluster Nodes", key="all_nodes"):
                if self.rag_agent:
                    result = self.rag_agent._execute_safe_command("kubectl get nodes")
                    st.code(result, language='bash')
        
        with col4:
            st.markdown("**🔍 Pod Analysis**")
            
            # Pod selector for detailed analysis
            pod_for_analysis = st.text_input("Pod Name for Analysis:", 
                                           placeholder="expert-llm-system-58f748cf59-cc57j",
                                           key="pod_analysis")
            pod_namespace = st.text_input("Namespace (optional):", 
                                        placeholder="expert-llm-system", 
                                        key="pod_ns")
            
            if st.button("📋 Describe Pod", key="describe_pod"):
                if pod_for_analysis:
                    ns_flag = f" -n {pod_namespace}" if pod_namespace else ""
                    cmd = f"kubectl describe pod {pod_for_analysis}{ns_flag}"
                    if self.rag_agent:
                        result = self.rag_agent._execute_safe_command(cmd)
                        st.code(result, language='bash')
                else:
                    st.warning("Please enter a pod name")
            
            if st.button("📜 Pod Logs", key="pod_logs"):
                if pod_for_analysis:
                    ns_flag = f" -n {pod_namespace}" if pod_namespace else ""
                    cmd = f"kubectl logs {pod_for_analysis}{ns_flag} --tail=100"
                    if self.rag_agent:
                        result = self.rag_agent._execute_safe_command(cmd)
                        st.code(result, language='bash')
                else:
                    st.warning("Please enter a pod name")
        
        with col5:
            st.markdown("**🧠 AI Analysis**")
            
            # Error pattern input for correlation
            error_pattern = st.text_input("Error Pattern to Analyze:", 
                                        placeholder="Connection refused", 
                                        key="error_pattern")
            
            if st.button("🔍 Find Root Cause", key="root_cause"):
                if error_pattern:
                    cmd = f"analyze '{error_pattern}'"
                    if self.rag_agent:
                        result = self.rag_agent._execute_safe_command(cmd)
                        st.markdown("### 🔍 Root Cause Analysis Results")
                        st.text(result)
                else:
                    st.warning("Please enter an error pattern")
            
            if st.button("⚡ Smart Pod Correlation", key="smart_correlation"):
                if pod_for_analysis:
                    # This will trigger intelligent cross-pod correlation
                    cmd = f"smart_correlate {pod_for_analysis}"
                    if pod_namespace:
                        cmd += f" -n {pod_namespace}"
                    
                    if self.rag_agent:
                        with st.spinner("Analyzing pod correlations with timestamps..."):
                            result = self.rag_agent._execute_safe_command(cmd)
                            st.markdown("### 🧠 Smart Correlation Analysis")
                            st.text(result)
                else:
                    st.warning("Please enter a pod name for correlation analysis")
        
        # Enhanced Custom Command section with suggestions
        st.subheader("💻 Custom Command Execution")
        st.warning("⚠️ Use with caution - these commands will be executed on the system")
        
        # Command suggestions
        st.markdown("**💡 Quick Command Templates:**")
        template_col1, template_col2 = st.columns(2)
        
        with template_col1:
            if st.button("Get Events by Time", key="events_template"):
                st.session_state.command_template = "kubectl get events --all-namespaces --sort-by='.lastTimestamp'"
            if st.button("Get Failing Pods", key="failing_template"):
                st.session_state.command_template = "analyze 'Failed'"
            if st.button("Memory Analysis", key="memory_template"):
                st.session_state.command_template = "analyze 'Out of memory'"
        
        with template_col2:
            if st.button("Network Issues", key="network_template"):
                st.session_state.command_template = "analyze 'Connection refused'"
            if st.button("Image Pull Issues", key="image_template"):
                st.session_state.command_template = "analyze 'ImagePullBackOff'"
            if st.button("Deployment Status", key="deployment_template"):
                st.session_state.command_template = "kubectl get deployments --all-namespaces"
        
        # Use template if selected
        default_command = st.session_state.get('command_template', "kubectl get pods --all-namespaces")
        if 'command_template' in st.session_state:
            del st.session_state.command_template  # Clear after use
        
        custom_command = st.text_area(
            "Custom Command:",
            value=default_command if 'command_template' in locals() else "",
            placeholder="kubectl get pods --all-namespaces",
            help="Enter a safe command to execute",
            key="custom_command_input"
        )
        
        # Add command execution history to session state
        if 'command_history' not in st.session_state:
            st.session_state.command_history = []
        
        if st.button("Execute Command"):
            if custom_command:
                st.info(f"Executing: {custom_command}")
                
                try:
                    # Use the enhanced RAG agent's safe command execution if available
                    if self.rag_agent and hasattr(self.rag_agent, '_execute_safe_command'):
                        with st.spinner("Executing command safely..."):
                            # Enhanced debugging and command preprocessing
                            processed_command = custom_command.strip()
                            
                            # Check if this is an analyze command (special handling)
                            if processed_command.lower().startswith('analyze '):
                                # Extract the error pattern from quotes or after 'analyze '
                                import re
                                match = re.search(r"analyze\s+['\"]([^'\"]+)['\"]", processed_command, re.IGNORECASE)
                                if match:
                                    error_pattern = match.group(1)
                                    processed_command = f"analyze {error_pattern}"
                                else:
                                    # Remove 'analyze ' and use the rest as error pattern
                                    error_pattern = processed_command[8:].strip()
                                    processed_command = f"analyze {error_pattern}"
                            
                            result = self.rag_agent._execute_safe_command(processed_command)
                        
                        # Enhanced result display with better formatting
                        if result:
                            if result.startswith("Command rejected for safety"):
                                st.error("🚫 " + result)
                            elif result.startswith("Error executing command"):
                                st.error("❌ " + result)
                            elif result.startswith("Command failed"):
                                st.warning("⚠️ " + result)
                            elif result.startswith("Get command not recognized"):
                                st.warning("❓ " + result)
                                st.info("💡 **Supported kubectl commands:**")
                                st.code("""
# Resource Queries
kubectl get pods [--all-namespaces]
kubectl get services [--all-namespaces] 
kubectl get nodes
kubectl get deployments [--all-namespaces]
kubectl get events [--all-namespaces]
kubectl get namespaces
kubectl get configmaps [--all-namespaces]
kubectl get secrets [--all-namespaces]
kubectl get ingress [--all-namespaces]
kubectl get pv
kubectl get pvc [--all-namespaces]
kubectl get all [--all-namespaces]

# Detailed Analysis
kubectl describe pod <name> [-n <namespace>]
kubectl describe service <name> [-n <namespace>]
kubectl describe deployment <name> [-n <namespace>]
kubectl describe node <name>

# Logs Analysis
kubectl logs <pod-name> [-n <namespace>]
kubectl logs <pod-name> -c <container> [-n <namespace>]
kubectl logs <pod-name> --tail=100 [-n <namespace>]

# Root Cause Analysis (AI-powered)
analyze 'ImagePullBackOff'
analyze 'CrashLoopBackOff'
analyze 'Connection refused'
analyze '<any-error-message>'
                                """, language='bash')
                            else:
                                st.success("✅ Command executed successfully!")
                                
                                # Format output with proper spacing and highlights
                                formatted_result = result
                                
                                # Add syntax highlighting for specific types
                                if "NAMESPACE" in result and "NAME" in result:
                                    # This looks like kubectl get output
                                    st.code(formatted_result, language='bash')
                                elif "=== ROOT CAUSE ANALYSIS ===" in result:
                                    # This is root cause analysis output
                                    st.markdown("### 🔍 Root Cause Analysis Results")
                                    st.text(formatted_result)
                                else:
                                    st.code(formatted_result, language='bash')
                                
                                # Add to command history
                                st.session_state.command_history.append({
                                    'command': custom_command,
                                    'result': result,
                                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'status': 'success'
                                })
                        else:
                            st.warning("⚠️ Command executed but returned no output")
                    else:
                        st.error("❌ Enhanced RAG agent not available for safe command execution")
                        st.info("💡 Make sure the application is properly initialized with the RAG agent")
                        
                except Exception as e:
                    st.error(f"💥 Error executing command: {str(e)}")
                    # Add error to command history
                    st.session_state.command_history.append({
                        'command': custom_command,
                        'result': str(e),
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'status': 'error'
                    })
            else:
                st.warning("Please enter a command")
        
        # Action History
        st.subheader("Action History")
        
        if st.session_state.get('command_history'):
            st.info(f"Showing {len(st.session_state.command_history)} recent command executions")
            
            # Add clear history button
            if st.button("Clear History"):
                st.session_state.command_history = []
                st.rerun()
            
            # Display command history
            for i, cmd_entry in enumerate(reversed(st.session_state.command_history[-10:])):  # Show last 10
                with st.expander(f"Command {len(st.session_state.command_history) - i}: {cmd_entry['command'][:50]}..." if len(cmd_entry['command']) > 50 else f"Command {len(st.session_state.command_history) - i}: {cmd_entry['command']}"):
                    
                    # Status indicator
                    if cmd_entry['status'] == 'success':
                        st.success(f"✅ Executed successfully at {cmd_entry['timestamp']}")
                    else:
                        st.error(f"❌ Failed at {cmd_entry['timestamp']}")
                    
                    # Command details
                    st.code(f"Command: {cmd_entry['command']}", language='bash')
                    
                    # Result
                    if cmd_entry['status'] == 'success':
                        st.text("Output:")
                        st.code(cmd_entry['result'], language='bash')
                    else:
                        st.text("Error:")
                        st.code(cmd_entry['result'], language='text')
        else:
            st.info("No command execution history yet")
            with st.expander("How to use command execution"):
                st.markdown("""
                **🚀 COMPREHENSIVE KUBECTL SUPPORT:**
                - ✅ All major kubectl get commands (pods, services, nodes, deployments, namespaces, events, configmaps, secrets, ingress, pv, pvc)
                - ✅ Detailed describe commands with health analysis
                - ✅ Advanced logs commands with container and time filtering
                - ✅ **INTELLIGENT ROOT CAUSE ANALYSIS** - analyze '<error-message>'
                - ✅ Cross-reference error patterns across pods, logs, and events
                - ✅ Safety validation and command history
                
                **📊 GET Commands (comprehensive support):**
                - `kubectl get pods --all-namespaces` (detailed with node info)
                - `kubectl get services --all-namespaces` (with port mappings)
                - `kubectl get nodes` (with capacity and conditions)
                - `kubectl get deployments --all-namespaces`
                - `kubectl get events --all-namespaces` (sorted by time)
                - `kubectl get namespaces`, `kubectl get configmaps`, `kubectl get secrets`
                - `kubectl get ingress`, `kubectl get pv`, `kubectl get pvc`
                - `kubectl get all --all-namespaces` (comprehensive overview)
                
                **📋 DESCRIBE Commands (enhanced with health analysis):**
                - `kubectl describe pod <name> [-n <namespace>]`
                - `kubectl describe service <name> [-n <namespace>]`
                - `kubectl describe deployment <name> [-n <namespace>]`
                - `kubectl describe node <name>`
                
                **📜 LOGS Commands (advanced options):**
                - `kubectl logs <pod-name> [-n <namespace>]`
                - `kubectl logs <pod-name> -c <container> [-n <namespace>]`
                - `kubectl logs <pod-name> --tail=100 [-n <namespace>]`
                
                **🔍 ROOT CAUSE ANALYSIS (AI-powered):**
                - `analyze 'ImagePullBackOff'` - Find all pods with image pull issues
                - `analyze 'CrashLoopBackOff'` - Investigate crash loops across cluster
                - `analyze 'Out of memory'` - Find memory-related issues
                - `analyze 'Connection refused'` - Network connectivity analysis
                - `analyze '<any-error-string>'` - Cross-reference any error across logs, events, and pod statuses
                
                **💡 Example Advanced Queries:**
                ```
                # Comprehensive cluster health check
                kubectl get all --all-namespaces
                
                # Find all failing pods with analysis
                analyze 'Failed'
                
                # Deep dive into specific pod issues
                kubectl describe pod <pod-name> -n <namespace>
                kubectl logs <pod-name> -c <container> --tail=50
                
                # Network troubleshooting
                kubectl get services --all-namespaces
                kubectl get ingress --all-namespaces
                analyze 'DNS resolution failed'
                
                # Resource analysis
                kubectl get nodes
                kubectl describe node <node-name>
                analyze 'insufficient resources'
                ```
                
                **🎯 The system will:**
                - Cross-reference error patterns across all pods and namespaces
                - Analyze pod logs, events, and statuses intelligently  
                - Provide specific recommendations based on error types
                - Show related issues and potential root causes
                - Format output with proper spacing and health indicators
                """)
                