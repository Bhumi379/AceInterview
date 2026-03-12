import cv2

def record_video(filename):

    cap = cv2.VideoCapture(0)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, 20.0, (640,480))

    print("Recording... Press 'q' to stop.")

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        out.write(frame)
        cv2.imshow("Recording Interview Answer", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()