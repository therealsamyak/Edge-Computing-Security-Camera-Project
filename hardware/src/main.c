// ESP32 core
#include <nvs_flash.h>
#include <esp_log.h>

// User-Defined
#include "WiFi.h"
#include "Camera_Server.h"
#include "TimeSync.h"

static const char *TAG = "MAIN";

void app_main(void)
{

    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES ||
        ret == ESP_ERR_NVS_NEW_VERSION_FOUND)
    {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    // Initialize WiFi
    wifi_init();
    ESP_LOGI(TAG, "Wi-Fi connected");

    // Sync Time
    sync_time(0);
    ESP_LOGI(TAG, "Time synchronized");

    // Camera Server
    startCameraServer();

    // Idle
    while (1)
    {
        vTaskDelay(pdMS_TO_TICKS(10000));
    }
}
