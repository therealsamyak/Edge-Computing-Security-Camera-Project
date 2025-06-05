import os
import re
import sys

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


# Determine both possible sources (camera index 1 and an optional stream URL)
camera_source = 1
stream_source = sys.argv[1] if len(sys.argv) > 1 else None

# Pre‐open both captures (if stream_source is None, we’ll leave cap_stream as None)
cap_cam = cv2.VideoCapture(camera_source)
cap_stream = None
if stream_source:
    cap_stream = cv2.VideoCapture(stream_source)

# Verify that at least one source opened successfully
if not cap_cam.isOpened():
    print(f"❌ Could not access camera (index {camera_source})")
    sys.exit(1)

if stream_source and not cap_stream.isOpened():
    print(f"❌ Could not access stream ({stream_source})")
    sys.exit(1)

# Decide which capture to use initially
if stream_source:
    using_stream = True
    current_cap = cap_stream
    location_label_stream = "checkout"
    location_label_cam = "entrance/exit"
    location_label = location_label_stream
else:
    using_stream = False
    current_cap = cap_cam
    location_label_cam = "entrance/exit"
    location_label = location_label_cam

# Load previously saved unknown faces into memory
known_face_encodings = []
known_face_names = []
for fname in os.listdir():
    if re.match(r"unknown_\d+\.png", fname):
        image = face_recognition.load_image_file(fname)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_face_encodings.append(encodings[0])
            known_face_names.append(fname.replace(".png", ""))
        else:
            print(f"⚠️ Warning: No face found in {fname}")

print("✅ Video capture running. Press 'q' to quit, 's' to swap source.")

face_locations = []
face_encodings = []
face_names = []
process_this_frame = 0

while True:
    ret, frame = current_cap.read()
    if not ret:
        print("❌ Failed to read frame from current source.")
        break

    # ── face‐recognition block ─────────────────────────────────────────────────
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    if process_this_frame >= 60:
        process_this_frame = 0
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(
            rgb_small_frame, face_locations
        )

        face_names = []
        for face_encoding, (top, right, bottom, left) in zip(
            face_encodings, face_locations
        ):
            matches = face_recognition.compare_faces(
                known_face_encodings, face_encoding
            )
            face_distances = face_recognition.face_distance(
                known_face_encodings, face_encoding
            )

            name = "Unknown"
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if (
                    matches[best_match_index]
                    and face_distances[best_match_index] < 0.45
                ):
                    name = known_face_names[best_match_index]

            if name == "Unknown":
                already_known = False
                for known_encoding in known_face_encodings:
                    if np.linalg.norm(known_encoding - face_encoding) < 0.50:
                        already_known = True
                        break

                if not already_known:
                    new_unknown_name = get_next_unknown_id()
                    filename = f"{new_unknown_name}.png"

                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4
                    face_image = frame[top:bottom, left:right]

                    cv2.imwrite(filename, face_image)
                    known_face_encodings.append(face_encoding)
                    known_face_names.append(new_unknown_name)
                    name = new_unknown_name
                    print(f"[+] Saved new unknown face as {filename}")
            else:
                matched_name = name
                matched_filename = f"{matched_name}.png"
                top_full, right_full, bottom_full, left_full = (
                    top * 4,
                    right * 4,
                    bottom * 4,
                    left * 4,
                )
                face_image = frame[
                    top_full:bottom_full,
                    left_full : left_full + (right_full - left_full),
                ]
                cv2.imwrite(matched_filename, face_image)
                print(f"[✓] Updated snapshot for {matched_name}")

            face_names.append(name)

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

    # ── draw boxes & text ─────────────────────────────────────────────────────
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

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        print("😁 Quitting gracefully")
        break

    elif key == ord("s") and stream_source is not None:
        # Simply switch which capture object we read from
        using_stream = not using_stream
        if using_stream:
            current_cap = cap_stream
            location_label = location_label_stream
            print("🔄 Switched to stream source.")
        else:
            current_cap = cap_cam
            location_label = location_label_cam
            print("🔄 Switched to camera source.")

        # Immediately continue so the very next iteration does a fresh read()
        continue

# Clean up both captures at the end
cap_cam.release()
if cap_stream:
    cap_stream.release()
cv2.destroyAllWindows()
