#include "Camera_Server.h"
#include <esp_camera.h>
#include <esp_http_server.h>
#include <esp_log.h>
#include <string.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

static const char *TAG = "camera_httpd";

// Pin definitions for FREENOVE ESP32 WROVER camera module (OV2640)
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27

#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

// ----------------------------------------------------------------------------
// HTTP “/mjpg/video.mjpg” handler — streams multipart JPEG frames
// ----------------------------------------------------------------------------
static esp_err_t stream_handler(httpd_req_t *req)
{
    esp_err_t res;
    camera_fb_t *fb = NULL;
    char part_buf[128];

    // build and set our content-type header with boundary
    char ct_header[64];
    snprintf(ct_header, sizeof(ct_header),
             "multipart/x-mixed-replace;boundary=%s",
             STREAM_BOUNDARY);
    res = httpd_resp_set_type(req, ct_header);
    if (res != ESP_OK)
        return res;

    while (true)
    {
        fb = esp_camera_fb_get();
        if (!fb)
        {
            ESP_LOGE(TAG, "Camera capture failed");
            httpd_resp_send_500(req);
            return ESP_FAIL;
        }

        size_t jpg_len;
        uint8_t *jpg_buf;
        if (fb->format != PIXFORMAT_JPEG)
        {
            bool ok = frame2jpg(fb, 80, &jpg_buf, &jpg_len);
            esp_camera_fb_return(fb);
            if (!ok)
            {
                ESP_LOGE(TAG, "JPEG conversion failed");
                httpd_resp_send_500(req);
                return ESP_FAIL;
            }
        }
        else
        {
            jpg_buf = fb->buf;
            jpg_len = fb->len;
        }

        // send boundary + headers
        int hlen = snprintf(part_buf, sizeof(part_buf),
                            "\r\n--%s\r\n"
                            "Content-Type: image/jpeg\r\n"
                            "Content-Length: %u\r\n\r\n",
                            STREAM_BOUNDARY,
                            (unsigned int)jpg_len);
        res = httpd_resp_send_chunk(req, part_buf, hlen);
        if (res != ESP_OK)
            break;

        // send JPEG payload
        res = httpd_resp_send_chunk(req, (const char *)jpg_buf, jpg_len);
        if (res != ESP_OK)
            break;

        // return buffers
        if (fb->format != PIXFORMAT_JPEG)
        {
            free(jpg_buf);
        }
        else
        {
            esp_camera_fb_return(fb);
        }

        // ~10 fps
        vTaskDelay(100 / portTICK_PERIOD_MS);
    }
    return res;
}

// ----------------------------------------------------------------------------
// HTTP “/” handler — simple HTML page embedding the MJPEG stream
// ----------------------------------------------------------------------------
static esp_err_t index_handler(httpd_req_t *req)
{
    const char *html =
        "<!DOCTYPE html><html><head><title>ESP32-CAM</title></head>"
        "<body><h1>ESP32-CAM MJPEG Stream</h1>"
        "<img src=\"/mjpg/video.mjpg\" />"
        "</body></html>";
    httpd_resp_set_type(req, "text/html");
    return httpd_resp_send(req, html, strlen(html));
}

static const httpd_uri_t uri_index = {
    .uri = "/",
    .method = HTTP_GET,
    .handler = index_handler,
    .user_ctx = NULL};

static const httpd_uri_t uri_stream = {
    .uri = "/mjpg/video.mjpg",
    .method = HTTP_GET,
    .handler = stream_handler,
    .user_ctx = NULL};

void startCameraServer(void)
{
    camera_config_t config = {
        .pin_pwdn = PWDN_GPIO_NUM,
        .pin_reset = RESET_GPIO_NUM,
        .pin_xclk = XCLK_GPIO_NUM,
        .pin_sscb_sda = SIOD_GPIO_NUM, // <— use new member names
        .pin_sscb_scl = SIOC_GPIO_NUM, // <— instead of pin_siod / pin_sioc
        .pin_d7 = Y9_GPIO_NUM,
        .pin_d6 = Y8_GPIO_NUM,
        .pin_d5 = Y7_GPIO_NUM,
        .pin_d4 = Y6_GPIO_NUM,
        .pin_d3 = Y5_GPIO_NUM,
        .pin_d2 = Y4_GPIO_NUM,
        .pin_d1 = Y3_GPIO_NUM,
        .pin_d0 = Y2_GPIO_NUM,
        .pin_vsync = VSYNC_GPIO_NUM,
        .pin_href = HREF_GPIO_NUM,
        .pin_pclk = PCLK_GPIO_NUM,
        .xclk_freq_hz = 20000000,
        .ledc_timer = LEDC_TIMER_0,
        .ledc_channel = LEDC_CHANNEL_0,
        .pixel_format = PIXFORMAT_JPEG,
        .frame_size = FRAMESIZE_VGA,
        .jpeg_quality = 10,
        .fb_count = 2,
        .grab_mode = CAMERA_GRAB_LATEST};

    if (esp_camera_init(&config) != ESP_OK)
    {
        ESP_LOGE(TAG, "Camera init failed");
        return;
    }

    httpd_handle_t server = NULL;
    httpd_config_t http_conf = HTTPD_DEFAULT_CONFIG();
    http_conf.server_port = 80;
    if (httpd_start(&server, &http_conf) == ESP_OK)
    {
        httpd_register_uri_handler(server, &uri_index);
        httpd_register_uri_handler(server, &uri_stream);
        ESP_LOGI(TAG, "Camera server started on port %d", http_conf.server_port);
    }
    else
    {
        ESP_LOGE(TAG, "Failed to start HTTP server");
    }
}
