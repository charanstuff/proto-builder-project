#!/usr/bin/env python3
import docker

def cleanup_containers(port=5000, runtime_label="runtime_project"):
    """
    Stops and removes any Docker containers that either:
    - Are binding to the specified host port (default 5000), or
    - Have a label with key 'runtime_project' (regardless of value).

    Adjust runtime_label as needed.
    """
    client = docker.from_env()
    containers = client.containers.list(all=True)
    for container in containers:
        remove_container = False
        # Check if container binds to the specified host port.
        ports = container.attrs.get('NetworkSettings', {}).get('Ports', {})
        if ports:
            for container_port, mappings in ports.items():
                if mappings:
                    for mapping in mappings:
                        if mapping.get("HostPort") == str(port):
                            remove_container = True
                            break
                if remove_container:
                    break

        # Check if container has the specific runtime label.
        labels = container.attrs.get("Config", {}).get("Labels", {})
        if labels and runtime_label in labels:
            remove_container = True

        if remove_container:
            print(f"Cleaning container {container.name} (ID: {container.id})")
            try:
                container.stop()
                container.remove(force=True)
                print("Container stopped and removed successfully.")
            except Exception as e:
                print(f"Error cleaning container {container.name}: {e}")
    client.close()

if __name__ == "__main__":
    cleanup_containers()
