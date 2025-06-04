import os
import sys
import time
import re

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

def get_next_unknown_id():
    """Finds the next available unknown_<index>.png in the current directory"""
    used_indices = set()
    for fname in os.listdir():
        match = re.match(r"unknown_(\d+)\.png", fname)
        if match:
            used_indices.add(int(match.group(1)))

    i = 1
    while i in used_indices:
        i += 1
    return f"unknown_{i}"

# Determine video source (default=0 for webcam)
if len(sys.argv) > 1:
    video_source = sys.argv[1]
    location_label = "entrance/exit"
    if (video_source) == "usb":
        video_source = 1
else:
    video_source = 0
    location_label = "checkout"

# Start capture
video_capture = cv2.VideoCapture(video_source)
if not video_capture.isOpened():
    print(f"❌ Could not access video source: {video_source}")
    sys.exit(1)

# Load known faces (optional static list can be commented out if unused)
known_faces = []

known_face_encodings = []
known_face_names = []

# Load previously saved unknown_X.png files as known faces
for fname in os.listdir():
    if re.match(r"unknown_\d+\.png", fname):
        image = face_recognition.load_image_file(fname)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_face_encodings.append(encodings[0])
            known_face_names.append(fname.replace(".png", ""))
        else:
            print(f"⚠️ Warning: No face found in {fname}")

print("✅ Video capture running. Press 'q' to quit.")

face_locations = []
face_encodings = []
face_names = []
process_this_frame = 0
last_supabase_insert = 0

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
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

            name = "Unknown"
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index] and face_distances[best_match_index] < 0.45:
                    name = known_face_names[best_match_index]

            if name == "Unknown":
                already_known = False
                for known_encoding in known_face_encodings:
                    if np.linalg.norm(known_encoding - face_encoding) < 0.4:
                        already_known = True
                        break

                if not already_known:
                    # Assign new filename
                    new_unknown_name = get_next_unknown_id()
                    filename = f"{new_unknown_name}.png"

                    # Convert original coords
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4
                    face_image = frame[top:bottom, left:right]

                    # Save image to disk
                    cv2.imwrite(filename, face_image)

                    # Add to known encodings
                    known_face_encodings.append(face_encoding)
                    known_face_names.append(new_unknown_name)
                    name = new_unknown_name
                    print(f"[+] Saved new unknown face as {filename}")
            else:
                # NEW: update image of known face
                matched_name = name
                matched_filename = f"{matched_name}.png"
                top_full, right_full, bottom_full, left_full = top * 4, right * 4, bottom * 4, left * 4
                face_image = frame[top_full:bottom_full, left_full:right_full]
                cv2.imwrite(matched_filename, face_image)
                print(f"[✓] Updated snapshot for {matched_name}")

            face_names.append(name)

        # Insert to Supabase with cooldown
        current_time = time.time()
        if face_names and (current_time - last_supabase_insert >= 10):
            last_supabase_insert = current_time
            for name in face_names:
                if name.startswith("unknown_"):
                    person_id = name
                else:
                    person_id = name.split()[-1].lower()
                data = {"id": person_id, "location": location_label}
                try:
                    supabase.table("security_system").insert(data).execute()
                except Exception as e:
                    print(f"⚠️ Supabase insert failed for {person_id}: {e}")

    process_this_frame += 1

    # Draw boxes and labels
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 6),
                    cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 1)

    cv2.imshow("Face Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

video_capture.release()
cv2.destroyAllWindows()
