# main.py

import argparse
from runtime_executor import ExecutionRequest, RuntimeExecutor

def main():
    parser = argparse.ArgumentParser(description="Runtime Environment Interface")
    parser.add_argument("--language", type=str, default="reactpython", help="Programming language (default: reactpython)")
    parser.add_argument("--source", type=str, required=True, help="Source of the code (git URL or local directory)")
    parser.add_argument("--command", type=str, required=True, help="Command to run inside the container")
    parser.add_argument("--workdir", type=str, default="/code", help="Working directory inside container")
    parser.add_argument("--dest", type=str, default="code_dir", help="Destination directory for code")
    parser.add_argument("--mode", type=str, default="local", help="Execution mode")
    
    args = parser.parse_args()
    
    req = ExecutionRequest(
        language=args.language,
        source=args.source,
        command=args.command,
        workdir=args.workdir,
        dest=args.dest,
        mode=args.mode
    )
    
    executor = RuntimeExecutor()
    executor.execute(req)

if __name__ == "__main__":
    main()
