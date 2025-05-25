#pragma once

#include <time.h>
#include <esp_sntp.h>
#include <esp_log.h>
#include <esp_err.h>
#include <stdint.h>
#include <stdlib.h>

#define TIME_TAG "TIME_SYNC"

esp_err_t sync_time(uint32_t interval_ms)
{
    // timezone
    setenv("TZ", "PST8PDT,M3.2.0,M11.1.0", 1);
    tzset();

    esp_sntp_setoperatingmode(SNTP_OPMODE_POLL);
    esp_sntp_setservername(0, "pool.ntp.org");
    if (interval_ms > 0)
    {
        esp_sntp_set_sync_interval(interval_ms);
    }
    esp_sntp_init();

    time_t now = 0;
    struct tm timeinfo = {0};
    int retry = 0;
    const int max_retries = 10;
    while (timeinfo.tm_year < (2020 - 1900) && ++retry < max_retries)
    {
        ESP_LOGI(TIME_TAG, "Waiting for system time to be set... (%d/%d)", retry, max_retries);
        vTaskDelay(2000 / portTICK_PERIOD_MS);
        time(&now);
        localtime_r(&now, &timeinfo);
    }

    if (timeinfo.tm_year < (2020 - 1900))
    {
        ESP_LOGE(TIME_TAG, "Failed to get NTP time!");
        return ESP_FAIL;
    }
    else
    {
        ESP_LOGI(TIME_TAG, "Time synchronized: %s", asctime(&timeinfo));
        return ESP_OK;
    }
}