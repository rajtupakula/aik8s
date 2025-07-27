"""
Enhanced RAG Agent - Expert query processing and intelligent action detection
"""

import logging
import json
import re
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
import yaml
import ollama

from .expert_remediation_engine import ExpertRemediationEngine
from .issue_history_manager import IssueHistoryManager
from .utils import SafetyValidator, SystemMonitor

class EnhancedRAGAgent:
    """
    Enhanced RAG (Retrieval-Augmented Generation) Agent for expert system interaction
    
    Features:
    - Expert query processing with context awareness
    - Intelligent action detection from conversational input
    - Integration with 14 expert patterns across Ubuntu OS, Kubernetes, and GlusterFS
    - Historical learning integration for improved responses
    - Safety-first command execution with validation
    - Real-time system context integration
    """
    
    def __init__(self, model_name: str = "expert-llm", patterns_file: str = None):
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        
        # Set Ollama base URL from environment or use default
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        
        # Initialize components
        self.remediation_engine = ExpertRemediationEngine(patterns_file)
        self.history_manager = IssueHistoryManager()
        self.safety_validator = SafetyValidator()
        self.system_monitor = SystemMonitor()
        
        # Load expert patterns for context
        self.expert_patterns = self._load_expert_patterns(patterns_file)
        
        # Initialize conversation context
        self.conversation_context = {
            'system_status': {},
            'active_issues': [],
            'user_preferences': {},
            'session_history': []
        }
        
        # Action detection patterns
        self.action_patterns = {
            'diagnostic': [
                r'check|diagnose|status|health|monitor',
                r'what.*wrong|problem|issue|error',
                r'show.*logs|display.*info'
            ],
            'remediation': [
                r'fix|resolve|repair|solve',
                r'restart|reload|reset',
                r'install|update|upgrade'
            ],
            'preventive': [
                r'prevent|avoid|protect',
                r'backup|snapshot|save',
                r'monitor|watch|alert'
            ],
            'informational': [
                r'how.*work|explain|describe',
                r'what.*is|tell.*about',
                r'help|guide|tutorial'
            ]
        }
        
        self.logger.info(f"Enhanced RAG Agent initialized with model: {model_name}")

    def _load_expert_patterns(self, patterns_file: str = None) -> Dict[str, Any]:
        """Load expert patterns for context"""
        try:
            if patterns_file is None:
                import os
                patterns_file = os.path.join(os.path.dirname(__file__), '../data/expert_patterns.yaml')
            
            with open(patterns_file, 'r') as f:
                patterns = yaml.safe_load(f)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error loading expert patterns: {e}")
            return {}

    def expert_query(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process user query with expert context and intelligent action detection
        
        Args:
            user_query: The user's natural language query
            context: Additional context information
            
        Returns:
            Comprehensive response with actions, recommendations, and context
        """
        try:
            # Update system context
            self._update_system_context()
            
            # Detect query intent and actions
            query_analysis = self._analyze_query(user_query)
            
            # Generate expert response
            response = self._generate_expert_response(user_query, query_analysis, context)
            
            # Update conversation history
            self._update_conversation_history(user_query, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                'response': "I apologize, but I encountered an error processing your query. Please try rephrasing your question.",
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    def detect_actions(self, query: str) -> List[Dict[str, Any]]:
        """Analyze user query for intent and actionable items"""
        analysis = self._analyze_query(query)
        
        actions = []
        
        # Convert analysis to actionable items
        for issue in analysis.get('potential_issues', []):
            actions.append({
                'type': 'diagnostic',
                'category': issue['category'],
                'pattern': issue['pattern'],
                'confidence': issue['confidence'],
                'urgency': analysis['urgency_level']
            })
        
        # Add intent-based actions
        if analysis['intent'] == 'remediation':
            actions.append({
                'type': 'remediation',
                'systems': analysis['detected_systems'],
                'requires_validation': analysis['requires_validation'],
                'urgency': analysis['urgency_level']
            })
        
        return actions

    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze user query for intent and actionable items"""
        analysis = {
            'intent': 'informational',
            'confidence': 0.0,
            'detected_systems': [],
            'potential_issues': [],
            'suggested_actions': [],
            'urgency_level': 'low',
            'requires_validation': False,
            'kubectl_command': None  # New field for kubectl commands
        }
        
        try:
            query_lower = query.lower()
            
            # Enhanced kubectl command detection
            kubectl_patterns = {
                'logs': [
                    r'check.*logs?.*(?:of|for|in)\s+([a-z0-9-]+)',
                    r'(?:show|get).*logs?.*(?:of|for|from)\s+(?:pod\s+)?([a-z0-9-]+)',
                    r'errors?.*logs?.*(?:of|for|from)\s+([a-z0-9-]+)',
                    r'(?:view|see).*logs?.*(?:of|for|from)\s+([a-z0-9-]+)'
                ],
                'describe': [
                    r'describe.*pod\s+([a-z0-9-]+)',
                    r'(?:status|details|info).*(?:of|for|about)\s+(?:pod\s+)?([a-z0-9-]+)',
                    r'what.*(?:status|condition).*([a-z0-9-]+)'
                ],
                'get': [
                    r'list.*pods?',
                    r'show.*pods?',
                    r'get.*pods?',
                    r'all.*pods?'
                ]
            }
            
            # Check for kubectl patterns and extract pod names
            for cmd_type, patterns in kubectl_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, query_lower)
                    if match:
                        analysis['intent'] = 'kubectl_command'
                        analysis['confidence'] = 0.9
                        
                        if cmd_type == 'logs':
                            pod_name = match.group(1)
                            # Try to detect namespace
                            namespace_match = re.search(r'namespace\s+([a-z0-9-]+)', query_lower)
                            namespace = namespace_match.group(1) if namespace_match else 'expert-llm-system'
                            
                            analysis['kubectl_command'] = {
                                'type': 'logs',
                                'pod': pod_name,
                                'namespace': namespace,
                                'command': f'kubectl logs {pod_name} -n {namespace} --tail=50'
                            }
                        elif cmd_type == 'describe':
                            pod_name = match.group(1)
                            namespace_match = re.search(r'namespace\s+([a-z0-9-]+)', query_lower)
                            namespace = namespace_match.group(1) if namespace_match else 'expert-llm-system'
                            
                            analysis['kubectl_command'] = {
                                'type': 'describe',
                                'pod': pod_name,
                                'namespace': namespace,
                                'command': f'kubectl describe pod {pod_name} -n {namespace}'
                            }
                        elif cmd_type == 'get':
                            analysis['kubectl_command'] = {
                                'type': 'get',
                                'resource': 'pods',
                                'command': 'kubectl get pods --all-namespaces'
                            }
                        break
                
                if analysis['kubectl_command']:
                    break
            
            # Detect intent (keep existing logic)
            if not analysis['kubectl_command']:  # Only if not already kubectl command
                for intent_type, patterns in self.action_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, query_lower):
                            analysis['intent'] = intent_type
                            analysis['confidence'] = 0.8
                            break
            
            # Detect mentioned systems
            if any(keyword in query_lower for keyword in ['ubuntu', 'linux', 'os', 'system']):
                analysis['detected_systems'].append('ubuntu_os')
            
            if any(keyword in query_lower for keyword in ['kubernetes', 'k8s', 'pod', 'container']):
                analysis['detected_systems'].append('kubernetes')
            
            if any(keyword in query_lower for keyword in ['gluster', 'storage', 'volume', 'filesystem']):
                analysis['detected_systems'].append('glusterfs')
            
            # Detect potential issues from patterns
            for category, patterns in self.expert_patterns.items():
                if isinstance(patterns, dict) and 'patterns' in patterns:
                    for pattern_name, pattern_data in patterns['patterns'].items():
                        keywords = pattern_data.get('detection', {}).get('keywords', [])
                        
                        if any(keyword.lower() in query_lower for keyword in keywords):
                            analysis['potential_issues'].append({
                                'category': category,
                                'pattern': pattern_name,
                                'confidence': 0.7
                            })
            
            # Determine urgency
            urgent_keywords = ['critical', 'urgent', 'emergency', 'down', 'failed', 'crashed']
            if any(keyword in query_lower for keyword in urgent_keywords):
                analysis['urgency_level'] = 'high'
            elif any(keyword in query_lower for keyword in ['warning', 'issue', 'problem']):
                analysis['urgency_level'] = 'medium'
            
            # Check if validation required
            dangerous_keywords = ['delete', 'remove', 'destroy', 'format', 'rm ', 'kill']
            if any(keyword in query_lower for keyword in dangerous_keywords):
                analysis['requires_validation'] = True
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing query: {e}")
            return analysis

    def generate_response(self, actions: List[Dict[str, Any]]) -> str:
        """Generate context-aware responses based on detected actions"""
        if not actions:
            return "I understand your query. Could you provide more specific details about what you'd like me to help you with?"
        
        response_parts = []
        
        for action in actions:
            if action['type'] == 'diagnostic':
                response_parts.append(f"I can help diagnose {action['category']} issues related to {action['pattern']}.")
            elif action['type'] == 'remediation':
                response_parts.append(f"I can assist with remediation for {', '.join(action['systems'])} systems.")
            
        return " ".join(response_parts)

    def _generate_expert_response(self, query: str, analysis: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate expert response using RAG approach"""
        try:
            # Handle kubectl commands directly
            if analysis.get('kubectl_command'):
                return self._handle_kubectl_query(analysis['kubectl_command'], query)
            
            # Prepare context for LLM
            expert_context = self._prepare_expert_context(analysis, context)
            
            # Create expert prompt
            prompt = self._create_expert_prompt(query, analysis, expert_context)
            
            # Generate response using Ollama
            llm_response = self._query_llm(prompt)
            
            # Process LLM response for actions
            processed_response = self._process_llm_response(llm_response, analysis)
            
            # Add system recommendations
            processed_response.update(self._generate_system_recommendations(analysis))
            
            return processed_response
            
        except Exception as e:
            self.logger.error(f"Error generating expert response: {e}")
            return {
                'response': "I encountered an error generating the expert response. Please try again.",
                'error': str(e)
            }

    def _prepare_expert_context(self, analysis: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare expert context for LLM query"""
        expert_context = {
            'current_system_status': self.conversation_context['system_status'],
            'historical_patterns': {},
            'safety_guidelines': self.safety_validator.get_safety_guidelines(),
            'available_patterns': []
        }
        
        try:
            # Add relevant expert patterns
            for system in analysis['detected_systems']:
                if system in self.expert_patterns:
                    expert_context['available_patterns'].append({
                        'system': system,
                        'patterns': self.expert_patterns[system]
                    })
            
            # Add historical context for potential issues
            for issue_info in analysis['potential_issues']:
                issue_key = f"{issue_info['category']}_{issue_info['pattern']}"
                if self.history_manager.has_similar_issue(issue_key):
                    expert_context['historical_patterns'][issue_key] = \
                        self.history_manager.get_pattern_history(issue_key)
            
            # Add current context if provided
            if context:
                expert_context.update(context)
            
            return expert_context
            
        except Exception as e:
            self.logger.error(f"Error preparing expert context: {e}")
            return expert_context

    def _create_expert_prompt(self, query: str, analysis: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Create expert-level prompt for LLM"""
        prompt = f"""You are an expert system administrator with deep knowledge of Ubuntu OS, Kubernetes, and GlusterFS systems.

QUERY ANALYSIS:
- User Query: "{query}"
- Detected Intent: {analysis['intent']}
- Detected Systems: {', '.join(analysis['detected_systems']) if analysis['detected_systems'] else 'None'}
- Urgency Level: {analysis['urgency_level']}
- Potential Issues: {len(analysis['potential_issues'])} detected

AVAILABLE EXPERT PATTERNS:
{json.dumps(context.get('available_patterns', []), indent=2)}

HISTORICAL CONTEXT:
{json.dumps(context.get('historical_patterns', {}), indent=2)}

CURRENT SYSTEM STATUS:
{json.dumps(context.get('current_system_status', {}), indent=2)}

SAFETY GUIDELINES:
{json.dumps(context.get('safety_guidelines', {}), indent=2)}

Please provide a comprehensive expert response that includes:

1. **Analysis**: Explain what you understand from the query
2. **Diagnosis**: If this is a technical issue, provide diagnostic steps
3. **Recommendations**: Specific actions or solutions
4. **Safety Considerations**: Any risks or precautions to consider
5. **Next Steps**: Clear actionable items for the user

Format your response as JSON with the following structure:
{{
    "analysis": "Your analysis of the situation",
    "diagnosis": "Technical diagnosis if applicable",
    "recommendations": ["List of specific recommendations"],
    "safety_considerations": ["Any safety notes or warnings"],
    "next_steps": ["Clear actionable items"],
    "confidence_level": "high|medium|low",
    "requires_human_review": true|false
}}

Focus on being practical, safe, and leveraging the historical patterns and expert knowledge available."""

        return prompt

    def _query_llm(self, prompt: str) -> str:
        """Query the LLM using Ollama"""
        try:
            # Configure Ollama client with base URL
            client = ollama.Client(host=self.ollama_base_url)
            
            response = client.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert system administrator with deep knowledge of Kubernetes, GlusterFS, and Ubuntu. Always respond with valid JSON containing analysis, diagnosis, recommendations, safety_considerations, commands, and risk_level.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.3,  # Lower temperature for more consistent responses
                    'top_p': 0.9,
                    'num_predict': 1000  # Limit response length
                },
                format='json'  # Ensure JSON response
            )
            
            return response['message']['content']
            
        except Exception as e:
            self.logger.error(f"Error querying LLM: {e}")
            # Fallback to rule-based response when LLM is not available
            return self._generate_fallback_response(prompt)

    def _generate_fallback_response(self, prompt: str) -> str:
        """Generate rule-based response when LLM is not available"""
        self.logger.info("Using fallback rule-based response system")
        
        # Analyze prompt for keywords to provide intelligent fallback
        prompt_lower = prompt.lower()
        
        if any(keyword in prompt_lower for keyword in ['pod', 'kubernetes', 'k8s', 'kubectl']):
            # Execute actual kubectl command for pod listing
            command_result = self._execute_safe_command('kubectl get pods --all-namespaces')
            
            return json.dumps({
                'analysis': 'Kubernetes query detected - providing live pod data',
                'diagnosis': 'LLM temporarily unavailable, executing kubectl commands directly',
                'recommendations': [
                    'Live pod data retrieved successfully',
                    'Use "kubectl describe pod <name>" for detailed pod information',
                    'Check pod logs with "kubectl logs <pod-name>"'
                ],
                'safety_considerations': ['Commands are read-only and safe to execute'],
                'commands': ['kubectl get pods --all-namespaces'],
                'command_output': command_result,
                'risk_level': 'SAFE'
            })
        elif any(keyword in prompt_lower for keyword in ['gluster', 'volume', 'storage']):
            # Execute GlusterFS status commands
            volume_result = self._execute_safe_command('gluster volume status')
            peer_result = self._execute_safe_command('gluster peer status')
            
            return json.dumps({
                'analysis': 'GlusterFS query detected - providing live cluster data',
                'diagnosis': 'LLM temporarily unavailable, executing gluster commands directly',
                'recommendations': [
                    'Live GlusterFS data retrieved',
                    'Check volume status and peer connectivity',
                    'Monitor healing processes if needed'
                ],
                'safety_considerations': ['Verify cluster health before making changes'],
                'commands': ['gluster volume status', 'gluster peer status'],
                'command_output': {
                    'volume_status': volume_result,
                    'peer_status': peer_result
                },
                'risk_level': 'SAFE'
            })
        else:
            # Execute general system status commands
            system_result = self._execute_safe_command('df -h')
            memory_result = self._execute_safe_command('free -m')
            
            return json.dumps({
                'analysis': 'General system query - providing live system data',
                'diagnosis': 'Expert LLM service is initializing, showing current system status',
                'recommendations': [
                    'Live system data retrieved',
                    'Wait for LLM service to complete initialization for advanced analysis',
                    'Current system status shows basic health metrics'
                ],
                'safety_considerations': ['System is in initialization phase'],
                'commands': ['df -h', 'free -m'],
                'command_output': {
                    'disk_usage': system_result,
                    'memory_usage': memory_result
                },
                'risk_level': 'SAFE'
            })

    def _execute_safe_command(self, command: str) -> str:
        """Execute safe system commands and return output"""
        import subprocess
        
        try:
            # Validate command safety first
            validation = self.safety_validator.validate_command(command, "SAFE")
            
            if not validation['safe']:
                return f"Command rejected for safety: {validation['reason']}"
            
            # Check if this is a kubectl command - use Kubernetes API instead
            if command.startswith('kubectl'):
                return self._execute_kubectl_command(command)
            
            # Execute the command
            self.logger.info(f"Executing safe command: {command}")
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    return output
                else:
                    return "Command executed successfully (no output)"
            else:
                error_msg = result.stderr.strip() or "Command failed with no error message"
                return f"Command failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds"
        except Exception as e:
            self.logger.error(f"Error executing command {command}: {e}")
            return f"Error executing command: {str(e)}"

    def _execute_kubectl_command(self, command: str) -> str:
        """Execute comprehensive kubectl commands using Kubernetes Python client with intelligent analysis"""
        try:
            from kubernetes import client, config
            import re
            
            # Load in-cluster config (we're running inside a Kubernetes pod)
            config.load_incluster_config()
            
            # Create API clients
            v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()
            networking_v1 = client.NetworkingV1Api()
            rbac_v1 = client.RbacAuthorizationV1Api()
            events_v1 = client.EventsV1Api()
            
            self.logger.info(f"Executing kubectl command via K8s API: {command}")
            
            # Parse kubectl command - Enhanced parsing for comprehensive support
            command_lower = command.lower().strip()
            
            # Debug logging
            self.logger.info(f"Command after lowercase and strip: '{command_lower}'")
            
            # GET COMMANDS
            if command_lower.startswith('kubectl get') or command_lower.startswith('get'):
                self.logger.info("Routing to _handle_get_commands")
                return self._handle_get_commands(command_lower, v1, apps_v1, networking_v1, rbac_v1)
            
            # DESCRIBE COMMANDS  
            elif 'describe' in command_lower:
                self.logger.info("Routing to _handle_describe_commands")
                return self._handle_describe_commands(command_lower, v1, apps_v1, networking_v1)
            
            # LOGS COMMANDS
            elif 'logs' in command_lower:
                self.logger.info("Routing to _handle_logs_commands")
                return self._handle_logs_commands(command_lower, v1)
            
            # EVENTS COMMANDS
            elif 'events' in command_lower:
                self.logger.info("Routing to _handle_events_commands")
                return self._handle_events_commands(command_lower, v1)
            
            # ROOT CAUSE ANALYSIS - New intelligent feature
            elif 'analyze' in command_lower or 'root cause' in command_lower or 'investigate' in command_lower:
                self.logger.info("Routing to root cause analysis")
                error_pattern = self._extract_error_pattern(command)
                return self._perform_root_cause_analysis(error_pattern, v1, apps_v1)
            
            # SMART CORRELATION - New cross-pod timestamp correlation
            elif 'smart_correlate' in command_lower or 'correlate' in command_lower:
                self.logger.info("Routing to smart correlation analysis")
                return self._perform_smart_correlation(command_lower, v1, apps_v1)
            
            # TIMESTAMP ANALYSIS - Correlate events across time
            elif 'timestamp' in command_lower and 'analyze' in command_lower:
                self.logger.info("Routing to timestamp analysis")
                return self._perform_timestamp_analysis(command_lower, v1)
            
            # EXEC COMMANDS (limited for security)
            elif 'exec' in command_lower:
                return self._handle_exec_commands(command_lower, v1)
            
            # PORT-FORWARD (informational)
            elif 'port-forward' in command_lower:
                return "Port-forward commands should be run from your local terminal:\n" + command
            
            # APPLY/CREATE/DELETE - Safety restricted
            elif any(action in command_lower for action in ['apply', 'create', 'delete', 'patch', 'edit']):
                return f"⚠️ WRITE OPERATIONS RESTRICTED FOR SAFETY\nCommand: {command}\nReason: Write operations require manual approval for safety"
            
            else:
                self.logger.warning(f"Command not recognized: {command_lower}")
                return self._suggest_command_alternatives(command_lower)
                
        except Exception as e:
            self.logger.error(f"Error executing kubectl command via K8s API: {e}")
            return f"Error executing kubectl command: {str(e)}\n\nTip: Try using standard kubectl syntax like:\n- kubectl get pods\n- kubectl describe pod <name>\n- kubectl logs <pod-name>"

    def _handle_get_commands(self, command: str, v1, apps_v1, networking_v1, rbac_v1) -> str:
        """Handle all kubectl get commands comprehensively"""
        try:
            # Parse namespace
            namespace = self._parse_namespace(command)
            all_namespaces = '--all-namespaces' in command or '-A' in command
            
            if 'get pods' in command or 'get pod' in command:
                return self._get_pods_detailed(v1, namespace, all_namespaces)
            elif 'get services' in command or 'get svc' in command:
                return self._get_services_detailed(v1, namespace, all_namespaces)
            elif 'get nodes' in command or 'get node' in command:
                return self._get_nodes_detailed(v1)
            elif 'get deployments' in command or 'get deploy' in command:
                return self._get_deployments_detailed(apps_v1, namespace, all_namespaces)
            elif 'get namespaces' in command or 'get ns' in command:
                return self._get_namespaces_detailed(v1)
            elif 'get events' in command:
                return self._get_events_detailed(v1, namespace, all_namespaces)
            elif 'get configmaps' in command or 'get cm' in command:
                return self._get_configmaps_detailed(v1, namespace, all_namespaces)
            elif 'get secrets' in command:
                return self._get_secrets_detailed(v1, namespace, all_namespaces)
            elif 'get ingress' in command or 'get ing' in command:
                return self._get_ingress_detailed(networking_v1, namespace, all_namespaces)
            elif 'get persistentvolumes' in command or 'get pv' in command:
                return self._get_pv_detailed(v1)
            elif 'get persistentvolumeclaims' in command or 'get pvc' in command:
                return self._get_pvc_detailed(v1, namespace, all_namespaces)
            elif 'get all' in command:
                return self._get_all_resources(v1, apps_v1, namespace, all_namespaces)
            else:
                return f"Get command not recognized. Try: pods, services, nodes, deployments, namespaces, events, configmaps, secrets, ingress, pv, pvc, all"
                
        except Exception as e:
            return f"Error handling get command: {str(e)}"

    def _handle_describe_commands(self, command: str, v1, apps_v1, networking_v1) -> str:
        """Handle all kubectl describe commands with detailed analysis"""
        try:
            parts = command.split()
            if len(parts) < 3:
                return "Usage: kubectl describe <resource-type> <resource-name> [-n <namespace>]"
            
            resource_type = parts[1].lower()
            resource_name = parts[2]
            namespace = self._parse_namespace(command) or 'default'
            
            if resource_type in ['pod', 'pods']:
                return self._describe_pod_detailed(v1, resource_name, namespace)
            elif resource_type in ['service', 'services', 'svc']:
                return self._describe_service_detailed(v1, resource_name, namespace)
            elif resource_type in ['deployment', 'deployments', 'deploy']:
                return self._describe_deployment_detailed(apps_v1, resource_name, namespace)
            elif resource_type in ['node', 'nodes']:
                return self._describe_node_detailed(v1, resource_name)
            else:
                return f"Describe command for {resource_type} not yet implemented"
                
        except Exception as e:
            return f"Error handling describe command: {str(e)}"

    def _handle_logs_commands(self, command: str, v1) -> str:
        """Handle kubectl logs with advanced options"""
        try:
            parts = command.split()
            if len(parts) < 2:
                return "Usage: kubectl logs <pod-name> [-n <namespace>] [-c <container>] [--tail=lines] [--since=time]"
            
            pod_name = parts[1] if len(parts) > 1 else None
            namespace = self._parse_namespace(command) or 'default'
            container = self._parse_container(command)
            tail_lines = self._parse_tail_lines(command)
            since_seconds = self._parse_since_seconds(command)
            
            if not pod_name:
                return "Pod name is required"
            
            try:
                log_params = {
                    'name': pod_name,
                    'namespace': namespace,
                    'tail_lines': tail_lines or 100,
                }
                
                if container:
                    log_params['container'] = container
                if since_seconds:
                    log_params['since_seconds'] = since_seconds
                
                logs = v1.read_namespaced_pod_log(**log_params)
                
                header = f"=== Logs for pod {pod_name}"
                if container:
                    header += f" (container: {container})"
                header += f" in namespace {namespace} ==="
                
                return f"{header}\n{logs}"
                
            except client.ApiException as e:
                if e.status == 404:
                    return f"Pod '{pod_name}' not found in namespace '{namespace}'"
                else:
                    return f"Error getting logs for pod '{pod_name}': {e.reason}"
                    
        except Exception as e:
            return f"Error handling logs command: {str(e)}"

    def _handle_events_commands(self, command: str, v1) -> str:
        """Handle kubectl get events with filtering"""
        try:
            namespace = self._parse_namespace(command)
            all_namespaces = '--all-namespaces' in command or '-A' in command
            
            if all_namespaces:
                events = v1.list_event_for_all_namespaces()
            elif namespace:
                events = v1.list_namespaced_event(namespace=namespace)
            else:
                events = v1.list_namespaced_event(namespace='default')
            
            output = "NAMESPACE    LAST SEEN    TYPE      REASON          OBJECT                     MESSAGE\n"
            
            # Sort events by timestamp (most recent first)
            sorted_events = sorted(events.items, key=lambda x: x.last_timestamp or x.first_timestamp, reverse=True)
            
            for event in sorted_events[:50]:  # Show last 50 events
                last_seen = "unknown"
                if event.last_timestamp:
                    time_diff = datetime.now(timezone.utc) - event.last_timestamp
                    if time_diff.days > 0:
                        last_seen = f"{time_diff.days}d"
                    elif time_diff.seconds > 3600:
                        last_seen = f"{time_diff.seconds // 3600}h"
                    else:
                        last_seen = f"{time_diff.seconds // 60}m"
                
                obj_ref = f"{event.involved_object.kind}/{event.involved_object.name}" if event.involved_object else "unknown"
                message = (event.message[:50] + '...') if len(event.message) > 50 else event.message
                
                output += f"{event.namespace:<12} {last_seen:<12} {event.type:<9} {event.reason:<15} {obj_ref:<26} {message}\n"
            
            return output.strip()
            
        except Exception as e:
            return f"Error getting events: {str(e)}"

    def _perform_root_cause_analysis(self, error_pattern: str, v1, apps_v1) -> str:
        """Perform intelligent root cause analysis by cross-referencing cluster data"""
        try:
            analysis_result = "=== ROOT CAUSE ANALYSIS ===\n"
            analysis_result += f"Analyzing error pattern: '{error_pattern}'\n\n"
            
            findings = []
            
            # 1. Search in pod logs across all namespaces
            pods_with_error = self._search_error_in_pods(error_pattern, v1)
            if pods_with_error:
                findings.append("🔍 FOUND IN POD LOGS:")
                for pod_info in pods_with_error:
                    findings.append(f"  • {pod_info}")
            
            # 2. Search in events
            events_with_error = self._search_error_in_events(error_pattern, v1)
            if events_with_error:
                findings.append("\n🔍 FOUND IN EVENTS:")
                for event_info in events_with_error:
                    findings.append(f"  • {event_info}")
            
            # 3. Check pod statuses for related issues
            related_pod_issues = self._find_related_pod_issues(error_pattern, v1)
            if related_pod_issues:
                findings.append("\n🔍 RELATED POD ISSUES:")
                for issue in related_pod_issues:
                    findings.append(f"  • {issue}")
            
            # 4. Cross-reference with node issues
            node_issues = self._check_node_issues(v1)
            if node_issues:
                findings.append("\n🔍 POTENTIAL NODE ISSUES:")
                for issue in node_issues:
                    findings.append(f"  • {issue}")
            
            # 5. Generate intelligent recommendations
            recommendations = self._generate_rca_recommendations(error_pattern, findings)
            
            if findings:
                analysis_result += "\n".join(findings)
                analysis_result += f"\n\n=== RECOMMENDATIONS ===\n{recommendations}"
            else:
                analysis_result += "❌ No direct matches found in cluster data.\n"
                analysis_result += "🔍 Try checking:\n"
                analysis_result += "  • Specific pod logs: kubectl logs <pod-name>\n"
                analysis_result += "  • Recent events: kubectl get events --sort-by='.lastTimestamp'\n"
                analysis_result += "  • Node status: kubectl get nodes -o wide\n"
            
            return analysis_result
            
        except Exception as e:
            return f"Error performing root cause analysis: {str(e)}"

    def _handle_exec_commands(self, command: str, v1) -> str:
        """Handle exec commands (limited for security)"""
        return "⚠️ EXEC COMMANDS RESTRICTED\nFor security reasons, exec commands are not allowed through this interface.\nUse your local kubectl: " + command

    def _suggest_command_alternatives(self, command: str) -> str:
        """Suggest alternative commands based on input"""
        suggestions = []
        
        if any(word in command for word in ['status', 'health', 'check']):
            suggestions.extend([
                "kubectl get pods --all-namespaces",
                "kubectl get nodes",
                "kubectl get events --sort-by='.lastTimestamp'"
            ])
        
        if any(word in command for word in ['error', 'issue', 'problem']):
            suggestions.extend([
                "kubectl get events --all-namespaces | grep -i error",
                "kubectl get pods --all-namespaces --field-selector=status.phase!=Running",
                "analyze 'your-error-message-here'"
            ])
        
        if any(word in command for word in ['network', 'connection', 'dns']):
            suggestions.extend([
                "kubectl get services --all-namespaces",
                "kubectl get ingress --all-namespaces",
                "kubectl get networkpolicies --all-namespaces"
            ])
        
        base_msg = f"Command not recognized: {command}\n\n"
        
        if suggestions:
            base_msg += "💡 You might want to try:\n"
            for suggestion in suggestions[:5]:
                base_msg += f"  • {suggestion}\n"
        
        base_msg += "\n📖 Supported commands:\n"
        base_msg += "  • get [pods|services|nodes|deployments|events|all] [--all-namespaces]\n"
        base_msg += "  • describe [pod|service|deployment|node] <name> [-n <namespace>]\n"
        base_msg += "  • logs <pod-name> [-n <namespace>] [-c <container>]\n"
        base_msg += "  • analyze '<error-message>' (for root cause analysis)\n"
        
        return base_msg

    def _process_llm_response(self, llm_response: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate LLM response"""
        try:
            # Try to parse JSON response
            try:
                response_data = json.loads(llm_response)
            except json.JSONDecodeError:
                # Extract JSON from response if wrapped in text
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    response_data = json.loads(json_match.group())
                else:
                    # Fallback to text response
                    response_data = {
                        'analysis': 'Response parsing error',
                        'diagnosis': 'Could not parse LLM response as JSON',
                        'recommendations': [llm_response[:500] + '...' if len(llm_response) > 500 else llm_response],
                        'safety_considerations': ['Manual review required'],
                        'next_steps': ['Review response manually'],
                        'confidence_level': 'low',
                        'requires_human_review': True
                    }
            
            # Add metadata
            response_data.update({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'query_analysis': analysis,
                'response_type': 'expert_rag',
                'model_used': self.model_name
            })
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Error processing LLM response: {e}")
            return {
                'analysis': 'Error processing response',
                'diagnosis': f'Processing error: {str(e)}',
                'recommendations': ['Please try rephrasing your query'],
                'safety_considerations': ['System error detected'],
                'next_steps': ['Retry with different query'],
                'confidence_level': 'low',
                'requires_human_review': True,
                'error': str(e)
            }

    def _generate_system_recommendations(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate system-level recommendations based on analysis"""
        recommendations = {
            'automated_actions': [],
            'manual_actions': [],
            'monitoring_suggestions': [],
            'preventive_measures': []
        }
        
        try:
            # Check for potential issues and suggest actions
            for issue_info in analysis['potential_issues']:
                issue_key = f"{issue_info['category']}_{issue_info['pattern']}"
                
                # Get historical recommendations
                if self.history_manager.has_similar_issue(issue_key):
                    history = self.history_manager.get_pattern_history(issue_key)
                    
                    # Suggest based on successful past resolutions
                    for occurrence in history['occurrences']:
                        if occurrence['success']:
                            recommendations['automated_actions'].append({
                                'action': occurrence['resolution_method'],
                                'confidence': occurrence['confidence_score'],
                                'historical_success': True
                            })
            
            # Add urgency-based recommendations
            if analysis['urgency_level'] == 'high':
                recommendations['manual_actions'].append({
                    'action': 'Immediate human review required',
                    'priority': 'CRITICAL',
                    'reason': 'High urgency detected in query'
                })
            
            # Add system monitoring suggestions
            for system in analysis['detected_systems']:
                recommendations['monitoring_suggestions'].append({
                    'system': system,
                    'action': f'Enable enhanced monitoring for {system}',
                    'duration': '24 hours'
                })
            
        except Exception as e:
            self.logger.error(f"Error generating system recommendations: {e}")
        
        return recommendations

    def _update_system_context(self) -> None:
        """Update current system context"""
        try:
            self.conversation_context['system_status'] = self.system_monitor.get_comprehensive_status()
            self.conversation_context['active_issues'] = self.history_manager.get_trending_issues(7)  # Last 7 days
        except Exception as e:
            self.logger.error(f"Error updating system context: {e}")

    def _update_conversation_history(self, query: str, response: Dict[str, Any]) -> None:
        """Update conversation history for context"""
        try:
            self.conversation_context['session_history'].append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'query': query,
                'response_summary': response.get('analysis', 'No analysis available'),
                'actions_suggested': len(response.get('recommendations', [])),
                'confidence': response.get('confidence_level', 'unknown')
            })
            
            # Keep only last 10 interactions
            if len(self.conversation_context['session_history']) > 10:
                self.conversation_context['session_history'] = \
                    self.conversation_context['session_history'][-10:]
                    
        except Exception as e:
            self.logger.error(f"Error updating conversation history: {e}")

    def update_history(self, issue: Dict[str, Any]) -> None:
        """Update the issue history with new occurrences"""
        try:
            issue_id = issue.get('id', 'unknown_issue')
            occurrence_data = issue.get('data', {})
            
            self.history_manager.track_issue(issue_id, occurrence_data)
            
        except Exception as e:
            self.logger.error(f"Error updating history: {e}")

    def predict_root_cause(self, issue: Dict[str, Any]) -> Tuple[str, float]:
        """Use historical data to predict the root cause of an issue"""
        try:
            issue_id = issue.get('id', 'unknown_issue')
            current_context = issue.get('context', {})
            
            return self.history_manager.predict_root_cause(issue_id, current_context)
            
        except Exception as e:
            self.logger.error(f"Error predicting root cause: {e}")
            return "Error in prediction", 0.1

    def get_conversation_context(self) -> Dict[str, Any]:
        """Get current conversation context"""
        return self.conversation_context

    def execute_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a detected action with safety validation
        
        Args:
            action_data: Action details from the conversation
            
        Returns:
            Execution result with safety information
        """
        try:
            # Validate action safety
            if action_data.get('requires_validation', False):
                safety_check = self.safety_validator.validate_command(action_data.get('command', ''))
                
                if safety_check['risk_level'] == 'HIGH':
                    return {
                        'status': 'blocked',
                        'reason': 'High risk action blocked by safety validator',
                        'safety_check': safety_check,
                        'requires_manual_approval': True
                    }
            
            # Execute through remediation engine if it's a known pattern
            if 'issue_pattern' in action_data:
                result = self.remediation_engine.execute_remediation(
                    action_data['issue_pattern'],
                    action_data.get('commands', [])
                )
                
                # Record the execution for learning
                self.history_manager.record_resolution(
                    action_data['issue_pattern'],
                    result
                )
                
                return result
            
            # For general actions, use safety validator
            return {
                'status': 'manual_review_required',
                'message': 'Action requires manual execution',
                'action_data': action_data
            }
            
        except Exception as e:
            self.logger.error(f"Error executing action: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'requires_manual_review': True
            }

    # ===== COMPREHENSIVE KUBECTL HELPER METHODS =====
    
    def _parse_namespace(self, command: str) -> str:
        """Parse namespace from kubectl command"""
        if '-n ' in command:
            parts = command.split('-n ')
            if len(parts) > 1:
                return parts[1].split()[0]
        elif '--namespace=' in command:
            parts = command.split('--namespace=')
            if len(parts) > 1:
                return parts[1].split()[0]
        elif '--namespace ' in command:
            parts = command.split('--namespace ')
            if len(parts) > 1:
                return parts[1].split()[0]
        return None

    def _parse_container(self, command: str) -> str:
        """Parse container name from kubectl logs command"""
        if '-c ' in command:
            parts = command.split('-c ')
            if len(parts) > 1:
                return parts[1].split()[0]
        elif '--container=' in command:
            parts = command.split('--container=')
            if len(parts) > 1:
                return parts[1].split()[0]
        return None

    def _parse_tail_lines(self, command: str) -> int:
        """Parse tail lines from kubectl logs command"""
        if '--tail=' in command:
            parts = command.split('--tail=')
            if len(parts) > 1:
                try:
                    return int(parts[1].split()[0])
                except ValueError:
                    pass
        return None

    def _parse_since_seconds(self, command: str) -> int:
        """Parse since seconds from kubectl logs command"""
        if '--since=' in command:
            parts = command.split('--since=')
            if len(parts) > 1:
                time_str = parts[1].split()[0]
                # Simple parsing - can be enhanced
                if time_str.endswith('s'):
                    return int(time_str[:-1])
                elif time_str.endswith('m'):
                    return int(time_str[:-1]) * 60
                elif time_str.endswith('h'):
                    return int(time_str[:-1]) * 3600
        return None

    def _extract_error_pattern(self, command: str) -> str:
        """Extract error pattern from analyze command"""
        # Look for quoted strings or specific patterns
        import re
        quoted_match = re.search(r"['\"]([^'\"]+)['\"]", command)
        if quoted_match:
            return quoted_match.group(1)
        
        # If no quotes, take everything after 'analyze'
        if 'analyze' in command.lower():
            parts = command.lower().split('analyze')
            if len(parts) > 1:
                return parts[1].strip()
        
        return command

    def _get_pods_detailed(self, v1, namespace: str, all_namespaces: bool) -> str:
        """Get detailed pod information"""
        try:
            if all_namespaces:
                pods = v1.list_pod_for_all_namespaces()
                output = "NAMESPACE         NAME                           READY   STATUS      RESTARTS   AGE     NODE\n"
            else:
                ns = namespace or 'default'
                pods = v1.list_namespaced_pod(namespace=ns)
                output = "NAME                           READY   STATUS      RESTARTS   AGE     NODE\n"
            
            for pod in pods.items:
                # Calculate ready containers
                ready_count = 0
                total_count = len(pod.status.container_statuses) if pod.status.container_statuses else 0
                
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        if container.ready:
                            ready_count += 1
                
                ready_status = f"{ready_count}/{total_count}"
                
                # Calculate age
                if pod.status.start_time:
                    age = (datetime.now(timezone.utc) - pod.status.start_time).days
                    age_str = f"{age}d" if age > 0 else "<1d"
                else:
                    age_str = "unknown"
                
                # Get restart count
                restart_count = 0
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        restart_count += container.restart_count
                
                node_name = pod.spec.node_name or "unknown"
                
                if all_namespaces:
                    output += f"{pod.metadata.namespace:<17} {pod.metadata.name:<30} {ready_status:<7} {pod.status.phase:<11} {restart_count:<10} {age_str:<7} {node_name}\n"
                else:
                    output += f"{pod.metadata.name:<30} {ready_status:<7} {pod.status.phase:<11} {restart_count:<10} {age_str:<7} {node_name}\n"
            
            return output.strip()
            
        except Exception as e:
            return f"Error getting pods: {str(e)}"

    def _get_services_detailed(self, v1, namespace: str, all_namespaces: bool) -> str:
        """Get detailed service information"""
        try:
            if all_namespaces:
                services = v1.list_service_for_all_namespaces()
                output = "NAMESPACE    NAME                    TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)                  AGE\n"
            else:
                ns = namespace or 'default'
                services = v1.list_namespaced_service(namespace=ns)
                output = "NAME                    TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)                  AGE\n"
            
            for svc in services.items:
                external_ip = "<none>"
                if svc.status.load_balancer and svc.status.load_balancer.ingress:
                    external_ip = svc.status.load_balancer.ingress[0].ip or svc.status.load_balancer.ingress[0].hostname or "<pending>"
                
                ports = []
                if svc.spec.ports:
                    for port in svc.spec.ports:
                        if port.node_port:
                            ports.append(f"{port.port}:{port.node_port}/{port.protocol}")
                        else:
                            ports.append(f"{port.port}/{port.protocol}")
                port_str = ','.join(ports) or "<none>"
                
                if svc.metadata.creation_timestamp:
                    age = (datetime.now(timezone.utc) - svc.metadata.creation_timestamp).days
                    age_str = f"{age}d" if age > 0 else "<1d"
                else:
                    age_str = "unknown"
                
                if all_namespaces:
                    output += f"{svc.metadata.namespace:<12} {svc.metadata.name:<23} {svc.spec.type:<14} {svc.spec.cluster_ip:<15} {external_ip:<13} {port_str:<24} {age_str}\n"
                else:
                    output += f"{svc.metadata.name:<23} {svc.spec.type:<14} {svc.spec.cluster_ip:<15} {external_ip:<13} {port_str:<24} {age_str}\n"
            
            return output.strip()
            
        except Exception as e:
            return f"Error getting services: {str(e)}"

    def _get_nodes_detailed(self, v1) -> str:
        """Get detailed node information"""
        try:
            nodes = v1.list_node()
            output = "NAME              STATUS    ROLES           AGE     VERSION        INTERNAL-IP     EXTERNAL-IP\n"
            
            for node in nodes.items:
                status = "Ready" if any(condition.status == "True" and condition.type == "Ready" for condition in node.status.conditions) else "NotReady"
                roles = ','.join([label.split('/')[-1] for label in node.metadata.labels.keys() if 'node-role.kubernetes.io' in label]) or "<none>"
                
                if node.metadata.creation_timestamp:
                    age = (datetime.now(timezone.utc) - node.metadata.creation_timestamp).days
                    age_str = f"{age}d" if age > 0 else "<1d"
                else:
                    age_str = "unknown"
                
                version = node.status.node_info.kubelet_version if node.status.node_info else "unknown"
                
                internal_ip = external_ip = "<none>"
                if node.status.addresses:
                    for addr in node.status.addresses:
                        if addr.type == "InternalIP":
                            internal_ip = addr.address
                        elif addr.type == "ExternalIP":
                            external_ip = addr.address
                
                output += f"{node.metadata.name:<17} {status:<9} {roles:<15} {age_str:<7} {version:<14} {internal_ip:<15} {external_ip}\n"
            
            return output.strip()
            
        except Exception as e:
            return f"Error getting nodes: {str(e)}"

    def _get_deployments_detailed(self, apps_v1, namespace: str, all_namespaces: bool) -> str:
        """Get detailed deployment information"""
        try:
            if all_namespaces:
                deployments = apps_v1.list_deployment_for_all_namespaces()
                output = "NAMESPACE    NAME                    READY   UP-TO-DATE   AVAILABLE   AGE\n"
            else:
                ns = namespace or 'default'
                deployments = apps_v1.list_namespaced_deployment(namespace=ns)
                output = "NAME                    READY   UP-TO-DATE   AVAILABLE   AGE\n"
            
            for deploy in deployments.items:
                ready = f"{deploy.status.ready_replicas or 0}/{deploy.spec.replicas or 0}"
                up_to_date = deploy.status.updated_replicas or 0
                available = deploy.status.available_replicas or 0
                
                if deploy.metadata.creation_timestamp:
                    age = (datetime.now(timezone.utc) - deploy.metadata.creation_timestamp).days
                    age_str = f"{age}d" if age > 0 else "<1d"
                else:
                    age_str = "unknown"
                
                if all_namespaces:
                    output += f"{deploy.metadata.namespace:<12} {deploy.metadata.name:<23} {ready:<7} {up_to_date:<12} {available:<11} {age_str}\n"
                else:
                    output += f"{deploy.metadata.name:<23} {ready:<7} {up_to_date:<12} {available:<11} {age_str}\n"
            
            return output.strip()
            
        except Exception as e:
            return f"Error getting deployments: {str(e)}"

    def _get_namespaces_detailed(self, v1) -> str:
        """Get detailed namespace information"""
        try:
            namespaces = v1.list_namespace()
            output = "NAME                   STATUS    AGE\n"
            
            for ns in namespaces.items:
                status = ns.status.phase or "Unknown"
                
                if ns.metadata.creation_timestamp:
                    age = (datetime.now(timezone.utc) - ns.metadata.creation_timestamp).days
                    age_str = f"{age}d" if age > 0 else "<1d"
                else:
                    age_str = "unknown"
                
                output += f"{ns.metadata.name:<22} {status:<9} {age_str}\n"
            
            return output.strip()
            
        except Exception as e:
            return f"Error getting namespaces: {str(e)}"

    def _get_events_detailed(self, v1, namespace: str, all_namespaces: bool) -> str:
        """Get detailed events information"""
        return self._handle_events_commands(f"get events {'--all-namespaces' if all_namespaces else ''}", v1)

    def _get_configmaps_detailed(self, v1, namespace: str, all_namespaces: bool) -> str:
        """Get detailed configmaps information"""
        try:
            if all_namespaces:
                cms = v1.list_config_map_for_all_namespaces()
                output = "NAMESPACE    NAME                    DATA   AGE\n"
            else:
                ns = namespace or 'default'
                cms = v1.list_namespaced_config_map(namespace=ns)
                output = "NAME                    DATA   AGE\n"
            
            for cm in cms.items:
                data_count = len(cm.data) if cm.data else 0
                
                if cm.metadata.creation_timestamp:
                    age = (datetime.now(timezone.utc) - cm.metadata.creation_timestamp).days
                    age_str = f"{age}d" if age > 0 else "<1d"
                else:
                    age_str = "unknown"
                
                if all_namespaces:
                    output += f"{cm.metadata.namespace:<12} {cm.metadata.name:<23} {data_count:<6} {age_str}\n"
                else:
                    output += f"{cm.metadata.name:<23} {data_count:<6} {age_str}\n"
            
            return output.strip()
            
        except Exception as e:
            return f"Error getting configmaps: {str(e)}"

    def _get_secrets_detailed(self, v1, namespace: str, all_namespaces: bool) -> str:
        """Get detailed secrets information"""
        try:
            if all_namespaces:
                secrets = v1.list_secret_for_all_namespaces()
                output = "NAMESPACE    NAME                               TYPE                                  DATA   AGE\n"
            else:
                ns = namespace or 'default'
                secrets = v1.list_namespaced_secret(namespace=ns)
                output = "NAME                               TYPE                                  DATA   AGE\n"
            
            for secret in secrets.items:
                data_count = len(secret.data) if secret.data else 0
                secret_type = secret.type or "Opaque"
                
                if secret.metadata.creation_timestamp:
                    age = (datetime.now(timezone.utc) - secret.metadata.creation_timestamp).days
                    age_str = f"{age}d" if age > 0 else "<1d"
                else:
                    age_str = "unknown"
                
                if all_namespaces:
                    output += f"{secret.metadata.namespace:<12} {secret.metadata.name:<34} {secret_type:<37} {data_count:<6} {age_str}\n"
                else:
                    output += f"{secret.metadata.name:<34} {secret_type:<37} {data_count:<6} {age_str}\n"
            
            return output.strip()
            
        except Exception as e:
            return f"Error getting secrets: {str(e)}"

    def _get_ingress_detailed(self, networking_v1, namespace: str, all_namespaces: bool) -> str:
        """Get detailed ingress information"""
        try:
            if all_namespaces:
                ingresses = networking_v1.list_ingress_for_all_namespaces()
                output = "NAMESPACE    NAME                    CLASS    HOSTS                   ADDRESS     PORTS     AGE\n"
            else:
                ns = namespace or 'default'
                ingresses = networking_v1.list_namespaced_ingress(namespace=ns)
                output = "NAME                    CLASS    HOSTS                   ADDRESS     PORTS     AGE\n"
            
            for ing in ingresses.items:
                ing_class = ing.spec.ingress_class_name or "<none>"
                hosts = []
                if ing.spec.rules:
                    for rule in ing.spec.rules:
                        if rule.host:
                            hosts.append(rule.host)
                host_str = ','.join(hosts) or "*"
                
                address = "<none>"
                if ing.status.load_balancer and ing.status.load_balancer.ingress:
                    ing_ingress = ing.status.load_balancer.ingress[0]
                    address = ing_ingress.ip or ing_ingress.hostname or "<none>"
                
                ports = "80"
                if ing.spec.tls:
                    ports += ",443"
                
                if ing.metadata.creation_timestamp:
                    age = (datetime.now(timezone.utc) - ing.metadata.creation_timestamp).days
                    age_str = f"{age}d" if age > 0 else "<1d"
                else:
                    age_str = "unknown"
                
                if all_namespaces:
                    output += f"{ing.metadata.namespace:<12} {ing.metadata.name:<23} {ing_class:<8} {host_str:<23} {address:<11} {ports:<9} {age_str}\n"
                else:
                    output += f"{ing.metadata.name:<23} {ing_class:<8} {host_str:<23} {address:<11} {ports:<9} {age_str}\n"
            
            return output.strip()
            
        except Exception as e:
            return f"Error getting ingress: {str(e)}"

    def _get_pv_detailed(self, v1) -> str:
        """Get detailed persistent volume information"""
        try:
            pvs = v1.list_persistent_volume()
            output = "NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM                    STORAGECLASS   AGE\n"
            
            for pv in pvs.items:
                capacity = pv.spec.capacity.get('storage', 'unknown') if pv.spec.capacity else 'unknown'
                access_modes = ','.join(pv.spec.access_modes) if pv.spec.access_modes else 'unknown'
                reclaim_policy = pv.spec.persistent_volume_reclaim_policy or 'unknown'
                status = pv.status.phase or 'unknown'
                
                claim = "<none>"
                if pv.spec.claim_ref:
                    claim = f"{pv.spec.claim_ref.namespace}/{pv.spec.claim_ref.name}"
                
                storage_class = pv.spec.storage_class_name or "<none>"
                
                if pv.metadata.creation_timestamp:
                    age = (datetime.now(timezone.utc) - pv.metadata.creation_timestamp).days
                    age_str = f"{age}d" if age > 0 else "<1d"
                else:
                    age_str = "unknown"
                
                output += f"{pv.metadata.name:<42} {capacity:<10} {access_modes:<14} {reclaim_policy:<16} {status:<11} {claim:<24} {storage_class:<14} {age_str}\n"
            
            return output.strip()
            
        except Exception as e:
            return f"Error getting persistent volumes: {str(e)}"

    def _get_pvc_detailed(self, v1, namespace: str, all_namespaces: bool) -> str:
        """Get detailed persistent volume claims information"""
        try:
            if all_namespaces:
                pvcs = v1.list_persistent_volume_claim_for_all_namespaces()
                output = "NAMESPACE    NAME                    STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE\n"
            else:
                ns = namespace or 'default'
                pvcs = v1.list_namespaced_persistent_volume_claim(namespace=ns)
                output = "NAME                    STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE\n"
            
            for pvc in pvcs.items:
                status = pvc.status.phase or 'unknown'
                volume_name = pvc.spec.volume_name or "<none>"
                
                capacity = "<none>"
                if pvc.status.capacity:
                    capacity = pvc.status.capacity.get('storage', '<none>')
                
                access_modes = ','.join(pvc.spec.access_modes) if pvc.spec.access_modes else '<none>'
                storage_class = pvc.spec.storage_class_name or "<none>"
                
                if pvc.metadata.creation_timestamp:
                    age = (datetime.now(timezone.utc) - pvc.metadata.creation_timestamp).days
                    age_str = f"{age}d" if age > 0 else "<1d"
                else:
                    age_str = "unknown"
                
                if all_namespaces:
                    output += f"{pvc.metadata.namespace:<12} {pvc.metadata.name:<23} {status:<8} {volume_name:<42} {capacity:<10} {access_modes:<14} {storage_class:<14} {age_str}\n"
                else:
                    output += f"{pvc.metadata.name:<23} {status:<8} {volume_name:<42} {capacity:<10} {access_modes:<14} {storage_class:<14} {age_str}\n"
            
            return output.strip()
            
        except Exception as e:
            return f"Error getting persistent volume claims: {str(e)}"

    def _get_all_resources(self, v1, apps_v1, namespace: str, all_namespaces: bool) -> str:
        """Get all major resources in a summary"""
        result = "=== CLUSTER RESOURCE SUMMARY ===\n\n"
        
        try:
            result += "PODS:\n"
            result += self._get_pods_detailed(v1, namespace, all_namespaces)
            result += "\n\nSERVICES:\n"
            result += self._get_services_detailed(v1, namespace, all_namespaces)
            result += "\n\nDEPLOYMENTS:\n"
            result += self._get_deployments_detailed(apps_v1, namespace, all_namespaces)
            
            if all_namespaces or not namespace:
                result += "\n\nNODES:\n"
                result += self._get_nodes_detailed(v1)
                
        except Exception as e:
            result += f"\nError getting all resources: {str(e)}"
        
        return result

    def _describe_pod_detailed(self, v1, pod_name: str, namespace: str) -> str:
        """Provide detailed pod description with enhanced analysis"""
        try:
            from kubernetes import client
            pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            
            output = f"=== DETAILED POD ANALYSIS: {pod_name} ===\n\n"
            
            # Basic info
            output += f"Name:        {pod.metadata.name}\n"
            output += f"Namespace:   {pod.metadata.namespace}\n"
            output += f"Status:      {pod.status.phase}\n"
            output += f"Node:        {pod.spec.node_name or 'Not assigned'}\n"
            output += f"Start Time:  {pod.status.start_time or 'Not started'}\n"
            
            if pod.status.pod_ip:
                output += f"Pod IP:      {pod.status.pod_ip}\n"
            
            # Labels
            if pod.metadata.labels:
                output += f"\nLabels:\n"
                for key, value in pod.metadata.labels.items():
                    output += f"  {key}={value}\n"
            
            # Containers detailed analysis
            if pod.spec.containers:
                output += f"\nCONTAINERS:\n"
                for i, container in enumerate(pod.spec.containers):
                    output += f"  Container {i+1}: {container.name}\n"
                    output += f"    Image:   {container.image}\n"
                    
                    if container.ports:
                        ports = ', '.join([f"{port.container_port}/{port.protocol}" for port in container.ports])
                        output += f"    Ports:   {ports}\n"
                    
                    # Resource requests/limits
                    if container.resources:
                        if container.resources.requests:
                            output += f"    Requests: {dict(container.resources.requests)}\n"
                        if container.resources.limits:
                            output += f"    Limits:   {dict(container.resources.limits)}\n"
            
            # Container statuses with health analysis
            if pod.status.container_statuses:
                output += f"\nCONTAINER STATUS ANALYSIS:\n"
                for status in pod.status.container_statuses:
                    output += f"  {status.name}:\n"
                    output += f"    Ready:        {status.ready}\n"
                    output += f"    Restart Count: {status.restart_count}\n"
                    output += f"    Image:        {status.image}\n"
                    
                    if status.state:
                        if status.state.running:
                            output += f"    State:        Running (started: {status.state.running.started_at})\n"
                        elif status.state.waiting:
                            output += f"    State:        Waiting\n"
                            output += f"    Reason:       {status.state.waiting.reason}\n"
                            if status.state.waiting.message:
                                output += f"    Message:      {status.state.waiting.message}\n"
                        elif status.state.terminated:
                            output += f"    State:        Terminated\n"
                            output += f"    Reason:       {status.state.terminated.reason}\n"
                            output += f"    Exit Code:    {status.state.terminated.exit_code}\n"
                            if status.state.terminated.message:
                                output += f"    Message:      {status.state.terminated.message}\n"
            
            # Conditions analysis
            if pod.status.conditions:
                output += f"\nPOD CONDITIONS:\n"
                for condition in pod.status.conditions:
                    status_indicator = "✅" if condition.status == "True" else "❌"
                    output += f"  {status_indicator} {condition.type}: {condition.status}\n"
                    if condition.reason:
                        output += f"    Reason: {condition.reason}\n"
                    if condition.message:
                        output += f"    Message: {condition.message}\n"
            
            # Events for this pod
            try:
                events = v1.list_namespaced_event(
                    namespace=namespace,
                    field_selector=f"involvedObject.name={pod_name}"
                )
                if events.items:
                    output += f"\nRECENT EVENTS:\n"
                    for event in sorted(events.items, key=lambda x: x.last_timestamp or x.first_timestamp, reverse=True)[:10]:
                        output += f"  {event.type}: {event.reason} - {event.message}\n"
            except:
                output += f"\nEvents: Could not retrieve events\n"
            
            # Health recommendations
            output += f"\n=== HEALTH ANALYSIS ===\n"
            health_issues = []
            
            if pod.status.phase != "Running":
                health_issues.append(f"Pod is in {pod.status.phase} state")
            
            if pod.status.container_statuses:
                for status in pod.status.container_statuses:
                    if not status.ready:
                        health_issues.append(f"Container {status.name} is not ready")
                    if status.restart_count > 0:
                        health_issues.append(f"Container {status.name} has {status.restart_count} restarts")
            
            if health_issues:
                output += "⚠️  Issues found:\n"
                for issue in health_issues:
                    output += f"  • {issue}\n"
            else:
                output += "✅ Pod appears healthy\n"
            
            return output
            
        except client.ApiException as e:
            if e.status == 404:
                return f"Pod '{pod_name}' not found in namespace '{namespace}'"
            else:
                return f"Error describing pod '{pod_name}': {e.reason}"

    def _describe_service_detailed(self, v1, service_name: str, namespace: str) -> str:
        """Provide detailed service description"""
        try:
            from kubernetes import client
            service = v1.read_namespaced_service(name=service_name, namespace=namespace)
            
            output = f"=== SERVICE ANALYSIS: {service_name} ===\n\n"
            output += f"Name:         {service.metadata.name}\n"
            output += f"Namespace:    {service.metadata.namespace}\n"
            output += f"Type:         {service.spec.type}\n"
            output += f"Cluster IP:   {service.spec.cluster_ip}\n"
            
            if service.spec.external_i_ps:
                output += f"External IPs: {', '.join(service.spec.external_i_ps)}\n"
            
            if service.spec.ports:
                output += f"\nPorts:\n"
                for port in service.spec.ports:
                    port_info = f"  {port.name or 'unnamed'}: {port.port}"
                    if port.target_port:
                        port_info += f" -> {port.target_port}"
                    port_info += f"/{port.protocol}"
                    if port.node_port:
                        port_info += f" (NodePort: {port.node_port})"
                    output += port_info + "\n"
            
            if service.spec.selector:
                output += f"\nSelector:\n"
                for key, value in service.spec.selector.items():
                    output += f"  {key}={value}\n"
                
                # Find matching pods
                try:
                    label_selector = ','.join([f"{k}={v}" for k, v in service.spec.selector.items()])
                    pods = v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
                    output += f"\nMatching Pods ({len(pods.items)}):\n"
                    for pod in pods.items:
                        output += f"  • {pod.metadata.name} ({pod.status.phase})\n"
                except:
                    output += f"\nCould not retrieve matching pods\n"
            
            return output
            
        except client.ApiException as e:
            if e.status == 404:
                return f"Service '{service_name}' not found in namespace '{namespace}'"
            else:
                return f"Error describing service '{service_name}': {e.reason}"

    def _describe_deployment_detailed(self, apps_v1, deployment_name: str, namespace: str) -> str:
        """Provide detailed deployment description"""
        try:
            from kubernetes import client
            deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
            
            output = f"=== DEPLOYMENT ANALYSIS: {deployment_name} ===\n\n"
            output += f"Name:            {deployment.metadata.name}\n"
            output += f"Namespace:       {deployment.metadata.namespace}\n"
            output += f"Replicas:        {deployment.spec.replicas}\n"
            output += f"Ready Replicas:  {deployment.status.ready_replicas or 0}\n"
            output += f"Updated:         {deployment.status.updated_replicas or 0}\n"
            output += f"Available:       {deployment.status.available_replicas or 0}\n"
            
            if deployment.spec.strategy:
                output += f"Strategy:        {deployment.spec.strategy.type}\n"
            
            # Pod template analysis
            if deployment.spec.template.spec.containers:
                output += f"\nContainer Template:\n"
                for container in deployment.spec.template.spec.containers:
                    output += f"  • {container.name}: {container.image}\n"
            
            # Selector
            if deployment.spec.selector.match_labels:
                output += f"\nSelector:\n"
                for key, value in deployment.spec.selector.match_labels.items():
                    output += f"  {key}={value}\n"
            
            # Conditions
            if deployment.status.conditions:
                output += f"\nConditions:\n"
                for condition in deployment.status.conditions:
                    status_indicator = "✅" if condition.status == "True" else "❌"
                    output += f"  {status_indicator} {condition.type}: {condition.reason}\n"
                    if condition.message:
                        output += f"    {condition.message}\n"
            
            return output
            
        except client.ApiException as e:
            if e.status == 404:
                return f"Deployment '{deployment_name}' not found in namespace '{namespace}'"
            else:
                return f"Error describing deployment '{deployment_name}': {e.reason}"

    def _describe_node_detailed(self, v1, node_name: str) -> str:
        """Provide detailed node description"""
        try:
            from kubernetes import client
            node = v1.read_node(name=node_name)
            
            output = f"=== NODE ANALYSIS: {node_name} ===\n\n"
            output += f"Name:                 {node.metadata.name}\n"
            
            # Node info
            if node.status.node_info:
                info = node.status.node_info
                output += f"OS:                   {info.operating_system}\n"
                output += f"Architecture:         {info.architecture}\n"
                output += f"Kernel Version:       {info.kernel_version}\n"
                output += f"Kubelet Version:      {info.kubelet_version}\n"
                output += f"Container Runtime:    {info.container_runtime_version}\n"
            
            # Addresses
            if node.status.addresses:
                output += f"\nAddresses:\n"
                for addr in node.status.addresses:
                    output += f"  {addr.type}: {addr.address}\n"
            
            # Conditions
            if node.status.conditions:
                output += f"\nConditions:\n"
                for condition in node.status.conditions:
                    status_indicator = "✅" if condition.status == "True" else "❌"
                    if condition.type == "Ready":
                        status_indicator = "✅" if condition.status == "True" else "❌"
                    else:
                        status_indicator = "❌" if condition.status == "True" else "✅"
                    
                    output += f"  {status_indicator} {condition.type}: {condition.status}\n"
                    if condition.reason:
                        output += f"    Reason: {condition.reason}\n"
            
            # Capacity and allocatable
            if node.status.capacity:
                output += f"\nCapacity:\n"
                for resource, quantity in node.status.capacity.items():
                    output += f"  {resource}: {quantity}\n"
            
            if node.status.allocatable:
                output += f"\nAllocatable:\n"
                for resource, quantity in node.status.allocatable.items():
                    output += f"  {resource}: {quantity}\n"
            
            return output
            
        except client.ApiException as e:
            if e.status == 404:
                return f"Node '{node_name}' not found"
            else:
                return f"Error describing node '{node_name}': {e.reason}"

    def _search_error_in_pods(self, error_pattern: str, v1) -> list:
        """Search for error pattern in pod logs across all namespaces"""
        findings = []
        try:
            pods = v1.list_pod_for_all_namespaces()
            
            for pod in pods.items:
                if pod.status.phase == "Running" or pod.status.phase == "Failed":
                    try:
                        logs = v1.read_namespaced_pod_log(
                            name=pod.metadata.name,
                            namespace=pod.metadata.namespace,
                            tail_lines=100
                        )
                        
                        if error_pattern.lower() in logs.lower():
                            findings.append(f"Pod {pod.metadata.namespace}/{pod.metadata.name}: Found in logs")
                    except:
                        pass  # Skip pods without logs
            
        except Exception as e:
            findings.append(f"Error searching pod logs: {str(e)}")
        
        return findings

    def _search_error_in_events(self, error_pattern: str, v1) -> list:
        """Search for error pattern in cluster events"""
        findings = []
        try:
            events = v1.list_event_for_all_namespaces()
            
            for event in events.items:
                if (error_pattern.lower() in event.message.lower() or 
                    error_pattern.lower() in event.reason.lower()):
                    findings.append(f"Event in {event.namespace}: {event.reason} - {event.message[:100]}")
            
        except Exception as e:
            findings.append(f"Error searching events: {str(e)}")
        
        return findings

    def _find_related_pod_issues(self, error_pattern: str, v1) -> list:
        """Find pods with related issues"""
        issues = []
        try:
            pods = v1.list_pod_for_all_namespaces()
            
            for pod in pods.items:
                pod_issues = []
                
                # Check pod status
                if pod.status.phase != "Running":
                    pod_issues.append(f"Status: {pod.status.phase}")
                
                # Check container statuses
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        if not container.ready:
                            pod_issues.append(f"Container {container.name} not ready")
                        if container.restart_count > 0:
                            pod_issues.append(f"Container {container.name} restarted {container.restart_count} times")
                        
                        # Check container state messages
                        if container.state:
                            if container.state.waiting and container.state.waiting.message:
                                if error_pattern.lower() in container.state.waiting.message.lower():
                                    pod_issues.append(f"Container {container.name}: {container.state.waiting.message}")
                            elif container.state.terminated and container.state.terminated.message:
                                if error_pattern.lower() in container.state.terminated.message.lower():
                                    pod_issues.append(f"Container {container.name}: {container.state.terminated.message}")
                
                if pod_issues:
                    issues.append(f"Pod {pod.metadata.namespace}/{pod.metadata.name}: {', '.join(pod_issues)}")
                    
        except Exception as e:
            issues.append(f"Error analyzing pod issues: {str(e)}")
        
        return issues

    def _check_node_issues(self, v1) -> list:
        """Check for node-level issues that might be related"""
        issues = []
        try:
            nodes = v1.list_node()
            
            for node in nodes.items:
                node_issues = []
                
                if node.status.conditions:
                    for condition in node.status.conditions:
                        if condition.type == "Ready" and condition.status != "True":
                            node_issues.append("Node not ready")
                        elif condition.type in ["MemoryPressure", "DiskPressure", "PIDPressure"] and condition.status == "True":
                            node_issues.append(f"{condition.type} detected")
                
                if node_issues:
                    issues.append(f"Node {node.metadata.name}: {', '.join(node_issues)}")
                    
        except Exception as e:
            issues.append(f"Error checking node issues: {str(e)}")
        
        return issues

    def _generate_rca_recommendations(self, error_pattern: str, findings: list) -> str:
        """Generate intelligent recommendations based on root cause analysis"""
        recommendations = []
        
        # Analyze findings to generate specific recommendations
        findings_text = ' '.join(findings).lower()
        
        if 'imagepullbackoff' in findings_text or 'errimagepull' in findings_text:
            recommendations.extend([
                "Check image name and tag for typos",
                "Verify image exists in the registry",
                "Check registry authentication (imagePullSecrets)",
                "kubectl describe pod <pod-name> for detailed error info"
            ])
        
        elif 'crashloopbackoff' in findings_text:
            recommendations.extend([
                "Check container logs: kubectl logs <pod-name>",
                "Verify application startup configuration",
                "Check resource limits and requests",
                "Review application dependencies and health checks"
            ])
        
        elif 'pending' in findings_text:
            recommendations.extend([
                "Check node resources: kubectl describe nodes",
                "Verify PVC availability if using persistent storage",
                "Check pod affinity/anti-affinity rules",
                "Review nodeSelector constraints"
            ])
        
        elif 'out of memory' in findings_text or 'oom' in findings_text:
            recommendations.extend([
                "Increase memory limits in pod specification",
                "Check for memory leaks in application",
                "Review memory usage patterns: kubectl top pods",
                "Consider horizontal pod autoscaling"
            ])
        
        elif 'network' in findings_text or 'dns' in findings_text:
            recommendations.extend([
                "Check service definitions and selectors",
                "Verify network policies are not blocking traffic",
                "Test DNS resolution from within pods",
                "Check ingress configuration if applicable"
            ])
        
        return "; ".join(recommendations[:5])  # Return top 5 recommendations

    def _perform_smart_correlation(self, command: str, v1, apps_v1) -> str:
        """Perform intelligent cross-pod correlation with timestamp analysis"""
        try:
            # Parse pod name and namespace from command
            parts = command.split()
            pod_name = None
            namespace = 'default'
            
            for i, part in enumerate(parts):
                if part.startswith('smart_correlate'):
                    continue
                elif part == '-n' and i + 1 < len(parts):
                    namespace = parts[i + 1]
                elif not part.startswith('-') and pod_name is None:
                    pod_name = part
            
            if not pod_name:
                return "❌ Pod name required for smart correlation analysis\nUsage: smart_correlate <pod-name> [-n <namespace>]"
            
            correlation_result = "=== SMART POD CORRELATION ANALYSIS ===\n"
            correlation_result += f"Analyzing pod: {pod_name} in namespace: {namespace}\n\n"
            
            # 1. Get target pod details and logs
            target_pod_info = self._analyze_target_pod(pod_name, namespace, v1)
            correlation_result += f"🎯 TARGET POD ANALYSIS:\n{target_pod_info}\n\n"
            
            # 2. Get pod logs with timestamps
            pod_logs = self._get_timestamped_logs(pod_name, namespace, v1)
            correlation_result += f"📜 POD LOGS ANALYSIS:\n{pod_logs}\n\n"
            
            # 3. Correlate with other pods in same namespace
            namespace_correlation = self._correlate_namespace_pods(pod_name, namespace, v1)
            correlation_result += f"🔗 NAMESPACE CORRELATION:\n{namespace_correlation}\n\n"
            
            # 4. Correlate with cluster events in same timeframe
            event_correlation = self._correlate_cluster_events(pod_name, namespace, v1)
            correlation_result += f"📊 EVENT CORRELATION:\n{event_correlation}\n\n"
            
            # 5. Generate timeline-based recommendations
            timeline_recommendations = self._generate_timeline_recommendations(pod_name, namespace, v1)
            correlation_result += f"⏰ TIMELINE-BASED RECOMMENDATIONS:\n{timeline_recommendations}"
            
            return correlation_result
            
        except Exception as e:
            return f"Error performing smart correlation: {str(e)}"

    def _perform_timestamp_analysis(self, command: str, v1) -> str:
        """Perform timestamp-based analysis across cluster"""
        try:
            analysis_result = "=== TIMESTAMP CORRELATION ANALYSIS ===\n"
            
            # Get all events in last hour sorted by time
            events = v1.list_event_for_all_namespaces()
            recent_events = []
            
            current_time = datetime.now(timezone.utc)
            one_hour_ago = current_time - timedelta(hours=1)
            
            for event in events.items:
                event_time = event.last_timestamp or event.first_timestamp
                if event_time and event_time >= one_hour_ago:
                    recent_events.append({
                        'time': event_time,
                        'namespace': event.namespace,
                        'object': f"{event.involved_object.kind}/{event.involved_object.name}",
                        'reason': event.reason,
                        'message': event.message,
                        'type': event.type
                    })
            
            # Sort by timestamp
            recent_events.sort(key=lambda x: x['time'])
            
            analysis_result += f"Found {len(recent_events)} events in the last hour:\n\n"
            
            # Group events by time windows (5-minute windows)
            time_windows = {}
            for event in recent_events:
                window = event['time'].replace(minute=event['time'].minute//5*5, second=0, microsecond=0)
                if window not in time_windows:
                    time_windows[window] = []
                time_windows[window].append(event)
            
            # Analyze each time window for patterns
            for window_time, window_events in sorted(time_windows.items()):
                analysis_result += f"⏰ Time Window: {window_time.strftime('%H:%M:%S')}\n"
                
                # Look for error patterns in this window
                error_events = [e for e in window_events if e['type'] == 'Warning']
                if error_events:
                    analysis_result += f"  ⚠️  {len(error_events)} warning events:\n"
                    for event in error_events[:5]:  # Show top 5
                        analysis_result += f"    • {event['namespace']}/{event['object']}: {event['reason']}\n"
                
                # Look for related normal events
                normal_events = [e for e in window_events if e['type'] == 'Normal']
                if normal_events:
                    analysis_result += f"  ✅  {len(normal_events)} normal events\n"
                
                analysis_result += "\n"
            
            return analysis_result
            
        except Exception as e:
            return f"Error performing timestamp analysis: {str(e)}"

    def _analyze_target_pod(self, pod_name: str, namespace: str, v1) -> str:
        """Analyze the target pod in detail"""
        try:
            pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            
            analysis = f"Pod: {pod_name}\n"
            analysis += f"Namespace: {namespace}\n"
            analysis += f"Status: {pod.status.phase}\n"
            analysis += f"Node: {pod.spec.node_name or 'Not scheduled'}\n"
            analysis += f"Created: {pod.metadata.creation_timestamp}\n"
            
            # Check container statuses
            if pod.status.container_statuses:
                analysis += "\nContainer Statuses:\n"
                for container in pod.status.container_statuses:
                    analysis += f"  • {container.name}: Ready={container.ready}, RestartCount={container.restart_count}\n"
                    if container.state.waiting:
                        analysis += f"    Waiting: {container.state.waiting.reason}\n"
                    elif container.state.terminated:
                        analysis += f"    Terminated: {container.state.terminated.reason}\n"
                    elif container.state.running:
                        analysis += f"    Running since: {container.state.running.started_at}\n"
            
            # Check conditions
            if pod.status.conditions:
                analysis += "\nPod Conditions:\n"
                for condition in pod.status.conditions:
                    analysis += f"  • {condition.type}: {condition.status} ({condition.reason})\n"
            
            return analysis
            
        except Exception as e:
            return f"Error analyzing target pod: {str(e)}"

    def _get_timestamped_logs(self, pod_name: str, namespace: str, v1) -> str:
        """Get pod logs with timestamp analysis"""
        try:
            logs = v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                timestamps=True,
                tail_lines=50
            )
            
            log_lines = logs.split('\n')
            error_lines = []
            warning_lines = []
            
            for line in log_lines:
                line_lower = line.lower()
                if any(error_word in line_lower for error_word in ['error', 'failed', 'exception', 'fatal']):
                    error_lines.append(line)
                elif any(warn_word in line_lower for warn_word in ['warn', 'warning', 'deprecated']):
                    warning_lines.append(line)
            
            analysis = f"Log Summary (last 50 lines):\n"
            analysis += f"Total lines: {len(log_lines)}\n"
            analysis += f"Error lines: {len(error_lines)}\n"
            analysis += f"Warning lines: {len(warning_lines)}\n\n"
            
            if error_lines:
                analysis += "🚨 Recent Errors:\n"
                for line in error_lines[-5:]:  # Show last 5 errors
                    analysis += f"  {line}\n"
                analysis += "\n"
            
            if warning_lines:
                analysis += "⚠️ Recent Warnings:\n"
                for line in warning_lines[-3:]:  # Show last 3 warnings
                    analysis += f"  {line}\n"
            
            return analysis
            
        except Exception as e:
            return f"Error getting timestamped logs: {str(e)}"

    def _correlate_namespace_pods(self, target_pod: str, namespace: str, v1) -> str:
        """Correlate with other pods in the same namespace"""
        try:
            pods = v1.list_namespaced_pod(namespace=namespace)
            
            correlation = f"Pods in namespace '{namespace}':\n"
            healthy_pods = 0
            unhealthy_pods = 0
            
            for pod in pods.items:
                if pod.metadata.name == target_pod:
                    continue
                
                status = "✅ Healthy"
                if pod.status.phase != 'Running':
                    status = f"❌ {pod.status.phase}"
                    unhealthy_pods += 1
                else:
                    # Check container health
                    if pod.status.container_statuses:
                        for container in pod.status.container_statuses:
                            if not container.ready or container.restart_count > 0:
                                status = f"⚠️ Issues (restarts: {container.restart_count})"
                                unhealthy_pods += 1
                                break
                        else:
                            healthy_pods += 1
                    else:
                        healthy_pods += 1
                
                correlation += f"  • {pod.metadata.name}: {status}\n"
            
            correlation += f"\nSummary: {healthy_pods} healthy, {unhealthy_pods} with issues\n"
            
            if unhealthy_pods > 0:
                correlation += "🔍 Potential cluster-wide issue detected!\n"
            
            return correlation
            
        except Exception as e:
            return f"Error correlating namespace pods: {str(e)}"

    def _correlate_cluster_events(self, pod_name: str, namespace: str, v1) -> str:
        """Correlate with cluster events in the same timeframe"""
        try:
            events = v1.list_namespaced_event(namespace=namespace)
            
            # Find events related to the target pod
            pod_events = []
            related_events = []
            
            current_time = datetime.now(timezone.utc)
            five_minutes_ago = current_time - timedelta(minutes=5)
            
            for event in events.items:
                event_time = event.last_timestamp or event.first_timestamp
                if not event_time or event_time < five_minutes_ago:
                    continue
                
                if event.involved_object.name == pod_name:
                    pod_events.append(event)
                else:
                    related_events.append(event)
            
            correlation = f"Events in last 5 minutes:\n"
            correlation += f"Direct pod events: {len(pod_events)}\n"
            correlation += f"Related events: {len(related_events)}\n\n"
            
            if pod_events:
                correlation += "🎯 Direct Pod Events:\n"
                for event in sorted(pod_events, key=lambda x: x.last_timestamp or x.first_timestamp)[-3:]:
                    time_str = (event.last_timestamp or event.first_timestamp).strftime('%H:%M:%S')
                    correlation += f"  {time_str} - {event.reason}: {event.message[:100]}...\n"
                correlation += "\n"
            
            if related_events:
                correlation += "🔗 Related Events:\n"
                for event in sorted(related_events, key=lambda x: x.last_timestamp or x.first_timestamp)[-5:]:
                    time_str = (event.last_timestamp or event.first_timestamp).strftime('%H:%M:%S')
                    correlation += f"  {time_str} - {event.involved_object.name}: {event.reason}\n"
            
            return correlation
            
        except Exception as e:
            return f"Error correlating cluster events: {str(e)}"

    def _generate_timeline_recommendations(self, pod_name: str, namespace: str, v1) -> str:
        """Generate timeline-based recommendations"""
        try:
            recommendations = []
            
            # Get pod creation time and current status
            pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            created_time = pod.metadata.creation_timestamp
            current_time = datetime.now(timezone.utc)
            pod_age = current_time - created_time
            
            recommendations.append(f"Pod age: {pod_age}")
            
            # Check restart patterns
            if pod.status.container_statuses:
                for container in pod.status.container_statuses:
                    if container.restart_count > 0:
                        recommendations.append(f"⚠️ Container '{container.name}' has {container.restart_count} restarts")
                        recommendations.append("  → Check logs for crash patterns")
                        recommendations.append("  → Review resource limits")
                        
                        if container.restart_count > 5:
                            recommendations.append("  → Consider CrashLoopBackOff investigation")
            
            # Check if pod is new and having issues
            if pod_age.total_seconds() < 300 and pod.status.phase != 'Running':  # Less than 5 minutes
                recommendations.append("🆕 Recent pod having startup issues")
                recommendations.append("  → Check image pull status")
                recommendations.append("  → Verify resource availability")
                recommendations.append("  → Review startup probes")
            
            # Long-running pod with issues
            if pod_age.days > 1 and pod.status.phase != 'Running':
                recommendations.append("🕰️ Long-running pod now failing")
                recommendations.append("  → Check for resource exhaustion")
                recommendations.append("  → Review recent changes")
                recommendations.append("  → Investigate node health")
            
            return "\n".join(recommendations) if recommendations else "No specific timeline-based recommendations"
            
        except Exception as e:
            return f"Error generating timeline recommendations: {str(e)}"

    def _handle_kubectl_query(self, kubectl_cmd: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Handle kubectl-specific queries from chat interface"""
        try:
            command = kubectl_cmd['command']
            
            # Execute the kubectl command
            result = self._execute_safe_command(command)
            
            # Format response based on command type
            if kubectl_cmd['type'] == 'logs':
                response_text = f"📜 **Pod Logs for {kubectl_cmd['pod']}:**\n\n"
                if "Error" in result:
                    response_text += f"❌ {result}"
                else:
                    # Analyze logs for errors
                    log_lines = result.split('\n')
                    error_count = sum(1 for line in log_lines if any(err in line.lower() for err in ['error', 'failed', 'exception', 'fatal']))
                    
                    response_text += f"**Log Summary:**\n"
                    response_text += f"- Total lines: {len(log_lines)}\n"
                    response_text += f"- Error indicators: {error_count}\n\n"
                    
                    if error_count > 0:
                        response_text += "**Recent Errors Found:**\n"
                        error_lines = [line for line in log_lines if any(err in line.lower() for err in ['error', 'failed', 'exception', 'fatal'])]
                        for line in error_lines[-5:]:  # Show last 5 errors
                            response_text += f"⚠️ {line}\n"
                        response_text += "\n"
                    
                    response_text += f"**Full Logs:**\n```\n{result}\n```"
                
            elif kubectl_cmd['type'] == 'describe':
                response_text = f"📋 **Pod Details for {kubectl_cmd['pod']}:**\n\n"
                if "Error" in result:
                    response_text += f"❌ {result}"
                else:
                    # Extract key information
                    lines = result.split('\n')
                    status_line = next((line for line in lines if 'Status:' in line), '')
                    node_line = next((line for line in lines if 'Node:' in line), '')
                    
                    if status_line:
                        response_text += f"**Status:** {status_line.split('Status:')[1].strip()}\n"
                    if node_line:
                        response_text += f"**Node:** {node_line.split('Node:')[1].strip()}\n"
                    
                    response_text += f"\n**Full Details:**\n```\n{result}\n```"
                    
            elif kubectl_cmd['type'] == 'get':
                response_text = f"📊 **Cluster Overview:**\n\n"
                if "Error" in result:
                    response_text += f"❌ {result}"
                else:
                    response_text += f"```\n{result}\n```"
            
            else:
                response_text = f"**Command Result:**\n```\n{result}\n```"
            
            return {
                'response': response_text,
                'confidence_level': 'high',
                'intent': 'kubectl_command',
                'kubectl_result': result,
                'executed_command': command,
                'next_steps': self._generate_kubectl_next_steps(kubectl_cmd, result),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error handling kubectl query: {e}")
            return {
                'response': f"❌ Error executing kubectl command: {str(e)}",
                'error': str(e),
                'confidence_level': 'low',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    def _generate_kubectl_next_steps(self, kubectl_cmd: Dict[str, Any], result: str) -> List[str]:
        """Generate suggested next steps based on kubectl command results"""
        next_steps = []
        
        try:
            if kubectl_cmd['type'] == 'logs':
                if 'error' in result.lower() or 'failed' in result.lower():
                    next_steps.extend([
                        f"kubectl describe pod {kubectl_cmd['pod']} -n {kubectl_cmd['namespace']}",
                        f"kubectl get events -n {kubectl_cmd['namespace']} --sort-by='.lastTimestamp'",
                        f"analyze 'error patterns in {kubectl_cmd['pod']}'"
                    ])
                else:
                    next_steps.extend([
                        f"kubectl describe pod {kubectl_cmd['pod']} -n {kubectl_cmd['namespace']}",
                        "kubectl get pods --all-namespaces"
                    ])
                    
            elif kubectl_cmd['type'] == 'describe':
                pod_name = kubectl_cmd['pod']
                namespace = kubectl_cmd['namespace']
                next_steps.extend([
                    f"kubectl logs {pod_name} -n {namespace} --tail=50",
                    f"smart_correlate {pod_name} -n {namespace}",
                    f"kubectl get events -n {namespace} --field-selector involvedObject.name={pod_name}"
                ])
                
            elif kubectl_cmd['type'] == 'get':
                next_steps.extend([
                    "kubectl get events --all-namespaces --sort-by='.lastTimestamp'",
                    "kubectl get services --all-namespaces",
                    "analyze 'cluster health'"
                ])
            
        except Exception as e:
            self.logger.error(f"Error generating kubectl next steps: {e}")
            
        return next_steps[:5]  # Limit to 5 suggestions