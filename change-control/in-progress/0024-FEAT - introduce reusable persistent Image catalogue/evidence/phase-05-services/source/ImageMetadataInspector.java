package com.rsmaxwell.diaries.responder.utilities;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import java.util.zip.CRC32;
import javax.imageio.ImageIO;
import javax.imageio.ImageReader;
import javax.imageio.stream.MemoryCacheImageInputStream;

/** Strict content inspection. Extensions do not determine image identity or trigger renaming. */
public final class ImageMetadataInspector {
    public static final long DEFAULT_MAX_BYTES = 20L * 1024 * 1024;
    public static final long DEFAULT_MAX_PIXELS = 40_000_000;
    private static final Set<String> TYPES = Set.of("image/jpeg", "image/png", "image/gif", "image/webp");
    private final long maxBytes;
    private final long maxPixels;

    public record Inspection(long size, String checksum, Optional<InspectedImage> image) {
        public Inspection {
            if (size < 0 || checksum == null || !checksum.matches("[0-9a-f]{64}") || image == null)
                throw new IllegalArgumentException("Invalid inspection");
            if (image.isPresent() && (image.orElseThrow().size() != size || !image.orElseThrow().checksum().equals(checksum)))
                throw new IllegalArgumentException("Inconsistent image inspection");
        }
    }

    public ImageMetadataInspector() { this(DEFAULT_MAX_BYTES, DEFAULT_MAX_PIXELS); }
    public ImageMetadataInspector(long maxBytes, long maxPixels) {
        if (maxBytes < 1 || maxBytes >= Integer.MAX_VALUE || maxPixels < 1) throw new IllegalArgumentException("Invalid inspection limits");
        this.maxBytes = maxBytes;
        this.maxPixels = maxPixels;
    }
    public long maxBytes() { return maxBytes; }

    public Inspection inspect(Path file, String declaredMime, String expectedChecksum) throws IOException {
        return inspect(file, declaredMime, expectedChecksum, null);
    }

    // Only trusted staging code may supply the hash computed while writing its private file.
    Inspection inspectStaged(Path file, String declaredMime, String checksum) throws IOException {
        return inspect(file, declaredMime, null, checksum);
    }

    private Inspection inspect(Path file, String declaredMime, String expectedChecksum, String stagedChecksum) throws IOException {
        ImagePathPolicy.verifyEntry(file);
        if (!Files.isRegularFile(file) || Files.size(file) > maxBytes) throw new IOException("File exceeds inspection limit or is not regular");
        byte[] bytes;
        try (var in = Files.newInputStream(file)) { bytes = in.readNBytes((int) maxBytes + 1); }
        if (bytes.length > maxBytes) throw new IOException("File exceeds inspection limit");
        String checksum = stagedChecksum == null ? sha256(bytes) : stagedChecksum;
        if (expectedChecksum != null && (!expectedChecksum.matches("[0-9a-fA-F]{64}")
                || !expectedChecksum.equalsIgnoreCase(checksum))) throw new IOException("SHA-256 mismatch");
        String declared = declaredMime == null ? "application/octet-stream" : declaredMime.toLowerCase(Locale.ROOT);
        if (!declared.equals("application/octet-stream") && !TYPES.contains(declared)) throw new IOException("Unsupported declared MIME type");
        String detected = signature(bytes);
        if (detected == null) {
            if (TYPES.contains(declared)) throw new IOException("Declared image does not contain supported image bytes");
            return new Inspection(bytes.length, checksum, Optional.empty());
        }
        if (TYPES.contains(declared) && !declared.equals(detected)) throw new IOException("Declared MIME type differs from image bytes");
        validateContainer(bytes, detected);
        try (var stream = new MemoryCacheImageInputStream(new ByteArrayInputStream(bytes))) {
            var readers = ImageIO.getImageReaders(stream);
            if (!readers.hasNext()) throw new IOException("Supported image decoder unavailable or image is corrupt");
            ImageReader reader = readers.next();
            try {
                reader.setInput(stream, false, false);
                boolean[] warned = { false };
                reader.addIIOReadWarningListener((source, warning) -> warned[0] = true);
                int width = reader.getWidth(0), height = reader.getHeight(0);
                if (detected.equals("image/gif")) {
                    // GIF frame rectangles can be smaller than the logical image canvas.
                    width = Short.toUnsignedInt(ByteBuffer.wrap(bytes, 6, 2).order(ByteOrder.LITTLE_ENDIAN).getShort());
                    height = Short.toUnsignedInt(ByteBuffer.wrap(bytes, 8, 2).order(ByteOrder.LITTLE_ENDIAN).getShort());
                }
                int frames = reader.getNumImages(true);
                if (frames < 1 || frames > 256 || width <= 0 || height <= 0 || (long)width * height > maxPixels)
                    throw new IOException("Invalid image dimensions or frame count");
                long pixels = 0;
                for (int index = 0; index < frames; index++) {
                    int w = reader.getWidth(index), h = reader.getHeight(index);
                    pixels += (long) w * h;
                    if (w <= 0 || h <= 0 || pixels > maxPixels) throw new IOException("Decoded image exceeds pixel budget");
                    var decoded = reader.read(index);
                    if (decoded == null || warned[0]) throw new IOException("Image decoding reported corrupt content");
                    decoded.flush();
                }
                return new Inspection(bytes.length, checksum, Optional.of(new InspectedImage(detected, width, height, bytes.length, checksum)));
            } finally { reader.dispose(); }
        } catch (RuntimeException corrupt) { throw new IOException("Image content cannot be decoded", corrupt); }
    }

