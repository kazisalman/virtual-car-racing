import cv2
from hand_tracker import HandTracker
from game_engine import GameEngine

def main():
    # Initialize OpenCV
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    tracker = HandTracker()
    engine = GameEngine(800, 600)
    
    running = True
    while running:
        success, frame = cap.read()
        if not success:
            break
            
        # Flip the frame horizontally for a selfie-view display
        frame = cv2.flip(frame, 1)
        
        # Process hand tracking
        frame, steering_angle, hands_detected = tracker.process_frame(frame)
        
        # Update and render game
        running = engine.update(steering_angle)
        engine.render(hands_detected)
        
        # Show the webcam feed in a small window
        preview = cv2.resize(frame, (320, 240))
        cv2.imshow("Webcam - Hand Tracking", preview)
        
        if cv2.waitKey(1) & 0xFF == 27: # ESC key
            break

    cap.release()
    cv2.destroyAllWindows()
    engine.quit()

if __name__ == "__main__":
    main()
