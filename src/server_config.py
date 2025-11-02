"""
Server Configuration System for Gomoku
Supports multiple deployment targets: localhost, AWS Lambda, Azure Functions, custom servers
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class ServerType(Enum):
    """Server deployment types"""
    LOCALHOST = "localhost"
    AWS_LAMBDA = "aws_lambda"
    AZURE_FUNCTIONS = "azure_functions"
    CUSTOM = "custom"


@dataclass
class ServerConfig:
    """Server configuration data structure"""
    name: str
    server_type: ServerType
    host: str
    port: int
    use_ssl: bool = False
    api_key: Optional[str] = None
    region: Optional[str] = None
    function_name: Optional[str] = None
    description: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['server_type'] = self.server_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ServerConfig':
        """Create from dictionary"""
        data['server_type'] = ServerType(data['server_type'])
        return cls(**data)


class ServerConfigManager:
    """Manages server configurations"""
    
    def __init__(self, config_file: str = "server_configs.json"):
        self.config_file = config_file
        self.configs: Dict[str, ServerConfig] = {}
        self.current_config: Optional[str] = None
        self._load_configs()
        self._ensure_default_configs()
    
    def _load_configs(self):
        """Load configurations from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    
                self.configs = {
                    name: ServerConfig.from_dict(config_data)
                    for name, config_data in data.get('configs', {}).items()
                }
                self.current_config = data.get('current_config')
            except Exception as e:
                print(f"Error loading server configs: {e}")
                self.configs = {}
                self.current_config = None
    
    def _save_configs(self):
        """Save configurations to file"""
        try:
            data = {
                'current_config': self.current_config,
                'configs': {
                    name: config.to_dict()
                    for name, config in self.configs.items()
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving server configs: {e}")
    
    def _ensure_default_configs(self):
        """Ensure default configurations exist"""
        defaults = [
            ServerConfig(
                name="Local Development",
                server_type=ServerType.LOCALHOST,
                host="localhost",
                port=12345,
                description="Local development server"
            ),
            ServerConfig(
                name="Local Network",
                server_type=ServerType.LOCALHOST,
                host="0.0.0.0",
                port=12345,
                description="Local network server (accessible from other devices)"
            ),
            ServerConfig(
                name="AWS Lambda (Example)",
                server_type=ServerType.AWS_LAMBDA,
                host="your-api-gateway-url.amazonaws.com",
                port=443,
                use_ssl=True,
                region="us-east-1",
                function_name="gomoku-server",
                description="AWS Lambda serverless deployment"
            ),
            ServerConfig(
                name="Azure Functions (Example)",
                server_type=ServerType.AZURE_FUNCTIONS,
                host="your-function-app.azurewebsites.net",
                port=443,
                use_ssl=True,
                function_name="gomoku-server",
                description="Azure Functions serverless deployment"
            )
        ]
        
        for default_config in defaults:
            if default_config.name not in self.configs:
                self.configs[default_config.name] = default_config
        
        # Set default current config if none set
        if not self.current_config and self.configs:
            self.current_config = "Local Development"
        
        self._save_configs()
    
    def add_config(self, config: ServerConfig) -> bool:
        """Add a new server configuration"""
        if config.name in self.configs:
            return False  # Config already exists
        
        self.configs[config.name] = config
        self._save_configs()
        return True
    
    def update_config(self, name: str, config: ServerConfig) -> bool:
        """Update an existing server configuration"""
        if name not in self.configs:
            return False
        
        # If name changed, remove old and add new
        if name != config.name:
            del self.configs[name]
            if self.current_config == name:
                self.current_config = config.name
        
        self.configs[config.name] = config
        self._save_configs()
        return True
    
    def remove_config(self, name: str) -> bool:
        """Remove a server configuration"""
        if name not in self.configs:
            return False
        
        del self.configs[name]
        
        # Update current config if it was removed
        if self.current_config == name:
            self.current_config = list(self.configs.keys())[0] if self.configs else None
        
        self._save_configs()
        return True
    
    def set_current_config(self, name: str) -> bool:
        """Set the current active configuration"""
        if name not in self.configs:
            return False
        
        self.current_config = name
        self._save_configs()
        return True
    
    def get_current_config(self) -> Optional[ServerConfig]:
        """Get the current active configuration"""
        if self.current_config and self.current_config in self.configs:
            return self.configs[self.current_config]
        return None
    
    def get_config(self, name: str) -> Optional[ServerConfig]:
        """Get a specific configuration by name"""
        return self.configs.get(name)
    
    def get_all_configs(self) -> Dict[str, ServerConfig]:
        """Get all configurations"""
        return self.configs.copy()
    
    def get_config_names(self) -> List[str]:
        """Get list of all configuration names"""
        return list(self.configs.keys())
    
    def get_connection_info(self) -> Optional[tuple]:
        """Get connection info (host, port) for current config"""
        config = self.get_current_config()
        if config:
            return (config.host, config.port)
        return None


# Global instance
server_config_manager = ServerConfigManager()


def get_server_config() -> ServerConfigManager:
    """Get the global server configuration manager"""
    return server_config_manager

