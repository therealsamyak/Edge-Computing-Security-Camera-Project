// ESP32 Libraries
#include <nvs_flash.h>

// RTOS Libraries
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

// Unity (Testing)
#include <unity.h>
#define LOG_LOCAL_LEVEL ESP_LOG_WARN

// Test Files
#include "test_wifi.h"

int runUnityTests(void)
{
    UNITY_BEGIN();
    runWiFiTests();

    // add more test functions here

    return UNITY_END();
}

void app_main(void)
{
    // check flash
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND)
    {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    // run tests
    runUnityTests();
}
