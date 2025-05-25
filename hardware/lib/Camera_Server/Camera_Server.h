#pragma once

#include <esp_camera.h>
#include <esp_http_server.h>
#include <esp_log.h>
#include <esp_netif.h>
#include <string.h>
#include <freertos/task.h>
#include <sys/socket.h>
#include <netinet/tcp.h>

#define STREAM_BOUNDARY "boundary"
#define STREAM_TAG "camera_httpd"

void startCameraServer(void);