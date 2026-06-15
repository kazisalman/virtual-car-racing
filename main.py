import sys
import cv2
from hand_tracker import HandTracker
from phone_tracker import PhoneTracker
from game_engine import GameEngine


# ──────────────────────────────────────────────────────────────────────────────
# Startup: let the user pick control mode in the terminal
# ──────────────────────────────────────────────────────────────────────────────

def choose_mode():
    print()
    print("╔══════════════════════════════════════╗")
    print("║      🏎️   Virtual Steering Racing     ║")
    print("╠══════════════════════════════════════╣")
    print("║  Select your control mode:           ║")
    print("║                                      ║")
    print("║   1  →  Webcam Hand Tracking         ║")
    print("║   2  →  Phone Gyroscope (OnePlus 11) ║")
    print("║                                      ║")
    print("╚══════════════════════════════════════╝")

    while True:
        choice = input("  Enter 1 or 2: ").strip()
        if choice in ("1", "2"):
            break
        print("  ⚠️  Please enter 1 or 2.")

    if choice == "2":
        print()
        print("  Open SensorServer on your phone.")
        print("  The app shows an IP like  192.168.x.x")
        phone_ip = input("  Enter your phone IP: ").strip()
        return "phone", phone_ip

    return "hands", None


# ──────────────────────────────────────────────────────────────────────────────
# Main game loop
# ──────────────────────────────────────────────────────────────────────────────

def main():
    mode, phone_ip = choose_mode()

    # ── Initialise the chosen tracker ───────────────────────────────────
    cap     = None
    tracker = None
    phone   = None

    if mode == "hands":
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌  Could not open webcam. Exiting.")
            return
        tracker = HandTracker()
        print("\n  ✅  Webcam ready! Place both hands in view to start steering.\n")

    else:   # phone gyro
        phone = PhoneTracker(phone_ip)
        phone.start()
        print("\n  ✅  Connecting to phone … (the game starts immediately).\n")
        print("  👉  Hold your phone FLAT, screen facing up, like a steering wheel.")
        print("      Tilt LEFT  →  car goes left")
        print("      Tilt RIGHT →  car goes right\n")

    engine  = GameEngine(800, 600)
    running = True

    while running:
        steering_angle = 0.0
        connected      = False

        # ── Get steering input ───────────────────────────────────────────
        if mode == "hands":
            success, frame = cap.read()
            if not success:
                break
            frame = cv2.flip(frame, 1)
            frame, steering_angle, connected = tracker.process_frame(frame)

            # Show webcam preview
            preview = cv2.resize(frame, (320, 240))
            cv2.imshow("Webcam – Hand Tracking", preview)
            if cv2.waitKey(1) & 0xFF == 27:   # ESC
                break

        else:   # phone
            steering_angle, connected = phone.get_steering()

        # ── Update & render ──────────────────────────────────────────────
        running = engine.update(steering_angle)
        engine.render(connected)

    # ── Cleanup ──────────────────────────────────────────────────────────
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    engine.quit()


if __name__ == "__main__":
    main()
