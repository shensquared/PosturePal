import cv2

def test_camera(index=0):
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"Camera {index} could not be opened.")
        return

    # Try to read a frame
    ret, frame = cap.read()
    if not ret:
        print(f"Camera {index} opened but failed to read a frame.")
        cap.release()
        return

    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"Camera {index} is working!")
    print(f"Resolution: {int(width)}x{int(height)}")
    print(f"FPS: {fps}")

    # Show a preview window
    cv2.imshow(f"Camera {index} Preview", frame)
    print("Press any key in the preview window to close.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cap.release()

if __name__ == "__main__":
    print("Testing first 5 camera indices...")
    for i in range(5):
        print("-" * 40)
        test_camera(i) 