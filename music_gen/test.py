import sys
from ableton_controllers import AbletonMetaController
import time

def main():
    try:
        controller = AbletonMetaController()
        controller.run()
        print("Controller running. Press Ctrl+C to exit.")
        # Keep the script running
        while True:
            time.sleep(0.1)  # Sleep for a short duration to avoid busy-waiting
    except KeyboardInterrupt:
        print("Controller stopped.")    
        sys.exit(0)

if __name__ == "__main__":
    main()