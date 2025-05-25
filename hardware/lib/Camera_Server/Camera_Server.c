#include "Camera_Server.h"

static esp_err_t stream_handler(httpd_req_t *req)
{
    camera_fb_t *fb = NULL;
    esp_err_t res = ESP_OK;
    char part_buf[128];

    // send content-type header (with boundary)
    char ct_header[64];
    snprintf(ct_header, sizeof(ct_header),
             "multipart/x-mixed-replace;boundary=%s",
             STREAM_BOUNDARY);
    res = httpd_resp_set_type(req, ct_header);
    if (res != ESP_OK)
    {
        return ESP_FAIL;
    }

    while (true)
    {
        fb = esp_camera_fb_get();
        if (!fb)
        {
            ESP_LOGE(STREAM_TAG, "Camera capture failed");
            break;
        }

        size_t jpg_len;
        uint8_t *jpg_buf;
        if (fb->format != PIXFORMAT_JPEG)
        {
            bool ok = frame2jpg(fb, 80, &jpg_buf, &jpg_len);
            esp_camera_fb_return(fb);
            if (!ok)
            {
                ESP_LOGE(STREAM_TAG, "JPEG conversion failed");
                break;
            }
        }
        else
        {
            jpg_buf = fb->buf;
            jpg_len = fb->len;
        }

        // multipart boundary + headers
        int hlen = snprintf(part_buf, sizeof(part_buf),
                            "\r\n--%s\r\n"
                            "Content-Type: image/jpeg\r\n"
                            "Content-Length: %u\r\n\r\n",
                            STREAM_BOUNDARY,
                            (unsigned int)jpg_len);
        res = httpd_resp_send_chunk(req, part_buf, hlen);
        if (res != ESP_OK)
        {
            // client disconnected or send error
            if (fb->format != PIXFORMAT_JPEG)
                free(jpg_buf);
            else
                esp_camera_fb_return(fb);
            break;
        }

        // image data
        res = httpd_resp_send_chunk(req, (const char *)jpg_buf, jpg_len);
        if (res != ESP_OK)
        {
            // client disconnected
            if (fb->format != PIXFORMAT_JPEG)
                free(jpg_buf);
            else
                esp_camera_fb_return(fb);
            break;
        }

        // return buffer for next frame
        if (fb->format != PIXFORMAT_JPEG)
        {
            free(jpg_buf);
        }
        else
        {
            esp_camera_fb_return(fb);
        }

        // throttle
        vTaskDelay(5);
    }

    return ESP_OK;
}

static esp_err_t index_handler(httpd_req_t *req)
{
    const char *html =
        "<!DOCTYPE html><html><head><title>ESP32-CAM</title></head>"
        "<body><h1>ESP32-CAM MJPEG Stream</h1>"
        "<img src=\"/mjpg/video.mjpg\" style=\"max-width:100%; height:auto;\" />"
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
        .pin_pwdn = -1,
        .pin_reset = -1,
        .pin_xclk = 21,
        .pin_sscb_sda = 26,
        .pin_sscb_scl = 27,
        .pin_d7 = 35,
        .pin_d6 = 34,
        .pin_d5 = 39,
        .pin_d4 = 36,
        .pin_d3 = 19,
        .pin_d2 = 18,
        .pin_d1 = 5,
        .pin_d0 = 4,
        .pin_vsync = 25,
        .pin_href = 23,
        .pin_pclk = 22,
        .xclk_freq_hz = 20000000,
        .ledc_timer = LEDC_TIMER_0,
        .ledc_channel = LEDC_CHANNEL_0,
        .pixel_format = PIXFORMAT_JPEG,
        .frame_size = 8,
        .jpeg_quality = 20,
        .fb_count = 3,
        .grab_mode = CAMERA_GRAB_LATEST,
        .fb_location = CAMERA_FB_IN_DRAM};

    if (esp_camera_init(&config) != ESP_OK)
    {
        ESP_LOGE(STREAM_TAG, "Camera init failed");
        return;
    }

    httpd_handle_t server = NULL;
    httpd_config_t http_conf = HTTPD_DEFAULT_CONFIG();
    http_conf.server_port = 80;
    http_conf.max_uri_handlers = 8;
    http_conf.max_resp_headers = 8;
    http_conf.send_wait_timeout = 5;
    http_conf.recv_wait_timeout = 5;
    http_conf.task_priority = 5;
    http_conf.stack_size = 8192;

    if (httpd_start(&server, &http_conf) == ESP_OK)
    {
        httpd_register_uri_handler(server, &uri_index);
        httpd_register_uri_handler(server, &uri_stream);

        esp_netif_ip_info_t ip;
        esp_netif_t *netif = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
        if (netif && esp_netif_get_ip_info(netif, &ip) == ESP_OK)
        {
            ESP_LOGI(STREAM_TAG,
                     "Broadcasting at " IPSTR "/mjpg/video.mjpg",
                     IP2STR(&ip.ip));
        }
        else
        {
            ESP_LOGW(STREAM_TAG, "Broadcasting (IP unknown) /mjpg/video.mjpg");
        }

        ESP_LOGI(STREAM_TAG, "Camera server started on port %d", http_conf.server_port);
    }
    else
    {
        ESP_LOGE(STREAM_TAG, "Failed to start HTTP server");
    }
}