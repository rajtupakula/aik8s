"""
Utility classes for the Expert Remediation Engine
"""

import subprocess
import shlex
import psutil
import os
import logging
import platform
from typing import Dict, List, Any, Tuple
from datetime import datetime
import re
import json

def log_message(message: str) -> None:
    """Logs a message to the console."""
    print(f"[LOG] {message}")

def validate_data(data: dict, required_keys: list) -> bool:
    """Validates that the provided data contains all required keys."""
    return all(key in data for key in required_keys)

def format_response(response: dict) -> str:
    """Formats the response dictionary into a readable string."""
    return "\n".join(f"{key}: {value}" for key, value in response.items())

class SafetyValidator:
    """
    Validates commands for safety before execution
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define dangerous command patterns
        self.dangerous_patterns = [
            r'rm\s+-rf\s+/',
            r'dd\s+if=.*of=/dev/',
            r'mkfs\.',
            r'fdisk',
            r'parted',
            r'shutdown',
            r'reboot',
            r'halt',
            r'init\s+[06]',
            r'killall\s+-9',
            r':\(\)\{\s*:\|:&\s*\};:',  # Fork bomb
            r'chmod\s+777\s+/',
            r'chown\s+.*\s+/',
        ]
        
        # Define safe command prefixes
        self.safe_prefixes = [
            'kubectl get',
            'kubectl describe',
            'kubectl logs',
            'docker ps',
            'docker images',
            'ps aux',
            'top',
            'free',
            'df',
            'du',
            'mount',
            'ip addr',
            'ping',
            'netstat',
            'ss',
            'systemctl status',
            'journalctl',
            'cat',
            'less',
            'tail',
            'head',
            'grep',
            'find',
            'ls',
            'gluster volume status',
            'gluster peer status',
            'gluster volume info'
        ]
    
    def validate_command(self, command: str, safety_level: str = "MEDIUM") -> Dict[str, Any]:
        """
        Validate a command for safety
        
        Args:
            command: The command to validate
            safety_level: Expected safety level (SAFE, MEDIUM, HIGH)
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'safe': False,
            'reason': '',
            'risk_level': 'UNKNOWN',
            'requires_confirmation': False
        }
        
        try:
            # Check for dangerous patterns
            for pattern in self.dangerous_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    result.update({
                        'safe': False,
                        'reason': f'Contains dangerous pattern: {pattern}',
                        'risk_level': 'HIGH',
                        'requires_confirmation': True
                    })
                    return result
            
            # Check if command starts with safe prefix
            command_lower = command.lower().strip()
            is_safe_prefix = any(command_lower.startswith(prefix.lower()) for prefix in self.safe_prefixes)
            
            if is_safe_prefix:
                result.update({
                    'safe': True,
                    'reason': 'Command matches safe pattern',
                    'risk_level': 'SAFE',
                    'requires_confirmation': False
                })
            elif safety_level == "SAFE":
                result.update({
                    'safe': True,
                    'reason': 'Marked as safe by pattern definition',
                    'risk_level': 'SAFE',
                    'requires_confirmation': False
                })
            elif safety_level == "MEDIUM":
                result.update({
                    'safe': True,
                    'reason': 'Medium risk command, requires confirmation',
                    'risk_level': 'MEDIUM',
                    'requires_confirmation': True
                })
            else:  # HIGH
                result.update({
                    'safe': False,
                    'reason': 'High risk command, manual execution required',
                    'risk_level': 'HIGH',
                    'requires_confirmation': True
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error validating command: {e}")
            result.update({
                'safe': False,
                'reason': f'Validation error: {str(e)}',
                'risk_level': 'UNKNOWN',
                'requires_confirmation': True
            })
            return result
    
    def sanitize_command(self, command: str) -> str:
        """Sanitize command input"""
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[;&|`$()]', '', command)
        return sanitized.strip()
    
    def get_safety_guidelines(self, risk_level: str = "MEDIUM") -> Dict[str, Any]:
        """
        Get safety guidelines based on risk level
        
        Args:
            risk_level: The risk level (SAFE, MEDIUM, HIGH)
            
        Returns:
            Dictionary with safety guidelines and recommendations
        """
        guidelines = {
            "SAFE": {
                "description": "Low risk operations that are safe to execute automatically",
                "recommendations": [
                    "These commands are read-only and don't modify system state",
                    "No confirmation required",
                    "Can be executed immediately"
                ],
                "examples": ["kubectl get pods", "ps aux", "df -h", "free -m"]
            },
            "MEDIUM": {
                "description": "Medium risk operations that require user confirmation",
                "recommendations": [
                    "Review the command before execution",
                    "Ensure you understand the implications",
                    "Have a rollback plan if needed",
                    "Monitor system after execution"
                ],
                "examples": ["systemctl restart service", "kubectl apply", "docker restart"]
            },
            "HIGH": {
                "description": "High risk operations that require careful manual execution",
                "recommendations": [
                    "DO NOT execute automatically",
                    "Require explicit administrator approval",
                    "Test in non-production environment first",
                    "Have comprehensive backup and rollback plan",
                    "Monitor system closely during and after execution"
                ],
                "examples": ["rm -rf", "dd if=", "mkfs", "shutdown", "reboot"]
            }
        }
        
        return guidelines.get(risk_level, guidelines["MEDIUM"])

class SystemMonitor:
    """
    Monitors system health and provides real-time metrics
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'system_info': self._get_system_info(),
                'resource_usage': self._get_resource_usage(),
                'disk_usage': self._get_disk_usage(),
                'network_status': self._get_network_status(),
                'process_info': self._get_process_info(),
                'kubernetes_status': self._get_kubernetes_status(),
                'services_status': self._get_services_status()
            }
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get basic system information"""
        return {
            'os': platform.system(),
            'os_version': platform.version(),
            'architecture': platform.architecture()[0],
            'hostname': platform.node(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
    
    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get resource usage information"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                'cpu_percent': cpu_percent,
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'memory_used_gb': round(memory.used / (1024**3), 2),
                'memory_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'swap_total_gb': round(psutil.swap_memory().total / (1024**3), 2),
                'swap_used_gb': round(psutil.swap_memory().used / (1024**3), 2),
                'swap_percent': psutil.swap_memory().percent
            }
        except Exception as e:
            self.logger.error(f"Error getting resource usage: {e}")
            return {}
    
    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information"""
        try:
            disk_usage = {}
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = {
                        'device': partition.device,
                        'fstype': partition.fstype,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                        'percent': round((usage.used / usage.total) * 100, 2)
                    }
                except PermissionError:
                    continue
            
            return disk_usage
            
        except Exception as e:
            self.logger.error(f"Error getting disk usage: {e}")
            return {}
    
    def _get_network_status(self) -> Dict[str, Any]:
        """Get network status information"""
        try:
            network_info = {}
            network_stats = psutil.net_io_counters(pernic=True)
            
            for interface, stats in network_stats.items():
                network_info[interface] = {
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv,
                    'errors_in': stats.errin,
                    'errors_out': stats.errout
                }
            
            return network_info
            
        except Exception as e:
            self.logger.error(f"Error getting network status: {e}")
            return {}
    
    def _get_process_info(self) -> Dict[str, Any]:
        """Get process information"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage and get top 10
            top_cpu = sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:10]
            # Sort by memory usage and get top 10
            top_memory = sorted(processes, key=lambda x: x.get('memory_percent', 0), reverse=True)[:10]
            
            return {
                'total_processes': len(processes),
                'top_cpu_processes': top_cpu,
                'top_memory_processes': top_memory
            }
            
        except Exception as e:
            self.logger.error(f"Error getting process info: {e}")
            return {}
    
    def _get_kubernetes_status(self) -> Dict[str, Any]:
        """Get Kubernetes cluster status if available"""
        try:
            # Check if kubectl is available
            result = subprocess.run(['which', 'kubectl'], capture_output=True, text=True)
            if result.returncode != 0:
                return {'available': False, 'reason': 'kubectl not found'}
            
            # Get cluster info
            cluster_info = subprocess.run(['kubectl', 'cluster-info'], capture_output=True, text=True, timeout=10)
            if cluster_info.returncode != 0:
                return {'available': False, 'reason': 'Cannot connect to cluster'}
            
            # Get nodes
            nodes_result = subprocess.run(['kubectl', 'get', 'nodes', '-o', 'json'], 
                                        capture_output=True, text=True, timeout=10)
            
            # Get pods
            pods_result = subprocess.run(['kubectl', 'get', 'pods', '--all-namespaces', '-o', 'json'], 
                                       capture_output=True, text=True, timeout=10)
            
            k8s_status = {
                'available': True,
                'cluster_accessible': True,
                'nodes_count': 0,
                'pods_count': 0,
                'failed_pods': 0,
                'pending_pods': 0
            }
            
            # Parse nodes info
            if nodes_result.returncode == 0:
                try:
                    nodes_data = json.loads(nodes_result.stdout)
                    k8s_status['nodes_count'] = len(nodes_data.get('items', []))
                except json.JSONDecodeError:
                    pass
            
            # Parse pods info
            if pods_result.returncode == 0:
                try:
                    pods_data = json.loads(pods_result.stdout)
                    pods = pods_data.get('items', [])
                    k8s_status['pods_count'] = len(pods)
                    
                    for pod in pods:
                        status = pod.get('status', {}).get('phase', '')
                        if status in ['Failed', 'Error']:
                            k8s_status['failed_pods'] += 1
                        elif status == 'Pending':
                            k8s_status['pending_pods'] += 1
                            
                except json.JSONDecodeError:
                    pass
            
            return k8s_status
            
        except subprocess.TimeoutExpired:
            return {'available': True, 'reason': 'Timeout connecting to cluster'}
        except Exception as e:
            self.logger.error(f"Error getting Kubernetes status: {e}")
            return {'available': False, 'reason': str(e)}
    
    def _get_services_status(self) -> Dict[str, Any]:
        """Get system services status"""
        try:
            # Check critical services
            critical_services = ['ssh', 'networking', 'systemd-resolved']
            services_status = {}
            
            for service in critical_services:
                try:
                    result = subprocess.run(['systemctl', 'is-active', service], 
                                          capture_output=True, text=True, timeout=5)
                    services_status[service] = {
                        'active': result.stdout.strip() == 'active',
                        'status': result.stdout.strip()
                    }
                except Exception:
                    services_status[service] = {
                        'active': False,
                        'status': 'unknown'
                    }
            
            return services_status
            
        except Exception as e:
            self.logger.error(f"Error getting services status: {e}")
            return {}