import os
import subprocess
import sys

def generate_protos():
    """
    Generate gNMI protobuf files from the proto definitions
    """
    # Create proto directories
    os.makedirs('proto/gnmi', exist_ok=True)
    os.makedirs('proto/gnmi_ext', exist_ok=True)
    
    # Download the proto files
    proto_files = {
        'proto/gnmi/gnmi.proto': 'https://raw.githubusercontent.com/openconfig/gnmi/master/proto/gnmi/gnmi.proto',
        'proto/gnmi_ext/gnmi_ext.proto': 'https://raw.githubusercontent.com/openconfig/gnmi/master/proto/gnmi_ext/gnmi_ext.proto'
    }
    
    for proto_path, url in proto_files.items():
        subprocess.run(['curl', '-o', proto_path, url], check=True)
        
        # Fix import path in gnmi.proto
        if 'gnmi.proto' in proto_path:
            with open(proto_path, 'r') as f:
                content = f.read()
            content = content.replace(
                'import "github.com/openconfig/gnmi/proto/gnmi_ext/gnmi_ext.proto";',
                'import "gnmi_ext/gnmi_ext.proto";'
            )
            with open(proto_path, 'w') as f:
                f.write(content)
    
    # Generate Python files from proto
    subprocess.run([
        '/opt/ufm/venv_ufm/bin/python3', '-m', 'grpc_tools.protoc',
        '-I./proto',
        '--python_out=.',
        '--grpc_python_out=.',
        'proto/gnmi/gnmi.proto',
        'proto/gnmi_ext/gnmi_ext.proto'
    ], check=True)
    
    print("Successfully generated gNMI protobuf files")

if __name__ == '__main__':
    generate_protos() 