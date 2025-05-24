#pragma once

#include <unity.h>

#include "WiFi.h"

/* Test that WiFi connected */
void test_wifi_connection(void)
{
    wifi_init();
    vTaskDelay(1500 / portTICK_PERIOD_MS);
    TEST_ASSERT_TRUE(is_wifi_connected());
}

/* Test that WiFi disconnected */
void test_wifi_disconnection(void)
{
    esp_wifi_disconnect();
    esp_wifi_stop();
    vTaskDelay(1500 / portTICK_PERIOD_MS);
    TEST_ASSERT_FALSE(is_wifi_connected());
}

/* Run all WiFi tests */
void runWiFiTests(void)
{
    RUN_TEST(test_wifi_connection);
    vTaskDelay(100 / portTICK_PERIOD_MS);
    RUN_TEST(test_wifi_disconnection);
}
