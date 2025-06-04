import face_recognition
import cv2
import numpy as np
import os

# Create folder for unknown faces if it doesn't exist
os.makedirs("unknown_faces", exist_ok=True)

# Load and encode known faces
known_faces = [
    ("Barack Obama", "obama.jpg"),
    ("Joe Biden", "biden.jpg"),
]

known_face_encodings = []
known_face_names = []

for name, file in known_faces:
    image = face_recognition.load_image_file(file)
    encodings = face_recognition.face_encodings(image)
    if encodings:
        known_face_encodings.append(encodings[0])
        known_face_names.append(name)
    else:
        print(f"⚠️ Warning: No face found in {file}")

# Track unknowns
unknown_encodings = []
unknown_names = []
unknown_id_counter = 1

# Start webcam
video_capture = cv2.VideoCapture(0)
if not video_capture.isOpened():
    print("❌ Could not access webcam.")
    exit()

print("✅ Webcam running. Press 'q' to quit.")

face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

while True:
    ret, frame = video_capture.read()
    if not ret:
        print("❌ Failed to read from webcam.")
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    if process_this_frame:
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []

        for i, face_encoding in enumerate(face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings + unknown_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(known_face_encodings + unknown_encodings, face_encoding)
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    if best_match_index < len(known_face_names):
                        name = known_face_names[best_match_index]
                    else:
                        name = unknown_names[best_match_index - len(known_face_names)]

            # Handle new unknown
            if name == "Unknown":
                # Scale face coords back up to full size
                top, right, bottom, left = face_locations[i]
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Crop the face and save
                face_crop = frame[top:bottom, left:right]
                filename = f"unknown_faces/unknown_{unknown_id_counter}.jpg"
                cv2.imwrite(filename, face_crop)

                # Store the encoding and label
                unknown_encodings.append(face_encoding)
                unknown_names.append(f"Unknown #{unknown_id_counter}")
                name = f"Unknown #{unknown_id_counter}"
                unknown_id_counter += 1

            face_names.append(name)

    process_this_frame = not process_this_frame

    # Draw results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 1)

    cv2.imshow('Face Recognition', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
