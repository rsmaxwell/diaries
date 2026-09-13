package com.rsmaxwell.diaries.responder.utilities;

/** Immutable metadata obtained from decoding supported image bytes. */
public record InspectedImage(String mimeType, int width, int height, long size, String checksum) {
    public InspectedImage {
        if (!java.util.Set.of("image/jpeg", "image/png", "image/gif", "image/webp").contains(mimeType)
                || width <= 0 || height <= 0 || size <= 0 || checksum == null || !checksum.matches("[0-9a-f]{64}"))
            throw new IllegalArgumentException("Invalid inspected image metadata");
    }
}
