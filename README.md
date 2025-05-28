# Edge-Computing-Security-Camera-Project

Read [https://docs.google.com/document/d/12N0_DUncdrwM2o6IFXWKLukxhMFFXXNmXrfzfeyNRBc/edit?tab=t.0#heading=h.wnz0o6isrx8s](this link) for more information.

## Hardware

```shell
cd hardware
```

We used PlatformIO for hardware implementations. The serial monitor outputs the streaming link for the server.

- Note: You have to be connected to the same WiFi network as the camera to view the stream.

## Backend

USE LINUX OR WSL TO RUN THIS. DOCKER NEEDS TO BE INSTALLED.

- ON WINDOWS, MAKE SURE DOCKER DESKTOP IS RUNNING IN THE BACKGROUND.

<br/>

```shell
cd backend
docker build -t security-backend .
docker run --rm -it security-backend
```

## Frontend

testing2
