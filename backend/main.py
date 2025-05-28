import glob

import face_recognition

test_filename = "obama.jpg"

known_files = [f for f in glob.glob("*.jpg") if f != test_filename]
known_encodings = []

for file in known_files:
    image = face_recognition.load_image_file(file)
    encodings = face_recognition.face_encodings(image)
    if encodings:
        known_encodings.append((file, encodings[0]))
    else:
        print(f"No face found in {file}, skipping.")

test_image = face_recognition.load_image_file(test_filename)
test_encodings = face_recognition.face_encodings(test_image)

if not test_encodings:
    print("No face found in test image.")
else:
    test_encoding = test_encodings[0]
    matches = []
    for filename, known_encoding in known_encodings:
        if face_recognition.compare_faces([known_encoding], test_encoding)[0]:
            matches.append(filename)
    if matches:
        print("Face matched with:")
        for match in matches:
            print(f"  - {match}")
    else:
        print("Unique / Unrecognized face.")