    private static String signature(byte[] bytes) {
        if (bytes.length >= 2 && (bytes[0] & 255) == 255 && (bytes[1] & 255) == 216) return "image/jpeg";
        if (bytes.length >= 4 && bytes[0] == (byte)137 && bytes[1] == 80 && bytes[2] == 78 && bytes[3] == 71) return "image/png";
        if (bytes.length >= 3 && bytes[0] == 71 && bytes[1] == 73 && bytes[2] == 70) return "image/gif";
        if (bytes.length >= 12 && ascii(bytes, 0, 4).equals("RIFF") && ascii(bytes, 8, 4).equals("WEBP")) return "image/webp";
        return null;
    }

    private static String ascii(byte[] bytes, int offset, int count) {
        return new String(bytes, offset, count, java.nio.charset.StandardCharsets.US_ASCII);
    }

    private static void validateContainer(byte[] bytes, String mime) throws IOException {
        int n = bytes.length;
        if (mime.equals("image/jpeg") && (n < 4 || bytes[n-2] != (byte)255 || bytes[n-1] != (byte)217))
            throw new IOException("JPEG end marker missing");
        if (mime.equals("image/gif") && (n < 14 || bytes[n-1] != 59)) throw new IOException("GIF trailer missing");
        if (mime.equals("image/webp")) {
            long length = Integer.toUnsignedLong(ByteBuffer.wrap(bytes, 4, 4).order(ByteOrder.LITTLE_ENDIAN).getInt()) + 8;
            if (length != n) throw new IOException("Truncated or inconsistent WebP container");
        }
        if (mime.equals("image/png")) {
            if (n < 20 || !Arrays.equals(Arrays.copyOf(bytes, 8), new byte[]{(byte)137,80,78,71,13,10,26,10}))
                throw new IOException("Invalid PNG signature");
            int offset = 8;
            while (offset + 12 <= n) {
                int length = ByteBuffer.wrap(bytes, offset, 4).getInt();
                if (length < 0 || (long)offset + length + 12 > n) throw new IOException("Truncated PNG chunk");
                CRC32 crc = new CRC32();
                crc.update(bytes, offset + 4, length + 4);
                long expected = Integer.toUnsignedLong(ByteBuffer.wrap(bytes, offset + length + 8, 4).getInt());
                if (crc.getValue() != expected) throw new IOException("PNG chunk checksum mismatch");
                String type = ascii(bytes, offset + 4, 4);
                offset += length + 12;
                if (type.equals("IEND")) {
                    if (length != 0 || offset != n) throw new IOException("Invalid PNG end chunk");
                    return;
                }
            }
            throw new IOException("PNG end chunk missing");
        }
    }

    static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
