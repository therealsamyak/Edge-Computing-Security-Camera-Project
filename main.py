import face_recognition
import os
import glob

# File to test
test_filename = "obama.jpg"

# Get all JPGs in the folder except the test file
known_files = [f for f in glob.glob("*.jpg") if f != test_filename]
known_encodings = []

# Encode known faces
for file in known_files:
    image = face_recognition.load_image_file(file)
    encodings = face_recognition.face_encodings(image)
    if len(encodings) > 0:
        known_encodings.append((file, encodings[0]))
    else:
        print(f"⚠️ No face found in {file}, skipping.")

# Load test image
test_image = face_recognition.load_image_file(test_filename)
test_encodings = face_recognition.face_encodings(test_image)

if len(test_encodings) == 0:
    print("❌ No face found in test image.")
else:
    test_encoding = test_encodings[0]

    matches = []
    for filename, known_encoding in known_encodings:
        result = face_recognition.compare_faces([known_encoding], test_encoding)[0]
        if result:
            matches.append(filename)

    if matches:
        print("✅ Face matched with:")
        for match in matches:
            print(f"  - {match}")
    else:
        print("🆕 Unique / Unrecognized face.")
