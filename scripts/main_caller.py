import sys
#from modules import setup, launch
from src.light_minded import config, launch


def main():
    if len(sys.argv) < 2:
        print("Usage: python main_caller.py [config|launch]")
        sys.exit(1)

    print("Welcome to light-minded!")
    command = sys.argv[1].lower()

    if command == "config":
        print("Configuring...")
        config.run()
    elif command == "launch":
        #print("Launching...")
        launch.run()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


    #TODO: online vs offline user modes
    #TODO: analysis setup mode --> which parcellation, etc.

if __name__ == "__main__":
    main()

