"""
Secure subprocess execution utilities for the TTS application.
"""

import os
import shlex
import subprocess
import tempfile
from typing import List, Optional, Tuple, Union


class SubprocessError(Exception):
    """Custom exception for subprocess errors."""
    pass


class SecureSubprocessRunner:
    """
    Secure subprocess runner with argument sanitization and timeout handling.
    """
    
    def __init__(self, timeout: int = 300):
        """
        Initialize the secure subprocess runner.
        
        Args:
            timeout: Default timeout in seconds for subprocess operations
        """
        self.timeout = timeout
        self.allowed_commands = {
            'say': {
                'path': '/usr/bin/say',
                'allowed_args': ['-v', '-o', '-f', '-r', '--file-format', '--data-format', '--channels', '--bit-rate', '--quality'],
                'max_args': 20
            },
            'ffmpeg': {
                'path': None,  # Will be resolved from PATH
                'allowed_args': ['-f', '-i', '-c', '-safe', '-y', '-q:a', '-version'],
                'max_args': 50
            }
        }
    
    def _sanitize_argument(self, arg: str) -> str:
        """
        Sanitizes a command argument to prevent injection attacks.
        
        Args:
            arg: The argument to sanitize
            
        Returns:
            Sanitized argument
        """
        # Remove null bytes
        arg = arg.replace('\x00', '')
        
        # Check for dangerous characters
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
        for char in dangerous_chars:
            if char in arg:
                raise SubprocessError(f"Dangerous character '{char}' found in argument: {arg}")
        
        # Limit argument length
        if len(arg) > 1000:
            raise SubprocessError(f"Argument too long: {len(arg)} characters (max: 1000)")
        
        return arg
    
    def _validate_command(self, command: str, args: List[str]) -> Tuple[str, List[str]]:
        """
        Validates and sanitizes a command and its arguments.
        
        Args:
            command: The command to execute
            args: List of arguments for the command
            
        Returns:
            Tuple of (validated_command_path, sanitized_args)
        """
        if command not in self.allowed_commands:
            raise SubprocessError(f"Command '{command}' is not allowed")
        
        cmd_config = self.allowed_commands[command]
        
        # Validate number of arguments
        if len(args) > cmd_config['max_args']:
            raise SubprocessError(f"Too many arguments for '{command}': {len(args)} (max: {cmd_config['max_args']})")
        
        # Determine command path
        if cmd_config['path']:
            cmd_path = cmd_config['path']
            if not os.path.exists(cmd_path):
                raise SubprocessError(f"Command '{command}' not found at expected path: {cmd_path}")
        else:
            # Resolve from PATH
            cmd_path = self._find_command_in_path(command)
            if not cmd_path:
                raise SubprocessError(f"Command '{command}' not found in PATH")
        
        # Sanitize and validate arguments
        sanitized_args = []
        i = 0
        while i < len(args):
            arg = args[i]
            
            # Sanitize the argument
            sanitized_arg = self._sanitize_argument(arg)
            
            # Check if it's a valid flag
            if sanitized_arg.startswith('-'):
                if sanitized_arg not in cmd_config['allowed_args']:
                    raise SubprocessError(f"Argument '{sanitized_arg}' is not allowed for command '{command}'")
            
            sanitized_args.append(sanitized_arg)
            i += 1
        
        return cmd_path, sanitized_args
    
    def _find_command_in_path(self, command: str) -> Optional[str]:
        """
        Finds a command in the system PATH.
        
        Args:
            command: The command to find
            
        Returns:
            Full path to the command or None if not found
        """
        for path in os.environ.get('PATH', '').split(os.pathsep):
            if not path:
                continue
            
            cmd_path = os.path.join(path, command)
            if os.path.isfile(cmd_path) and os.access(cmd_path, os.X_OK):
                return cmd_path
        
        return None
    
    def run_command(
        self,
        command: str,
        args: List[str],
        input_data: Optional[str] = None,
        timeout: Optional[int] = None,
        capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Runs a command securely with the given arguments.
        
        Args:
            command: The command to run
            args: List of arguments
            input_data: Optional input data to pass to the command
            timeout: Optional timeout override
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            CompletedProcess object with the result
        """
        # Validate and sanitize the command
        cmd_path, sanitized_args = self._validate_command(command, args)
        
        # Build the full command
        full_command = [cmd_path] + sanitized_args
        
        # Use provided timeout or default
        actual_timeout = timeout if timeout is not None else self.timeout
        
        try:
            result = subprocess.run(
                full_command,
                input=input_data,
                text=True,
                capture_output=capture_output,
                timeout=actual_timeout,
                check=False,  # Don't raise on non-zero exit code
                env=self._get_secure_environment()
            )
            
            return result
            
        except subprocess.TimeoutExpired:
            raise SubprocessError(f"Command '{command}' timed out after {actual_timeout} seconds")
        except FileNotFoundError:
            raise SubprocessError(f"Command '{command}' not found")
        except Exception as e:
            raise SubprocessError(f"Unexpected error running command '{command}': {e}")
    
    def _get_secure_environment(self) -> dict:
        """
        Returns a secure environment for subprocess execution.
        
        Returns:
            Dictionary of environment variables
        """
        # Start with a minimal environment
        secure_env = {
            'PATH': os.environ.get('PATH', ''),
            'HOME': os.environ.get('HOME', ''),
            'USER': os.environ.get('USER', ''),
            'LANG': os.environ.get('LANG', 'en_US.UTF-8'),
            'LC_ALL': os.environ.get('LC_ALL', 'en_US.UTF-8'),
        }
        
        # Remove any None values
        return {k: v for k, v in secure_env.items() if v}


def create_secure_temp_file(content: str, suffix: str = '.txt') -> str:
    """
    Creates a secure temporary file with the given content.
    
    Args:
        content: Content to write to the file
        suffix: File extension suffix
        
    Returns:
        Path to the created temporary file
    """
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=suffix,
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(content)
            temp_path = f.name
        
        # Set secure permissions (readable/writable by owner only)
        os.chmod(temp_path, 0o600)
        
        return temp_path
        
    except Exception as e:
        raise SubprocessError(f"Failed to create secure temporary file: {e}")


def secure_file_cleanup(file_path: str) -> None:
    """
    Securely removes a file.
    
    Args:
        file_path: Path to the file to remove
    """
    try:
        if os.path.exists(file_path):
            # Overwrite with random data before deletion (basic secure deletion)
            try:
                with open(file_path, 'r+b') as f:
                    length = f.seek(0, 2)  # Seek to end to get length
                    f.seek(0)
                    f.write(os.urandom(length))
                    f.flush()
                    os.fsync(f.fileno())
            except Exception:
                # If overwriting fails, just delete normally
                pass
            
            os.remove(file_path)
            
    except Exception as e:
        # Log error but don't raise - file cleanup is best effort
        print(f"Warning: Could not securely remove file {file_path}: {e}")


# Global instance for convenience
secure_runner = SecureSubprocessRunner() 