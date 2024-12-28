import threading
import gui
import website

def run_web():
    try:
        website.main()
    except Exception as e:
        print(f"Error in web thread: {e}")

if __name__ == '__main__':
    try:
        # Start the web thread
        web_thread = threading.Thread(target=run_web, daemon=True)  # Daemon thread ensures it won't block program exit
        web_thread.start()

        # Run the GUI in the main thread
        gui.main()

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Shutting down gracefully.")
    finally:
        print("Waiting for web thread to finish...")
        web_thread.join(timeout=2)  # Optional timeout for a clean exit
        print("Program terminated.")
