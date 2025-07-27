"""
Chat Assistant Component - Interactive conversational interface for expert system
"""

import streamlit as st
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import json

class ChatAssistant:
    """
    Interactive chat assistant for the Expert LLM System
    
    Features:
    - Natural language query processing
    - Expert pattern recognition and recommendation
    - Historical context integration
    - Safety-validated action suggestions
    - Real-time system context awareness
    """
    
    def __init__(self, rag_agent):
        self.logger = logging.getLogger(__name__)
        self.rag_agent = rag_agent
        
        # Initialize session state for chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'processing' not in st.session_state:
            st.session_state.processing = False

    def render(self):
        """Render the chat assistant interface"""
        st.header("💬 Expert Chat Assistant")
        st.markdown("*Ask questions about system issues, get expert recommendations, and execute guided remediation*")
        
        # Chat interface layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            self._render_chat_interface()
        
        with col2:
            self._render_chat_controls()

    def _render_chat_interface(self):
        """Render main chat interface"""
        # Chat container
        chat_container = st.container()
        
        with chat_container:
            # Display chat history
            self._display_chat_history()
            
            # Chat input
            with st.form(key="chat_form", clear_on_submit=True):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    user_input = st.text_area(
                        "Ask me anything about system administration...",
                        placeholder="e.g., 'My Kubernetes pod is crashing' or 'Check disk space on Ubuntu'",
                        height=100,
                        key="user_input"
                    )
                
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)  # Spacing
                    submit_button = st.form_submit_button("Send 🚀", use_container_width=True)
                
                if submit_button and user_input and not st.session_state.processing:
                    self._process_user_input(user_input)

    def _render_chat_controls(self):
        """Render chat controls and options"""
        st.subheader("🎛️ Chat Controls")
        
        # Quick action buttons
        st.markdown("**Quick Actions:**")
        
        if st.button("🔍 System Health Check", use_container_width=True):
            self._quick_action("system_health_check")
        
        if st.button("📊 Show Active Issues", use_container_width=True):
            self._quick_action("show_active_issues")
        
        if st.button("🎯 List Expert Patterns", use_container_width=True):
            self._quick_action("list_expert_patterns")
        
        if st.button("📈 Learning Analytics", use_container_width=True):
            self._quick_action("learning_analytics")
        
        st.markdown("---")
        
        # Chat settings
        st.subheader("⚙️ Settings")
        
        show_technical_details = st.checkbox("Show Technical Details", value=False)
        enable_auto_actions = st.checkbox("Enable Auto Actions", value=False)
        confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.7, 0.1)
        
        # Store settings in session state
        st.session_state.chat_settings = {
            'show_technical_details': show_technical_details,
            'enable_auto_actions': enable_auto_actions,
            'confidence_threshold': confidence_threshold
        }
        
        st.markdown("---")
        
        # Chat history controls
        st.subheader("📜 History")
        
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        
        if st.button("Export Chat Log", use_container_width=True):
            self._export_chat_log()

    def _display_chat_history(self):
        """Display chat history with messages"""
        if not st.session_state.chat_history:
            st.info("👋 Hello! I'm your expert system assistant. Ask me about Ubuntu OS, Kubernetes, or GlusterFS issues.")
            return
        
        for message in st.session_state.chat_history:
            self._render_message(message)

    def _render_message(self, message: Dict[str, Any]):
        """Render a single chat message"""
        timestamp = message.get('timestamp', '')
        role = message.get('role', 'user')
        content = message.get('content', '')
        
        if role == 'user':
            with st.chat_message("user"):
                st.write(f"**You** _{timestamp}_")
                st.write(content)
        
        elif role == 'assistant':
            with st.chat_message("assistant"):
                st.write(f"**Expert Assistant** _{timestamp}_")
                
                # Display main response
                if 'analysis' in message:
                    st.write("**Analysis:**")
                    st.write(message['analysis'])
                
                if 'recommendations' in message:
                    st.write("**Recommendations:**")
                    for i, rec in enumerate(message['recommendations'], 1):
                        st.write(f"{i}. {rec}")
                
                # Display command output if available
                if 'command_output' in message and message['command_output']:
                    st.write("**Live System Data:**")
                    st.code(message['command_output'], language='bash')
                
                # Show technical details if enabled
                if st.session_state.get('chat_settings', {}).get('show_technical_details', False):
                    if 'diagnosis' in message:
                        with st.expander("🔧 Technical Diagnosis"):
                            st.write(message['diagnosis'])
                    
                    if 'safety_considerations' in message:
                        with st.expander("🛡️ Safety Considerations"):
                            for safety_note in message['safety_considerations']:
                                st.warning(safety_note)
                    
                    if 'query_analysis' in message:
                        with st.expander("📊 Query Analysis"):
                            st.json(message['query_analysis'])
                
                # Action buttons
                if 'next_steps' in message and message['next_steps']:
                    st.write("**Suggested Actions:**")
                    
                    for i, action in enumerate(message['next_steps']):
                        if st.button(f"Execute: {action}", key=f"action_{message.get('id', 0)}_{i}"):
                            self._execute_action(action, message)

    def _process_user_input(self, user_input: str):
        """Process user input and generate response"""
        try:
            st.session_state.processing = True
            
            # Add user message to history
            user_message = {
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'id': len(st.session_state.chat_history)
            }
            st.session_state.chat_history.append(user_message)
            
            # Process query with RAG agent
            with st.spinner("🤔 Analyzing your query..."):
                response = self.rag_agent.expert_query(user_input)
            
            # Add assistant response to history
            assistant_message = {
                'role': 'assistant',
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'id': len(st.session_state.chat_history),
                **response
            }
            st.session_state.chat_history.append(assistant_message)
            
            # Check for high-confidence automated actions
            settings = st.session_state.get('chat_settings', {})
            if (settings.get('enable_auto_actions', False) and 
                response.get('confidence_level') == 'high' and
                not response.get('requires_human_review', False)):
                
                self._suggest_auto_execution(response)
            
        except Exception as e:
            self.logger.error(f"Error processing user input: {e}")
            error_message = {
                'role': 'assistant',
                'content': f"I apologize, but I encountered an error: {str(e)}",
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'id': len(st.session_state.chat_history)
            }
            st.session_state.chat_history.append(error_message)
        
        finally:
            st.session_state.processing = False
            st.rerun()

    def _quick_action(self, action_type: str):
        """Handle quick action buttons"""
        try:
            if action_type == "system_health_check":
                query = "Perform a comprehensive system health check"
            elif action_type == "show_active_issues":
                query = "Show me current active issues and their status"
            elif action_type == "list_expert_patterns":
                query = "List all available expert patterns and their categories"
            elif action_type == "learning_analytics":
                query = "Show learning analytics and historical insights"
            else:
                query = f"Execute quick action: {action_type}"
            
            self._process_user_input(query)
            
        except Exception as e:
            st.error(f"Quick action failed: {e}")

    def _execute_action(self, action: str, message: Dict[str, Any]):
        """Execute a suggested action"""
        try:
            with st.spinner(f"Executing: {action}"):
                # Prepare action data
                action_data = {
                    'action': action,
                    'context': message.get('query_analysis', {}),
                    'confidence': message.get('confidence_level', 'medium'),
                    'requires_validation': message.get('requires_human_review', False)
                }
                
                # Execute through RAG agent
                result = self.rag_agent.execute_action(action_data)
                
                # Add execution result to chat
                execution_message = {
                    'role': 'assistant',
                    'content': f"**Action Executed:** {action}",
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'id': len(st.session_state.chat_history),
                    'execution_result': result
                }
                
                st.session_state.chat_history.append(execution_message)
                
                # Show result
                if result.get('status') == 'success':
                    st.success(f"✅ Action completed successfully!")
                elif result.get('status') == 'blocked':
                    st.warning(f"⚠️ Action blocked: {result.get('reason', 'Safety validation failed')}")
                else:
                    st.info(f"ℹ️ Action status: {result.get('status', 'unknown')}")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Action execution failed: {e}")

    def _suggest_auto_execution(self, response: Dict[str, Any]):
        """Suggest automatic execution for high-confidence actions"""
        st.info("🤖 High-confidence recommendations detected. Auto-execution available.")
        
        if st.button("🚀 Execute All Recommendations"):
            for action in response.get('next_steps', []):
                self._execute_action(action, response)

    def _export_chat_log(self):
        """Export chat history as JSON"""
        try:
            chat_data = {
                'export_timestamp': datetime.now(timezone.utc).isoformat(),
                'chat_history': st.session_state.chat_history,
                'settings': st.session_state.get('chat_settings', {})
            }
            
            json_data = json.dumps(chat_data, indent=2)
            
            st.download_button(
                label="📥 Download Chat Log",
                data=json_data,
                file_name=f"expert_chat_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            st.success("Chat log prepared for download!")
            
        except Exception as e:
            st.error(f"Export failed: {e}")

    # Legacy methods for compatibility
    def process_query(self, query):
        """Legacy method - use render() instead"""
        return f"Expert response to: {query}"

    def display_history(self):
        """Legacy method - history is displayed in render()"""
        return st.session_state.get('chat_history', [])

    def clear_history(self):
        """Legacy method - use the clear button in render()"""
        st.session_state.chat_history = []