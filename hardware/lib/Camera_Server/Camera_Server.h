#pragma once

#ifdef __cplusplus
extern "C"
{
#endif

/** the multipart boundary string used in MJPEG stream headers */
#define STREAM_BOUNDARY "boundary"

    /**
     * @brief  Initialize camera hardware and start HTTP MJPEG stream on port 80.
     */
    void startCameraServer(void);

#ifdef __cplusplus
}
#endif
