@echo off

rem ============================================================================
rem set-env.example.bat
rem
rem Optional local published-image selection for local-published-smoke mode.
rem
rem Copy this file to set-env.bat and choose either one common tag or separate
rem client/responder tags. The actual set-env.bat should remain machine/local
rem configuration rather than committed shared configuration.
rem
rem Selection precedence for the client:
rem   DIARIES_CLIENT_IMAGE_TAG
rem   DIARIES_IMAGE_TAG
rem   integration
rem
rem Selection precedence for the responder:
rem   DIARIES_RESPONDER_IMAGE_TAG
rem   DIARIES_IMAGE_TAG
rem   integration
rem ============================================================================

rem To use one tag for both images:
rem set "DIARIES_IMAGE_TAG=0.0.9"
rem set "DIARIES_CLIENT_IMAGE_TAG="
rem set "DIARIES_RESPONDER_IMAGE_TAG="

rem To use different tags:
rem set "DIARIES_IMAGE_TAG="
rem set "DIARIES_CLIENT_IMAGE_TAG=0.0.9-build-64"
rem set "DIARIES_RESPONDER_IMAGE_TAG=0.0.9-build-73"

set "DIARIES_IMAGE_TAG=integration"
set "DIARIES_CLIENT_IMAGE_TAG="
set "DIARIES_RESPONDER_IMAGE_TAG="

exit /b 0
