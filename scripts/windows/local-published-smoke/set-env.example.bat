@echo off

rem -----------------------------------------------------------------
rem Local published-image smoke-test image selection
rem -----------------------------------------------------------------
rem
rem Selection order for the client:
rem   DIARIES_CLIENT_IMAGE_TAG
rem   DIARIES_IMAGE_TAG
rem   integration
rem
rem Selection order for the responder:
rem   DIARIES_RESPONDER_IMAGE_TAG
rem   DIARIES_IMAGE_TAG
rem   integration
rem
rem To use one tag for both images:
rem
rem set "DIARIES_IMAGE_TAG=0.0.9"
rem set "DIARIES_CLIENT_IMAGE_TAG="
rem set "DIARIES_RESPONDER_IMAGE_TAG="
rem
rem To use different tags:
rem
rem set "DIARIES_IMAGE_TAG="
rem set "DIARIES_CLIENT_IMAGE_TAG=0.0.9-build-57"
rem set "DIARIES_RESPONDER_IMAGE_TAG=0.0.9-build-71"

set "DIARIES_IMAGE_TAG=integration"
set "DIARIES_CLIENT_IMAGE_TAG="
set "DIARIES_RESPONDER_IMAGE_TAG="

exit /b 0
