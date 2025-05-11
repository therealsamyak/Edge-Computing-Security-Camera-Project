// ESP32 Libraries
#include <esp_log.h>
#include <nvs_flash.h>

// RTOS Libraries
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

// Custom Libraries
#include "WiFi.h"
#include "TimeSync.h"

static const char *MAIN_TAG = "MAIN";

void app_main()
{
    // Log program Starting
    ESP_LOGI(MAIN_TAG, "Starting ESP32 Application...");

    //
    //  Initialize Everything
    //

    // checkf falsh
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND)
    {
        ESP_LOGW(MAIN_TAG, "NVS Flash Full. Erasing...");
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    // Initialize WiFi
    ESP_LOGI(MAIN_TAG, "Initializing Wi-Fi...");
    wifi_init();

    vTaskDelay(5000 / portTICK_PERIOD_MS);

    if (is_wifi_connected())
    {
        ESP_LOGI(MAIN_TAG, "Wi-Fi setup complete!");
    }
    else
    {
        ESP_LOGE(MAIN_TAG, "Wi-Fi setup error. Check configurations...");
    }

    // Sync Time
    ESP_LOGI(MAIN_TAG, "Getting Current Time...");
    sync_time(0);

    vTaskDelay(5000 / portTICK_PERIOD_MS);
    ESP_LOGI(MAIN_TAG, "Time Synced!");

    // Loop For State Machine
    while (1)
    {
        // iterate every 10s
        ESP_LOGI(MAIN_TAG, "Placeholder...");
        vTaskDelay(10000 / portTICK_PERIOD_MS);
    }

    ESP_LOGI(MAIN_TAG, "All tests completed.");
}