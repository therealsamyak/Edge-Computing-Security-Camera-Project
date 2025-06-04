import os
import sys
import time

import cv2
import face_recognition
import numpy as np
from dotenv import load_dotenv
from supabase import Client, create_client

# Load Supabase credentials from .env
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)


# Create folder for unknown faces if it doesn't exist
os.makedirs("unknown_faces", exist_ok=True)

# Determine video source (default=0 for webcam)
if len(sys.argv) > 1:
    video_source = sys.argv[1]
    location_label = "entrance/exit"
else:
    video_source = 0
    location_label = "checkout"

# Start capture
video_capture = cv2.VideoCapture(video_source)
if not video_capture.isOpened():
    print(f"❌ Could not access video source: {video_source}")
    sys.exit(1)

# Load and encode known faces
known_faces = [
    ("Barack Obama", "obama.jpg"),
    ("Joe Biden", "biden.jpg"),
]

known_face_encodings = []
known_face_names = []

for name, filename in known_faces:
    image = face_recognition.load_image_file(filename)
    encodings = face_recognition.face_encodings(image)
    if encodings:
        known_face_encodings.append(encodings[0])
        known_face_names.append(name)
    else:
        print(f"⚠️ Warning: No face found in {filename}")

# Track unknowns
unknown_encodings = []
unknown_names = []
unknown_id_counter = 1

print("✅ Video capture running. Press 'q' to quit.")

face_locations = []
face_encodings = []
face_names = []
process_this_frame = 0

last_supabase_insert = 0  # timestamp of last Supabase update (in seconds)

while True:
    ret, frame = video_capture.read()
    if not ret:
        print("❌ Failed to read frame.")
        break

    # Resize frame for faster processing and convert to RGB
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    if process_this_frame >= 60:
        process_this_frame = 0
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(
            rgb_small_frame, face_locations
        )
        face_names = []

        for i, face_encoding in enumerate(face_encodings):
            # Compare against known + previously seen unknowns
            all_encodings = known_face_encodings + unknown_encodings
            matches = face_recognition.compare_faces(all_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(
                all_encodings, face_encoding
            )
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    if best_match_index < len(known_face_names):
                        name = known_face_names[best_match_index]
                    else:
                        name = unknown_names[best_match_index - len(known_face_names)]

            # If still unknown, save a new face crop and encoding
            if name == "Unknown":
                top, right, bottom, left = face_locations[i]
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                face_crop = frame[top:bottom, left : left + (right - left)]
                filename = f"unknown_faces/unknown_{unknown_id_counter}.jpg"
                cv2.imwrite(filename, face_crop)

                unknown_encodings.append(face_encoding)
                new_unknown_label = f"Unknown #{unknown_id_counter}"
                unknown_names.append(new_unknown_label)
                name = new_unknown_label
                unknown_id_counter += 1

            face_names.append(name)

        # ───────────────────────────────────────────────────────────────
        # Insert into Supabase only when faces are detected and cooldown has elapsed
        current_time = time.time()
        if face_names and (current_time - last_supabase_insert >= 10):
            last_supabase_insert = current_time
            for name in face_names:
                if name.startswith("Unknown"):
                    person_id = name.lower().replace("unknown #", "unknown_")
                else:
                    person_id = name.split()[-1].lower()

                data = {"id": person_id, "location": location_label}
                try:
                    supabase.table("security_system").insert(data).execute()
                except Exception as e:
                    print(f"⚠️ Supabase insert failed for {person_id}: {e}")
        # ───────────────────────────────────────────────────────────────

    process_this_frame += 1

    # Draw boxes and labels on the original frame
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.rectangle(
            frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED
        )
        cv2.putText(
            frame,
            name,
            (left + 6, bottom - 6),
            cv2.FONT_HERSHEY_DUPLEX,
            0.75,
            (255, 255, 255),
            1,
        )

    cv2.imshow("Face Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

video_capture.release()
cv2.destroyAllWindows()
