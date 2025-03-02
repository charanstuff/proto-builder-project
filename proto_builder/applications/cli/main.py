from pathlib import Path
from proto_builder.core.preprompts_holder import PrepromptsHolder


def main():
    """
    Main entry point for the CLI application.
    Demonstrates retrieving preprompts using PrepromptsHolder.
    """
    # # Assuming preprompts are stored in a 'preprompts' directory at the project root
    # preprompts_path = Path(__file__).parent.parent / "preprompts"
    
    # # Initialize the PrepromptsHolder
    # holder = PrepromptsHolder(preprompts_path)
    
    # # Get all preprompts
    # preprompts = holder.get_preprompts()
    
    # # Print the retrieved preprompts
    # for name, content in preprompts.items():
    #     print(f"\nPreprompt: {name}")
    #     print("-" * 40)
    #     print(content)
    print("test")


if __name__ == "__main__":
    main()