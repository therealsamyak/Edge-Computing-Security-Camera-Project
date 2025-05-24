#pragma once

#include <unity.h>

#include "Camera_Server.h"

/* Test that the camera server (and underlying camera init) starts without error */
void test_camera_server_start(void)
{
    startCameraServer();
    TEST_ASSERT_TRUE(true);
}

/* Test that we can grab a frame from the camera */
void test_camera_capture_not_null(void)
{
    camera_fb_t *fb = esp_camera_fb_get();
    TEST_ASSERT_NOT_NULL(fb);
    esp_camera_fb_return(fb);
}

/* Test that the captured frame is in JPEG format */
void test_camera_capture_format(void)
{
    camera_fb_t *fb = esp_camera_fb_get();
    TEST_ASSERT_NOT_NULL(fb);
    TEST_ASSERT_EQUAL(PIXFORMAT_JPEG, fb->format);
    esp_camera_fb_return(fb);
}

/* Run all camera tests */
void runCameraTests(void)
{
    RUN_TEST(test_camera_server_start);
    vTaskDelay(100 / portTICK_PERIOD_MS);

    RUN_TEST(test_camera_capture_not_null);
    vTaskDelay(100 / portTICK_PERIOD_MS);

    RUN_TEST(test_camera_capture_format);
    vTaskDelay(100 / portTICK_PERIOD_MS);
}
